# 👶 Baby Monitor 🎥

I like the idea of having a baby monitor, but I don't like the idea of using any old
off-the-shelf baby monitor/surveillance camera connected to the internet. There is a
history of these devices logging your data (pictures of my baby!) and insecure network
settings.

This project is an attempt to build my own, secure, private, online baby monitor.

## Server Setup

TBD

## Raspberry Pi Setup

TBD

### Running the streaming client on the Raspberry Pi

Copy `pi/stream.py` onto the Raspberry Pi. I'm using [Supervisor](http://supervisord.org/)
as the process manager, so the stream client runs automatically, even when the device
reboots.

The setup process looks like this:

```bash
# Install supervisor
sudo apt-get update
sudo apt-get -y install supervisor

HOSTNAME=<hostname> # enter your server's hostname here
ACCESS_TOKEN=<access_token> # enter your server's access token

# Add the configuration to run the stream demo
echo "\
[program:stream]
command=python3 stream.py --host ${HOSTNAME} --token ${ACCESS_TOKEN}
directory=/home/pi/
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true" >> stream.conf

sudo mv stream.conf /etc/supervisor/conf.d/

# Tell supervisor to load in new configurations and start your service
sudo supervisorctl update
```

### Creating a self-signed certificate for debugging

If you want to experiment running the server and your Raspberry Pi on your local network,
you will need to make sure a proper certificate is set up to allow for the TLS secure
socket to function properly.

Create a self-signed certificate for debugging (check out this
[tutorial](https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-apache-on-centos-8)
for more details):

```bash
sudo openssl req \
    -x509 \
    -nodes \
    -days 365 \
    -newkey rsa:2048 \
    -keyout certs/selfsigned.key \
    -out certs/selfsigned.crt
```

- When answering the questions, be sure to remember to use the right host name as the FQDN.
- You may need to enable read permissions. You can use `sudo chmod a+r certs/selfsigned.*`.

Now you want to add this cert to the Raspberry Pi's `ca-certificates` list (more details
[here](https://raspberrypi.stackexchange.com/questions/76419/entrusted-certificates-installation)).

Create a local cert directory:

```bash
mkdir /usr/share/ca-certificates/local
```

Copy `selfsigned.crt` to this directory on your Raspberry Pi, then reconfigure the
`ca-certificates` package:

```bash
dpkg-reconfigure ca-certificates
```

When prompted, choose the `ask` option, then select your new certificate by pressing the
`space` key.

Test that it works and then you're ready for local network debugging!

## Resources

- https://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
- https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/
- https://linuxize.com/post/how-to-install-raspbian-on-raspberry-pi/
- https://www.raspberrypi.org/documentation/usage/camera/raspicam/
- https://raspberrypi.stackexchange.com/questions/31705/capturing-video-in-low-light
- https://pimylifeup.com/raspberry-pi-light-sensor/
