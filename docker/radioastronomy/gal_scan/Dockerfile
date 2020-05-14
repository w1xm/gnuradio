FROM w1xm/base:python2
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

ARG makewidth=2

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-matplotlib
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-astropy
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-astroplan

COPY flowgraph.grc /src/
WORKDIR /flowgraph/
RUN . /pybombs/setup_env.sh && grcc -o /flowgraph /src/flowgraph.grc
COPY *.py /flowgraph/

CMD /flowgraph/run.py
