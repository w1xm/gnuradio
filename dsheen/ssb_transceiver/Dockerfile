FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

COPY ssb_transceiver.grc /src/
WORKDIR /run
RUN . /pybombs/setup_env.sh && grcc -d /run /src/ssb_transceiver.grc

CMD /run/top_block.py
