#!/usr/bin/python

# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import numpy as np
import argparse
import os
import time
from enum import Enum
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

from flowgraph import flowgraph

class radiotelescope(flowgraph):
    def __init__(self, client, **kwargs):
        super(radiotelescope, self).__init__(**kwargs)
        self.client = client
        self.darksky = None

    def snapshot(self, int_time): #straight snapshot over a certain integration time.
        print('Snapshot %d sec' % (int_time,))
        self.integration_block.integrate(int_time)
        vec = None
        while vec is None:
            time.sleep(1)
            vec = self.integration_block.integrate_results()
        return np.array(vec)

    observe = snapshot

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
            elif not status.get("Moving"):
                return
            print('Still moving, current position (%g, %g).' % (self.client.azimuth_position, self.client.elevation_position))

    def park(self):
        print("Parking")
        self.point(250,50)


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
    parser.add_argument('--sdr-frequency', type=float,
                        help='change SDR frequency')
    parser.add_argument('--bandwidth', metavar='HZ', type=float,
                        help='change filter bandwidth')
    parser.add_argument('--int-time', type=int, default=30,
                        help='integration time')
    parser.add_argument('--gain', type=int, default=45,
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
    parser.add_argument('--darksky-offset', type=float, default=0,
                        help='degree offset in azimuth to take darksky calibration at')
    parser.add_argument('--ref', default=False, action='store_true',
                        help='measure reference level instead')
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

    tbkwargs = {}
    if args.sdr_frequency:
        tbkwargs['sdr_frequency'] = args.sdr_frequency
    if args.bandwidth:
        if args.bandwidth > 5e6:
            raise ValueError("bandwidth must be <5e6")
        tbkwargs['if_bandwidth_1'] = args.bandwidth

    tb = top_block_cls(
        client=client,
        sdr_gain=args.gain,
        file_sink_path=os.path.join(args.output_dir, 'receive_block_sink'),
        **tbkwargs
    )
    tb.start()
    print('Receiving ...')

    try:
        band=0
        client.set_band_rx(band, not args.ref)
        survey_autoranging.run_survey(tb, savefolder=args.output_dir, int_time=args.int_time, darksky_offset=args.darksky_offset, iterator=iterator, args=args)
        client.set_band_rx(band, False)
        tb.park()
    finally:
        tb.stop()
        tb.wait()

if __name__ == '__main__':
    main()
