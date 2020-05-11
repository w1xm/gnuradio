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
from enum import Enum
import survey_autoranging

VELOCITY_QUIESCENT = 0.2 # degrees/second

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

from flowgraph import flowgraph

class radiotelescope(flowgraph):
    def __init__(self, client, **kwargs):
        super(radiotelescope, self).__init__(**kwargs)
        self.client = client
        self.darksky = None

    def set_recording_enabled(self, enabled):
        # TODO: Rename block to something more meaningful.
        self.blocks_copy_0.set_enabled(enabled)

    def snapshot(self, int_time): #straight snapshot over a certain integration time.
        print('Snapshot %d sec' % (int_time,))
        self.integration_block.integrate(int_time)
        self.set_recording_enabled(True) #start copying
        vec = None
        while vec is None:
            time.sleep(1)
            vec = self.integration_block.integrate_results()
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

    def point(self, az,el):
        """Point the dish at a particular azimuth and elevation.

        Blocks until the dish has stopped moving.
        """

        print('Moving to position ' + str(az)+' , '+str(el)+'.')
        while True:
            self.client.set_azimuth_position(az)
            self.client.set_elevation_position(el)
            time.sleep(1)
            status = self.client.status
            if status.get("ShutdownError") == 11:
                # Ignore elevation overvelocity
                print('Elevation overvelocity shutdown. Resetting.')
                self.client.i_know_what_i_am_doing_unsafe_exit_shutdown()
            elif status.get("CommandAzFlags") == 'POSITION' and status.get("CommandElFlags") == 'POSITION' and abs(self.client.azimuth_velocity) < VELOCITY_QUIESCENT and abs(self.client.elevation_velocity) < VELOCITY_QUIESCENT:
                return
            print('Still moving, current position (%g, %g).' % (self.client.azimuth_position, self.client.elevation_position))

    def park(self):
        print("Parking")
        self.point(250,50)


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

class Mode(Enum):
    gal = 'gal'
    az = 'az'
    grid = 'grid'

    def __str__(self):
        return self.value

def main(top_block_cls=radiotelescope, options=None):
    parser = argparse.ArgumentParser(description='Galactic sky scan')
    parser.add_argument('output_dir', metavar='DIRECTORY',
                        help='output directory to write scan results')
    parser.add_argument('--int-time', type=int, default=30,
                        help='integration time')
    parser.add_argument('--gain', type=int, default=60,
                        help='SDR gain')
    parser.add_argument('--mode', type=Mode, choices=list(Mode), default=Mode.gal)
    parser.add_argument('--step', type=float, default=2.5,
                        help='position step size')
    parser.add_argument('--start', type=float, default=0,
                        help='starting position')
    parser.add_argument('--stop', type=float, default=360,
                        help='ending position')
    parser.add_argument('--rotation', type=float,
                        help='degrees to rotate grid off-axis')
    parser.add_argument('--rotation-frame', default='icrs',
                        help='frame to rotate grid in')
    parser.add_argument('--lat', type=float,
                        help='galactic latitude to scan (for grid mode)')
    parser.add_argument('--lon', type=float,
                        help='galactic longitude to scan (for grid mode)')
    parser.add_argument('--obj-name',
                        help='named object to scan')
    parser.add_argument('--repeat', type=int, default=1,
                        help='number of times to repeat scan')
    args = parser.parse_args()

    iterator_cls = {
        Mode.gal: survey_autoranging.longitude_iterator,
        Mode.az: survey_autoranging.azimuth_iterator,
        Mode.grid: survey_autoranging.grid_iterator,
        }[args.mode]

    iterator = iterator_cls(**vars(args))

    if args.repeat:
        iterator = survey_autoranging.repeat(iterator, args.repeat)

    try:
        os.mkdir(args.output_dir)
    except OSError:
        pass

    client = rci.client.Client(client_name='gal_scan')
    client.set_offsets(az_offset, el_offset)

    tb = top_block_cls(
        client=client,
        file_sink_path=os.path.join(args.output_dir, 'receive_block_sink'),
    )
    tb.start()
    print('Receiving ...')

    band=0
    client.set_band_rx(band, True)
    survey_autoranging.run_survey(tb, savefolder=args.output_dir, gain=args.gain, int_time=args.int_time, iterator=iterator)
    client.set_band_rx(band, False)
    tb.park()

    tb.stop()
    tb.wait()

if __name__ == '__main__':
    main()
