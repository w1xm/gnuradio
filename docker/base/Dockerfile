FROM w1xm/pybombs/pybombs-commondeps AS base
MAINTAINER w1xm-officers@mit.edu

# Install pybombs-related stuff
ARG makewidth=2

RUN pybombs config makewidth $makewidth

RUN pybombs recipes update

# Needed by uhd
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-mako python3-requests python3-numpy python3-setuptools
RUN pybombs -v install --print-tree uhd && rm -rf /pybombs/src/
# tzdata requires configuration
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

# Install dependencies of gnuradio

# 20.04 doesn't have pygtk
RUN sed -Ei '/pygtk/d' ~/.pybombs/recipes/gr-recipes/gnuradio.lwr && \
    pybombs -v install --print-tree gnuradio && rm -rf /pybombs/src/

RUN pybombs -v install --print-tree limesuite && rm -rf /pybombs/src/

RUN pybombs -v install --print-tree gr-limesdr && rm -rf /pybombs/src/

RUN pybombs -v install --print-tree gr-osmosdr && rm -rf /pybombs/src/

COPY recipes/ /pybombs/.pybombs/recipes/

# Use GR 3.8 gr-bokehgui
RUN pybombs config -P gr-bokehgui source git+https://github.com/w1xm/gr-bokehgui && pybombs config -P gr-bokehgui gitbranch range_slider
RUN sed -i 's/pip: dateutil/deb: python3-dateutil/' ~/.pybombs/recipes/gr-recipes/dateutil.lwr && sed -i 's/pip: tornado/deb: python3-tornado/' ~/.pybombs/recipes/gr-recipes/tornado.lwr
RUN pip3 install bokeh

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-dateutil python3-dateutil net-tools nodejs
RUN pybombs -v install --print-tree gr-bokehgui && rm -rf /pybombs/src/

# TODO: Uncomment when gr-linrad supports 3.8
#RUN pybombs -r /recipes/ install gr-linrad && rm -rf /pybombs/src/

RUN pybombs config makewidth 2

# Install RCI client.
ARG rci_rev=master
RUN pip install 'git+https://github.com/w1xm/rci_interface.git@'$rci_rev'#egg=rci&subdirectory=client'

# Install xterm and configure grc to use it.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y xterm
RUN sed -Ei '/^xterm_executable\s*=/c xterm_executable = /usr/bin/xterm' /pybombs/etc/gnuradio/conf.d/grc.conf

# Install sound packages for aplay and friends.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y alsa-utils pulseaudio-utils libasound2-plugins
RUN sed -Ei '/enable-shm/c enable-shm = no' /etc/pulse/client.conf

# Fix setup_env.sh to refer to Python 3
RUN sed -Ei 's/python2\.6/python3/g; s/python2\.7/python3\.8/g' /pybombs/setup_env.sh

RUN echo 'source /pybombs/setup_env.sh && "$@"' > /run.sh
ENTRYPOINT ["/bin/bash", "/run.sh"]

FROM base AS gui

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget

# Install sublime text
RUN wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | apt-key add -
RUN echo "deb https://download.sublimetext.com/ apt/stable/" > /etc/apt/sources.list.d/sublime-text.list
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sublime-text

# Install and configure gqrx
RUN sed -Ei '/qt4/d' ~/.pybombs/recipes/gr-recipes/gqrx.lwr && \
    pybombs -v install --print-tree gqrx && rm -rf /pybombs/src/
COPY gqrx.conf /root/.config/gqrx/default.conf
