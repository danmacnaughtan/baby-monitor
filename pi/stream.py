#!/usr/bin/env python3

import argparse
import io
import logging
import socket
import ssl
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


def stream(*, feed, camera, host, access_token, port=DEFAULT_PORT):
    """
    Connects to the stream server and stream the video feed to it.

    Tries to reconnect indefinitely if the connection is broken.
    """
    while True:
        try:
            context = ssl.create_default_context()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:

                    ssock.connect((host, port))

                    conn = ssock.makefile("wb")

                    logger.info(f"Connected to host ({host}:{port})")

                    stream_feed(conn, feed, camera, access_token)

        except (ConnectionRefusedError, OSError):
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


def stream_feed(conn, feed, camera, access_token):
    """
    Streams the feed of image frames to the server connection.
    """

    # Sending the access token first. It will always be 41 bytes.
    conn.write(access_token.encode())
    conn.flush()

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


def main(*, host, access_token, port=None):
    if port is None:
        port = DEFAULT_PORT

    with picamera.PiCamera(resolution="640x480", framerate=24) as camera:

        output = StreamingOutput()

        camera.vflip = True
        camera.hflip = True

        camera.start_recording(output, format="mjpeg")

        try:
            stream(
                feed=output,
                camera=camera,
                host=host,
                port=port,
                access_token=access_token,
            )
        finally:
            camera.stop_recording()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--host", required=True)
    parser.add_argument("--port")
    parser.add_argument("--token", dest="access_token", required=True)

    kwargs = dict(parser.parse_args()._get_kwargs())

    logger.info("-- REBOOT --")

    try:
        main(**kwargs)
    except Exception:
        logger.exception("Non recoverable error occurred.")
