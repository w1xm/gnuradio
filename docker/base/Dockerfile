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

RUN pip install 'git+https://github.com/w1xm/rci_interface.git#egg=rci&subdirectory=client'

# Install xterm and configure grc to use it.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y xterm
RUN sed -Ei '/^xterm_executable\s*=/c xterm_executable = /usr/bin/xterm' /pybombs/etc/gnuradio/conf.d/grc.conf

# Install sound packages for aplay and friends.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y alsa-utils pulseaudio-utils

RUN echo 'source /pybombs/setup_env.sh && "$@"' > /run.sh
ENTRYPOINT ["/bin/bash", "/run.sh"]
