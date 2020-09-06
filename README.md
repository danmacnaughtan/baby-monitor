# 🦉 Baby Monitor

I'm having a baby, so I built a video baby monitor. It's a Raspberry Pi streaming video to
a hosted web application, so I can conveniently access it from anywhere.

<p align="center">
    <img src="https://user-images.githubusercontent.com/6351865/91840558-df6f2a80-ec1e-11ea-990a-200597e8506a.png" alt="Login screenshot" width="200">
    <img src="https://user-images.githubusercontent.com/6351865/91843702-2e6b8e80-ec24-11ea-8373-fc2d7cb43a1a.png" alt="Day screenshot" width="200">
    <img src="https://user-images.githubusercontent.com/6351865/91840637-03cb0700-ec1f-11ea-9ad6-9acff5ff8e0b.png" alt="Night screenshot" width="200">
</p>

I didn't like the idea of using any off-the-shelf baby monitor/surveillance camera
connected to the internet. Closed circuit cameras don't offer the same convenience, and
there is still the risk of some form of logging and/or telemetry if the camera needs to be on
WiFi.

I put some effort into making my baby monitor private and secure. The video feed uses TLS,
and any data being sent to the hosted web application requires an access token. Accessing
the frontend of the application requires a simple username and password.

## Hardware

* Raspberry Pi 3+
* Raspberry Pi Camera NoIR
* IR Illuminator light

## Server Setup

Copy over the `server/` directory to your choice of hosting service (or home server). Make
sure Python 3 and Pipenv are installed. Run `pipenv sync` to make sure all dependencies
are installed. Run `pipenv run uvicorn main:app` to change the server.

I recommend using something like [Supervisor](http://supervisord.org/) to manage the
server process. See [this section](running-the-streaming-client-on-the-raspberry-pi) for
an example.

### Create credentials

Run the following command and follow the prompts to create a new username and password
that you will use to login:

```bash
python cli.py create_user
```

Next you will need to create an access token for the Raspberry Pi to connect to the server
(using an auth token here protects us from letting anything that knows about our server
from connecting and sending unwanted data):

```bash
python cli.py create_access_token
```

Copy the access token and save it in a safe place. This is the only time it is shown to
you, and it is never stored in plain text in the server data files.

## Raspberry Pi Setup

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

- https://picamera.readthedocs.io/en/latest/recipes1.html#capturing-to-a-network-stream
- https://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
