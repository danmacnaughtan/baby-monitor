#!/usr/bin/env python3

import io
import logging
import socket
import struct
import sys
import time
from threading import Condition

import picamera


logging.basicConfig(
    filename="stream.log",
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

DEFAULT_PORT = 25000


class StreamingOutput:
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        # New frame, copy the existing buffer's content and notify all clients it's
        # available
        if buf.startswith(b"\xff\xd8"):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


def stream(*, feed, camera, host, port=DEFAULT_PORT):
    """
    Connects to the stream server and stream the video feed to it.

    Tries to reconnect indefinitely if the connection is broken.
    """
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            conn = sock.makefile("wb")

            logger.info(f"Connected to host ({host}:{port})")

            stream_feed(conn, feed, camera)

        except ConnectionRefusedError:
            time.sleep(5)

        except BrokenPipeError:
            logger.warning("Connection lost. Attempting to reconnect...")
            time.sleep(5)

        except Exception:
            logger.exception("Something went wrong. Attempting to reconnect...")
            time.sleep(5)

        finally:
            if camera.closed:
                break


def stream_feed(conn, feed, camera):
    """
    Streams the feed of image frames to the server connection.

    The protocol being used is based on:
    https://picamera.readthedocs.io/en/release-1.13/recipes1.html#capturing-to-a-network-stream

    || <image-len> | <image-data> | <image-len> | <image-data> | ... | <image-len> ||
    || (68702)     |              | (87532)     |              | ... | (0)         ||
    || 4 bytes     | 68702 bytes  | 4 bytes     | 87532 bytes  | ... | 4 bytes     ||
    """
    while True:
        if camera.closed:
            # Signal that the stream is done
            conn.write(struct.pack("<L", 0))
            conn.flush()
            break

        with feed.condition:
            feed.condition.wait()
            frame = feed.frame

        if not len(frame):
            continue

        conn.write(struct.pack("<L", len(frame)))
        conn.flush()

        conn.write(frame)


def main(host, port=DEFAULT_PORT):
    with picamera.PiCamera(resolution="640x480", framerate=24) as camera:

        output = StreamingOutput()

        camera.vflip = True
        camera.hflip = True

        camera.start_recording(output, format="mjpeg")

        try:
            stream(feed=output, camera=camera, host=host, port=port)
        finally:
            camera.stop_recording()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: stream.py HOST [PORT]")
        sys.exit(0)

    logger.info("-- REBOOT --")

    try:
        main(*sys.argv[1:])
    except Exception:
        logger.exception("Non recoverable error occurred.")
