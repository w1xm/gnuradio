FROM ubuntu:18.04
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget

WORKDIR /work
RUN wget http://physics.princeton.edu/pulsar/K1JT/wsjtx-2.1.0.tgz
RUN tar -xf wsjtx-2.1.0.tgz

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y cmake gfortran
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y qtmultimedia5-dev libqt5serialport5-dev qttools5-dev qttools5-dev-tools libusb-1.0.0-dev libfftw3-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y git
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libtool automake
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y texinfo
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libudev-dev

WORKDIR /work/build
RUN cmake -DWSJT_SKIP_MANPAGES=ON -DWSJT_GENERATE_DOCS=OFF ../wsjtx-2.1.0
RUN cmake --build .
RUN cmake --build . --target install

# Install sound packages for aplay and friends.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y alsa-utils pulseaudio-utils apulse libasound2-plugins libqt5multimedia5-plugins
RUN sed -Ei '/enable-shm/c enable-shm = no' /etc/pulse/client.conf

COPY WSJT-X.ini /root/.config/

CMD /usr/local/bin/wsjtx
