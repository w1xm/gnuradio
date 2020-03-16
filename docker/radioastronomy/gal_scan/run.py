#!/usr/bin/python

# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import argparse
import os
import time
import survey_autoranging

##################################################
##################################################
##################################################
            # RCI STUFF #
##################################################
##################################################
##################################################
az_offset=5.5
el_offset=-5.5
import rci.client
client = rci.client.Client()
client.set_offsets(az_offset, el_offset)

def point(az,el): #point the dish
    client.set_azimuth_position(az)
    client.set_elevation_position(el)
    print('Moving to position ' + str(az)+' , '+str(el)+'.')
    return

def park():
    point(250,50)
    print("Parking")
    return

from flowgraph import flowgraph

class top_block(flowgraph):
    def __init__(self, **kwargs):
        super(top_block, self).__init__(**kwargs)
        self.darksky = None

    def set_recording_enabled(self, enabled):
        # TODO: Rename block to something more meaningful.
        self.blocks_copy_0.set_enabled(enabled)

    def snapshot(self, int_time): #straight snapshot over a certain integration time.
        self.set_integration_time(int_time)
        print('Snapshot %d sec' % (int_time,))
        vec=self.get_variable_function_probe() #old vector
        pointa=vec[0]
        pointb=vec[-1]
        self.set_recording_enabled(True) #start copying
        while vec[0]==pointa and vec[-1]==pointb:
            time.sleep(1)
            vec=self.get_variable_function_probe()
        self.set_recording_enabled(False) #stop copying
        return np.array(vec)

    def dark_sky_calib(self, int_time): #for use when pointing at the dark sky
        self.darksky = self.snapshot(int_time)

    def observe(self, int_time): #dark sky calbrated snapshot
        vec=self.snapshot(int_time)
        # TODO: Why did the original code wait for int_time here?
        if self.darksky:
            return vec-self.darksky
        else:
            print('Warning: No dark sky calibration has been performed.')
            return vec
        

#axis extremes
flo=1420.4-0.75
fhi=1420.4+0.75
def graphing(tb, int_time, iter=float('inf')):
    plt.ion()
    plt.figure()
    vec=tb.get_variable_function_probe() #vector
    n=len(vec)
    x=np.linspace(flo, fhi, n)
    i=0
    while(i<iter):
        plt.pause(int_time)
        y=tb.observe(int_time)
        plt.clf()
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Scaled power')
        plt.axvline(x=1420.406, color='black', ls='--')
        plt.ticklabel_format(useOffset=False)
        plt.plot(x,y)
        plt.draw()
        i+=1


def main(top_block_cls=top_block, options=None):
    parser = argparse.ArgumentParser(description='Galactic sky scan')
    parser.add_argument('output_dir', metavar='DIRECTORY',
                        help='output directory to write scan results')
    parser.add_argument('--int-time', type=int, default=30,
                        help='integration time')
    args = parser.parse_args()

    try:
        os.mkdir(args.output_dir)
    except OSError:
        pass

    tb = top_block_cls(file_sink_path=os.path.join(args.output_dir, 'receive_block_sink'))
    tb.start()
    print('Receiving ...')

    band=0
    client.set_band_rx(band, True)
    survey_autoranging.run_survey(tb, point, savefolder=args.output_dir, int_time=args.int_time)
    client.set_band_rx(band, False)

    tb.stop()
    tb.wait()

if __name__ == '__main__':
    main()
