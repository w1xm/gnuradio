FROM w1xm/base
MAINTAINER w1xm-officers@mit.edu

RUN DEBIAN_FRONTEND=noninteractive apt-get update -q

ARG makewidth=2

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-matplotlib
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-astropy
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-astroplan
