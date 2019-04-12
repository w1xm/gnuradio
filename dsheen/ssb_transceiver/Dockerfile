FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

ARG flowgraph=ssb_transceiver.grc

COPY ${flowgraph} /src/
WORKDIR /run/
COPY *.py /run/
RUN . /pybombs/setup_env.sh && grcc -d /run /src/${flowgraph}

CMD /run/run.py
