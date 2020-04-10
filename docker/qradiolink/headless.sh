#!/bin/bash

/usr/bin/grumble --datadir /data --log /data/grumble.log &
export STARTUP="/headless-startup.sh"
exec vncserver -SecurityTypes None -localhost yes -geometry 1280x768 -fg
