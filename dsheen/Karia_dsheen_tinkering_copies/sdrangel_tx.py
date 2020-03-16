#!/usr/bin/python
import requests
import sys
import pprint
from rci import client

if len(sys.argv) < 2:
    raise ValueError('missing command')
command = sys.argv[1]

tx = (command == 'tx')

base_uri = 'http://localhost:8091/sdrangel'
rxdev = 0
txdev = 1

def get_settings(dev, channel=None):
    url = '%s/deviceset/%d/device/settings' % (base_uri, dev)
    if channel is not None:
        url = '%s/deviceset/%d/channel/%d/settings' % (base_uri, dev, channel)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()
def patch_settings(dev, settings, channel=None):
    url = '%s/deviceset/%d/device/settings' % (base_uri, dev)
    if channel is not None:
        url = '%s/deviceset/%d/channel/%d/settings' % (base_uri, dev, channel)    
    requests.patch(url, json=settings).raise_for_status()

rci = client.Client('ws://localhost:8502/api/ws')
if tx:
    # Copy frequency to TX
    settings = get_settings(txdev)
    rxsettings = get_settings(rxdev)
    freq = rxsettings['limeSdrInputSettings']['centerFrequency']
    rxchannelsettings = get_settings(rxdev, 0)
    for v in rxchannelsettings.itervalues():
        if isinstance(v, dict) and 'inputFrequencyOffset' in v:
            freq += v['inputFrequencyOffset']
    settings['hackRFOutputSettings']['centerFrequency'] = freq
    patch_settings(txdev, settings)
    # Set input gain to 0
    settings = get_settings(rxdev)
    settings['limeSdrInputSettings']['gain'] = 0
    patch_settings(rxdev, settings)
    # Focus TX tab
    requests.patch('%s/deviceset/%d/focus' % (base_uri, txdev)).raise_for_status()
    # Set sequencer to transmit and wait for key
    rci.set_band_tx(0, True, wait=False)
    # Start "acquisition" on output device
    requests.post('%s/deviceset/%d/device/run' % (base_uri, txdev)).raise_for_status()
    # Start audio on modulator
    txchannelsettings = get_settings(txdev, 0)
    txchannelsettings['SSBModSettings']['audioMute'] = 0
    patch_settings(txdev, txchannelsettings, 0)
else:
    ## Stop "acquisition" on output device
    #requests.delete('%s/deviceset/%d/device/run' % (base_uri, txdev)).raise_for_status()
    # Stop audio on modulator
    txchannelsettings = get_settings(txdev, 0)
    txchannelsettings['SSBModSettings']['audioMute'] = 1
    patch_settings(txdev, txchannelsettings, 0)
    # Set sequencer to receive
    rci.set_band_rx(0, True)
    # Focus RX tab
    requests.patch('%s/deviceset/%d/focus' % (base_uri, rxdev)).raise_for_status()
    # Set input gain to 60
    settings = get_settings(rxdev)
    settings['limeSdrInputSettings']['gain'] = 60
    patch_settings(rxdev, settings)
