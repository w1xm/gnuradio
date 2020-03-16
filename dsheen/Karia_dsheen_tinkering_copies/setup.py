#!/usr/bin/env python

from setuptools import setup

setup(name='rci',
      version='1.0',
      description='RCI Control Interface',
      author='Quentin Smith',
      author_email='quentin@mit.edu',
      packages=['rci'],
      install_requires=["websocket-client"],
     )
