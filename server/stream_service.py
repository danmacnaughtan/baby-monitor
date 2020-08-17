import asyncio
import ctypes
import io
import logging
import os
import socket
import struct
import time
from multiprocessing import Array, Condition, Process, Value


logger = logging.getLogger(__name__)


class StreamService:
    """
    Example usage:

        from PIL import Image

        service = StreamService().start()

        while True:
            buf = io.BytesIO()

            lock = service.frame_buffer.get_lock()
            lock.acquire()

            length = service.frame_length.value
            buf.write(bytearray(service.frame_buffer.get_obj())[:length])

            lock.release()

            if buf.tell():
                buf.seek(0)
                image = Image.open(buf)
    """

    def __init__(self):
        self.frame_length = Value("i", 0)
        self.frame_buffer = Array(ctypes.c_ubyte, 128000)
        self.condition = Condition()
        self._proc = None

    def __del__(self):
        self.stop()

    def run(self):
        """
        Starts the streaming service in another process.

        Access the current frame via the `frame_buffer` and `frame_length` shared memory
        objects.
        """
        self._proc = Process(
            target=StreamService.process_stream,
            args=(self.frame_buffer, self.frame_length, self.condition),
        )
        self._proc.start()
        return self

    def stop(self):
        self._proc.terminate()
        return self

    @staticmethod
    def process_stream(frame_buffer, frame_length, condition, port=25000):
        """
        Runs the socket server. Puts the latest frame in the given frame_buffer.
        """
        host = socket.gethostname()

        print(f"Socket server listening at: tcp://{host}:{port}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", port))
        sock.listen(0)

        # If the connection to the pi closes, we want to just wait for it to come up again.
        while True:
            # Accept a single connection and make a file-like object out of it.
            conn = sock.accept()[0].makefile("rb")

            # TODO: Authenticate the connection

            print("Connected...")

            try:
                while True:
                    # Read the length of the image as a 32-bit unsigned int.
                    image_len = struct.unpack("<L", conn.read(struct.calcsize("<L")))[0]

                    # print("Received:", image_len)

                    # If the length is 0, quit the loop.
                    if not image_len:
                        break

                    # Read the bytes of the image into the process-shared frame_buffer
                    with condition:
                        frame_length.value = image_len

                        try:
                            for i, b in enumerate(bytearray(conn.read(image_len))):
                                frame_buffer.get_obj()[i] = b
                        except IndexError:
                            logger.error(
                                f"Error writing frame buffer. (image_len: {image_len})"
                            )

                        condition.notify_all()
            finally:
                print("Connection closed")
                conn.close()

        sock.close()

    async def generate_frames(self):
        h = lambda key, value: f"{key}: {value}\r\n".encode("latin-1", "strict")

        try:
            while True:
                if not self._proc.is_alive():
                    print("Process is dead.")
                    break

                with self.condition:
                    self.condition.wait()

                    yield b"--FRAME\r\n"

                    length = self.frame_length.value

                    yield h("Content-Type", "image/jpeg")
                    yield h("Content-Length", length)
                    yield b"\r\n"

                    buf = io.BytesIO()
                    buf.write(bytearray(self.frame_buffer.get_obj())[:length])
                    yield buf.getvalue()

                    yield b"\r\n"

                await asyncio.sleep(0.001)

        except AssertionError:
            pass

        except Exception:
            logger.exception("Removed streaming client")
