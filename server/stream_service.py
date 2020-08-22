import asyncio
import ctypes
import io
import logging
import os
import socket
import ssl
import struct
from multiprocessing import Array, Condition, Process, Value

import config


logger = logging.getLogger(__name__)


class StreamService:
    """
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
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(config.CERT_PEM_FILE, config.CERT_KEY_FILE)

        host = socket.gethostname()

        logger.info(f"Socket server listening at: tcp://{host}:{port}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", port))
            sock.listen(0)

            while True:
                new_sock, fromaddr = sock.accept()

                with context.wrap_socket(new_sock, server_side=True) as ssock:
                    with ssock.makefile("rb") as conn:

                        if not StreamService.authenticate_connection(conn, fromaddr):
                            continue

                        try:
                            StreamService.recieve_frames(
                                conn, frame_buffer, frame_length, condition
                            )
                        finally:
                            logger.info("Connection closed")

    @staticmethod
    def authenticate_connection(conn, fromaddr) -> bool:
        # TODO: Authenticate the connection
        logger.info(f"Authentication failed ({fromaddr})")
        return False

    @staticmethod
    def recieve_frames(conn, frame_buffer, frame_length, condition):

        logger.info("Monitor is connected.")

        while True:
            # Read the length of the image as a 32-bit unsigned int.
            image_len = struct.unpack("<L", conn.read(struct.calcsize("<L")))[0]

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
                        f"Error writing to frame buffer (image_len: {image_len})"
                    )

                condition.notify_all()

    async def generate_frames(self):
        """
        A continuous async generator of mjpeg frames.
        """

        h = lambda key, value: f"{key}: {value}\r\n".encode("latin-1", "strict")

        try:
            while True:
                if not self._proc.is_alive():
                    break

                with self.condition:
                    self.condition.wait()

                    length = self.frame_length.value

                    buf = io.BytesIO()
                    buf.write(b"--FRAME\r\n")
                    buf.write(h("Content-Type", "image/jpeg"))
                    buf.write(h("Content-Length", length))
                    buf.write(b"\r\n")
                    buf.write(bytes(bytearray(self.frame_buffer.get_obj())[:length]))
                    buf.write(b"\r\n")

                    yield buf.getvalue()

                await asyncio.sleep(0.001)

        except AssertionError:
            pass

        except Exception:
            logger.exception("Removed streaming client")
