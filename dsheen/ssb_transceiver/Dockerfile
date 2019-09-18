FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

ARG flowgraph=ssb_transceiver.grc

COPY ${flowgraph} /src/
WORKDIR /flowgraph/
COPY *.py /flowgraph/
RUN . /pybombs/setup_env.sh && grcc -d /flowgraph /src/${flowgraph}

RUN echo "${flowgraph%.grc}" > client_name.txt

CMD /flowgraph/run.py
