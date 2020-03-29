FROM pybombs/pybombs-commondeps:2.3.3 AS base
MAINTAINER w1xm-officers@mit.edu

# Update package lists
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

# Install pybombs-related stuff
ARG makewidth=2

RUN pybombs config makewidth $makewidth

RUN DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y
RUN pybombs -v install apache-thrift && rm -rf /pybombs/src/
# Needed by uhd
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-mako python3-requests python3-numpy python3-setuptools
RUN pybombs install uhd && rm -rf /pybombs/src/
RUN pybombs -v install gnuradio && rm -rf /pybombs/src/
RUN pybombs install limesuite && rm -rf /pybombs/src/
RUN pybombs install gr-limesdr && rm -rf /pybombs/src/

COPY recipes/ /recipes/
RUN pybombs -r /recipes/ install gr-linrad && rm -rf /pybombs/src/

RUN pybombs config makewidth 2

# Install RCI client.
RUN pip install 'git+https://github.com/w1xm/rci_interface.git#egg=rci&subdirectory=client'

# Install xterm and configure grc to use it.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y xterm
RUN sed -Ei '/^xterm_executable\s*=/c xterm_executable = /usr/bin/xterm' /pybombs/etc/gnuradio/conf.d/grc.conf

# Install sound packages for aplay and friends.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y alsa-utils pulseaudio-utils libasound2-plugins
RUN sed -Ei '/enable-shm/c enable-shm = no' /etc/pulse/client.conf

RUN echo 'source /pybombs/setup_env.sh && "$@"' > /run.sh
ENTRYPOINT ["/bin/bash", "/run.sh"]

FROM base AS gui

# Install sublime text
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget
RUN wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | apt-key add -
RUN echo "deb https://download.sublimetext.com/ apt/stable/" > /etc/apt/sources.list.d/sublime-text.list
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sublime-text

# Install and configure gqrx
RUN pybombs -v install --print-tree gqrx && rm -rf /pybombs/src/
COPY gqrx.conf /root/.config/gqrx/default.conf
