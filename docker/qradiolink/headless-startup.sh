#!/bin/bash

fluxbox &

desktop=${DISPLAY%.0}

/usr/share/novnc/utils/launch.sh --vnc localhost:$(( 5900 + ${desktop#:} )) &

(
    # TODO: Wait for grumble and qradiolink to come up before sending commands
    sleep 10;
    (
	echo -e "connectserver localhost 64738\r"
	sleep 1
	echo -e "setrx 1\r"
	sleep 3
	echo -e "setforwarding 1\r"
	sleep 1
	echo -e "quit\r"
    ) | nc localhost 4939 || echo "Failed to configure qradiolink"
)&

. /pybombs/setup_env.sh && exec /work/qradiolink/build/qradiolink
