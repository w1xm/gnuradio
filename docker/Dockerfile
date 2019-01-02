FROM pybombs/pybombs-commondeps:2.3.3
MAINTAINER w1xm-officers@mit.edu

ARG makewidth=2

RUN pybombs config makewidth $makewidth

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN pybombs install apache-thrift
RUN pybombs install uhd
RUN pybombs -v install gnuradio
RUN pybombs install limesuite
RUN pybombs install gr-limesdr

RUN pybombs config makewidth 2

RUN echo 'source /pybombs/setup_env.sh && "$@"' > /run.sh
ENTRYPOINT ["/bin/bash", "/run.sh"]
