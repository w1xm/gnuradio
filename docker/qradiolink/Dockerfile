FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libconfig++-dev libgsm1-dev libprotobuf-dev libopus-dev libspeexdsp-dev libpulse-dev libasound2-dev libcodec2-dev libsqlite3-dev libjpeg-dev libprotoc-dev protobuf-compiler

WORKDIR /work
RUN git clone -b w1xm https://github.com/w1xm/qradiolink
WORKDIR /work/qradiolink/ext
RUN protoc --cpp_out=. Mumble.proto
RUN protoc --cpp_out=. QRadioLink.proto
WORKDIR /work/qradiolink/build
RUN qmake "INCLUDEPATH+=/pybombs/include" ..
RUN . /pybombs/setup_env.sh && make

COPY ptt .

CMD /work/qradiolink/build/qradiolink
