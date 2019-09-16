FROM ubuntu:18.04
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget

WORKDIR /work
RUN wget http://www.sm5bsz.com/linuxdsp/archive/lir04-14a.tbz
RUN tar -xf lir04-14a.tbz
WORKDIR /work/linrad-04.14a

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nasm
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y pkg-config libtool automake cmake git xxd pandoc libusb-dev libasound-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libx11-dev libusb-dev portaudio19-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libftdi-dev libusb-1.0-0-dev libxext-dev 
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libc6-dev-i386

RUN ./configure --with-help
RUN make xlinrad64
RUN make xlinrad
COPY par_* .
#RUN make sim
