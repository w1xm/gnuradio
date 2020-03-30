FROM pybombs/pybombs-commondeps:2.3.3 AS base
MAINTAINER w1xm-officers@mit.edu

# Update package lists
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

# Update base system
RUN DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y

# Install pybombs-related stuff
ARG makewidth=2

RUN pybombs config makewidth $makewidth

RUN pybombs recipes update

# Temporary patch until the gr-limesdr recipe is updated
RUN sed -i 's/master/gr-3.8/' ~/.pybombs/recipes/gr-recipes/gr-limesdr.lwr

RUN pybombs -v install --print-tree apache-thrift && rm -rf /pybombs/src/
# Needed by uhd
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-mako python3-requests python3-numpy python3-setuptools
RUN pybombs -v install --print-tree uhd && rm -rf /pybombs/src/
# tzdata requires configuration
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

# Install dependencies of gnuradio
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y swig3.0 libqt5opengl5-dev libqt5svg5-dev qt5-default pyqt5-dev pyqt5-dev-tools python-pyqt5 python-click-plugins python-pyqtgraph liborc-0.4-dev libgmp-dev libgmp3-dev python-yaml python-gi-dev python-gi-cairo python-gobject-2-dev gobject-introspection gir1.2-gtk-3.0

# Force the use of Python 2
COPY cmake-defaults.txt /pybombs/.pybombs/cmake-defaults.txt
RUN echo -e '#!/bin/sh\nexec /usr/bin/cmake -C /pybombs/.pybombs/cmake-defaults.txt "$@"' > /pybombs/bin/cmake && chmod +x /pybombs/bin/cmake

RUN pybombs -v install --print-tree gnuradio && rm -rf /pybombs/src/
RUN pybombs -v install --print-tree limesuite && rm -rf /pybombs/src/

# Use patched gr-limesdr for Python 2
RUN pybombs config -P gr-limesdr source git+https://github.com/w1xm/gr-limesdr
RUN pybombs -v install --print-tree gr-limesdr && rm -rf /pybombs/src/

# Some packages such as gr-osmosdr require a newer CMake
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget
RUN wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | apt-key add -
RUN echo "deb https://apt.kitware.com/ubuntu/ bionic main" > /etc/apt/sources.list.d/kitware.list
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y cmake

# Use patched gr-osmosdr for Python 2
RUN pybombs config -P gr-osmosdr source git+https://github.com/w1xm/gr-osmosdr
RUN pybombs -v install --print-tree gr-osmosdr && rm -rf /pybombs/src/

COPY recipes/ /recipes/

# TODO: Uncomment when gr-linrad supports 3.8
#RUN pybombs -r /recipes/ install gr-linrad && rm -rf /pybombs/src/

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
RUN wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | apt-key add -
RUN echo "deb https://download.sublimetext.com/ apt/stable/" > /etc/apt/sources.list.d/sublime-text.list
RUN DEBIAN_FRONTEND=noninteractive apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sublime-text

# Install and configure gqrx
RUN pybombs -v install --print-tree gqrx && rm -rf /pybombs/src/
COPY gqrx.conf /root/.config/gqrx/default.conf
