FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

ARG makewidth=2

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-matplotlib \
    python3-astropy \
    python3-astroplan \
    python-is-python3

COPY flowgraph.grc /src/
WORKDIR /flowgraph/
RUN . /pybombs/setup_env.sh && grcc -o /flowgraph /src/flowgraph.grc
COPY *.py *.ts *.css *.less /flowgraph/

CMD /flowgraph/run.py
