#!/usr/bin/env python3
"""
This is a RasberryPi Camera streaming demo Based on
https://picamera.readthedocs.io/en/latest/recipes2.html#web-streaminga. It was modified to
handle switching between day and low-light camera settings dynamically over the day.
"""

import datetime
import io
import logging
import os
import socket
import socketserver
import time
from fractions import Fraction
from http import server
from threading import Condition, Thread

import picamera


template = """\
<html>
    <head>
        <title>PiCamera MJPEG Streaming Demo</title>
        <style>
        body {
            background: #000000;
        }
        body h1 {
            color: #FFFFFF;
        }
        </style>
    </head>
    <body>
        <h1>PiCamera MJPEG Streaming Demo</h1>
        <br />
        <img src="stream.mjpg" width="640" height "480" />
    </body>
</html>
"""


class StreamingOutput:
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b"\xff\xd8"):
            # New frame, copy the existing buffer's content and notify all clients it's
            # available
            self.buffer.truncate()

            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()

            self.buffer.seek(0)

        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = template.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception as e:
                logging.warning(f"Removed streaming client {self.client_address} {e}")
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def handle_camera(camera, output):
    """
    Operates the camera.

    Adjusts the camera settings based on the time of day. Should be run in a non-main
    thread.

    It is required that the camera passed in was initialized with a 4:3 aspect ratio with
    a framerate of 24, and has the sensor_mode 4 manually set (this is because the
    sensor_mode will be changed while open to handle switching from default to low light
    settings).
    """
    camera.vflip = True
    camera.hflip = True

    handle_camera._state = "day"

    camera.start_recording(output, format="mjpeg")

    time.sleep(10)

    while True:
        if camera.closed:
            break

        camera.stop_recording()

        h = datetime.datetime.now().hour

        # Optimal for summer
        if h >= 21 or h < 5:
            if handle_camera._state == "day":
                # Low-light settings after 7pm
                camera.framerate = Fraction(1, 6)
                camera.sensor_mode = 3
                camera.sensor_mode = 3  # call twice to handle firmware bug
                camera.shutter_speed = 6000000
                camera.iso = 800
                time.sleep(30)
                camera.exposure_mode = "off"
                handle_camera._state = "night"
        else:
            if handle_camera._state == "night":
                # Default settings
                camera.framerate = 24
                camera.sensor_mode = 4
                camera.sensor_mode = 4  # call twice to handle firmware bug
                camera.shutter_speed = 0
                camera.iso = 0
                time.sleep(1)
                camera.exposure_mode = "auto"
                handle_camera._state = "day"

        camera.start_recording(output, format="mjpeg")

        time.sleep(1800)


if __name__ == "__main__":
    print(f"Streaming at: http://{socket.gethostname()}:8000")

    with picamera.PiCamera(resolution="640x480", framerate=24, sensor_mode=4) as camera:
        output = StreamingOutput()

        Thread(target=handle_camera, args=(camera, output)).start()

        try:
            address = ("", 8000)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()
