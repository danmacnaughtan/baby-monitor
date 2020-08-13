# 👶 Baby Monitor 🎥

I like the idea of having a baby monitor, but I don't like the idea of using any old
off-the-shelf baby monitor/surveillance camera connected to the internet. There is a
history of these devices logging your data (pictures of my baby!) and insecure network
settings.

This project is an attempt to build my own, secure, private, online baby monitor.

First I plan to just get the basic camera stream live on my local network. Next I want to
stream the video to my own digital ocean server, and allow secure authenticated
connections to watch the stream over the internet.

## Pi

TBD

### Running the stream demo

Copy the contents of `pi/` onto the raspberry pi. In order for us to run the service while
not logged in, we can use [Supervisor](http://supervisord.org/). Supervisor manages and
keeps your services running once you log out of your session or reboot the device.

Run the following commands:

```bash
# Install supervisor
sudo apt-get update
sudo apt-get -y install supervisor

# Add the configuration to run the stream demo
sudo echo "\
[program:stream]
command=python3 stream.py
directory=/home/pi/
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true" >> /etc/supervisor/conf.d/stream.conf

# Tell supervisor to load in new configurations and start your service
sudo supervisorctl update
```

## Research

[Tutorial](https://randomnerdtutorials.com/video-streaming-with-raspberry-pi-camera/)

[Web streaming
docs](https://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming)

[Live video streaming over
network](https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/)

### More Resources

- https://linuxize.com/post/how-to-install-raspbian-on-raspberry-pi/
- https://www.raspberrypi.org/documentation/usage/camera/raspicam/
- https://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
- https://github.com/jeffbass/imagezmq
- https://stackoverflow.com/questions/50058811/how-to-access-video-stream-from-an-ip-camera-using-opencv-in-python
- https://raspberrypi.stackexchange.com/questions/31705/capturing-video-in-low-light
- https://pimylifeup.com/raspberry-pi-light-sensor/
