FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

# Install base packages
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev \
    git wget \
    python3-twisted python3-txws python3-ephem python3-serial python3-service-identity \
    libsndfile1-dev libitpp-dev \
    multimon-ng

RUN sed -Ei '/qt4/d' ~/.pybombs/recipes/gr-recipes/gr-air-modes.lwr && \
    pybombs -v install --print-tree gr-dsd rtl_433 gr-air-modes && \
    rm -rf /pybombs/src/

# Enabled demodulators:
# DSD
# APRS
# 433
# MODE-S

# TODO:
# PSK31, RTTY (don't support GR 3.8)
# WSPR (needs wsprd)

ARG revision=master

RUN git clone https://github.com/w1xm/shinysdr/ /tmp/shinysdr && \
    cd /tmp/shinysdr && \
    git checkout $revision && \
    . /pybombs/setup_env.sh && \
    python3 setup.py fetch_deps && \
    python3 setup.py build && \
    python3 setup.py install

RUN adduser --system --shell /bin/bash shinysdr

RUN mkdir /config && chown shinysdr /config
COPY config.py /config

EXPOSE 8080 8081

CMD su shinysdr - -c ". /pybombs/setup_env.sh && shinysdr /config"
