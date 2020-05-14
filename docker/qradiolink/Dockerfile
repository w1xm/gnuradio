FROM w1xm/base:python2 AS qradiolink
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y protobuf-compiler libprotobuf-dev libopus0 libopus-dev libspeexdsp1 libspeexdsp-dev libpulse0 libpulse-dev libcodec2-dev libasound2 libasound2-dev libjpeg-turbo8-dev libjpeg-dev libconfig++9v5 libconfig++-dev qt5-qmake qt5-default qtbase5-dev libqt5core5a libqt5gui5 libqt5network5 libqt5sql5 qtmultimedia5-dev libqt5multimediawidgets5 libqt5multimedia5-plugins libqt5multimedia5 libftdi1-dev libftdi1 libsndfile1-dev libsndfile1

WORKDIR /work
RUN git clone -b w1xm https://github.com/w1xm/qradiolink
WORKDIR /work/qradiolink/ext
RUN protoc --cpp_out=. Mumble.proto
RUN protoc --cpp_out=. QRadioLink.proto
WORKDIR /work/qradiolink/build
RUN sed -i 's/-lftdi/-lftdi1/' /work/qradiolink/qradiolink.pro
RUN qmake "INCLUDEPATH+=/pybombs/include" "INCLUDEPATH+=/usr/include/libftdi1" ..
RUN . /pybombs/setup_env.sh && make

COPY ptt /
COPY qradiolink.cfg /root/.config/

CMD /work/qradiolink/build/qradiolink

# Build grumble
FROM golang:1.14 as grumble-builder

RUN mkdir -p /go/src/mumble.info/grumble/
RUN git clone https://github.com/w1xm/grumble /go/src/mumble.info/grumble

RUN go get -v -t mumble.info/grumble/cmd/grumble

FROM qradiolink AS headless

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tigervnc-standalone-server fluxbox netcat novnc

COPY --from=grumble-builder /go/bin/grumble /usr/bin/grumble
COPY headless* /
COPY fluxbox-apps /root/.fluxbox/apps
COPY index.html /usr/share/novnc

ENV DATADIR /data

RUN mkdir /data

WORKDIR /data

CMD /headless.sh
