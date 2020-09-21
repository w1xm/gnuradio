# -*- coding: utf-8 -*-

# This is a ShinySDR configuration file. For more information about what can
# be put here, read the manual section on it, available from the running
# ShinySDR server at: http://localhost:8100/manual/configuration

from os.path import expanduser
import os

from shinysdr.devices import AudioDevice, PositionedDevice
from shinysdr.plugins.osmosdr import OsmoSDRDevice, OsmoSDRProfile
from shinysdr.plugins.limesdr import LimeSDRDevice, LimeSDRUSB, LNAL
from shinysdr.plugins.simulate import SimulatedDevice
import shinysdr.plugins.hamlib

# Set either of these environment variables to the empty string to disable the device.
lime = os.environ.get('LIME', True)
sim = os.environ.get('SIM', True)

# OsmoSDR generic driver; handles USRP, RTL-SDR, FunCube Dongle, HackRF, etc.
# To select a specific device, replace '' with 'rtl=0' etc.
#config.devices.add(u'dish', OsmoSDRDevice('driver=lime,soapy=0', sample_rate=3e6))

if lime:
    sdr = LimeSDRDevice(serial='0009060B00471B22', device_type=LimeSDRUSB, lna_path=LNAL, sample_rate=6e6)

    ## TODO(quentin): Link up with rotator
    #d = shinysdr.plugins.hamlib.connect_to_rotctld(config.reactor, host='w1xm-radar-1.mit.edu', port=4533)
    #d.addCallback(lambda rotator: config.devices.add(u'dish', sdr, PositionedDevice(42.360326, -71.089324), rotator))
    #config.wait_for(d)
    config.devices.add(u'dish', sdr, PositionedDevice(42.360326, -71.089324))
from shinysdr.plugins.flightradar24 import Flightradar24
config.devices.add(u'flightradar24', Flightradar24(config.reactor, bounds=(47,37, -76,-66)))

## For hardware which uses a sound-card as its ADC or appears as an
## audio device.
#config.devices.add(u'audio', AudioDevice(rx_device=''))
#config.set_server_audio_allowed(True, 'pulse_shinyout', 48000)

# Locally generated RF signals for test purposes.
if sim:
    config.devices.add(u'sim', SimulatedDevice())

# Databases
config.databases.add_directory('/config/databases')

from uuid import getnode as get_mac

config.serve_web(
    # These are in Twisted endpoint description syntax:
    # <http://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.html#serverFromString>
    # Note: ws_endpoint must currently be 1 greater than http_endpoint; if one
    # is SSL then both must be. These restrictions will be relaxed later.
    http_endpoint='tcp:8100',
    ws_endpoint='tcp:8101',

    # A secret placed in the URL as simple access control. Does not
    # provide any real security unless using HTTPS. The default value
    # in this file has been automatically generated from 128 random bits.
    # Set to None to not use any secret.
    root_cap="%x" % get_mac(),
    
    # Page title / station name
    title='ShinySDR')
