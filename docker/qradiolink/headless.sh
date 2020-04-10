#!/bin/bash

/usr/bin/grumble --datadir /data --log /data/grumble.log --config WebPort=6443 &
export STARTUP="/headless-startup.sh"
exec vncserver -SecurityTypes None -localhost yes -geometry 1280x768 -fg
