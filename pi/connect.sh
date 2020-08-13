#!/bin/bash
$(nmap -sP 192.168.0.0/24 | awk '/raspberrypi/ {print "ssh pi@"$NF}' | sed 's/[()]//g')
