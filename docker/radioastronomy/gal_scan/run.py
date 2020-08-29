#!/usr/bin/python

# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import numpy as np
import argparse
import os
import sys
import time
from enum import Enum
import survey_autoranging
from survey_autoranging import AZ_OFFSET, EL_OFFSET

##################################################
##################################################
##################################################
            # RCI STUFF #
##################################################
##################################################
##################################################
import rci.client

from flowgraph import flowgraph

class radiotelescope(flowgraph):
    logger = logging.getLogger('radiotelescope')

    def __init__(self, client, **kwargs):
        super(radiotelescope, self).__init__(**kwargs)
        self.client = client
        self.darksky = None

    def snapshot(self, int_time): #straight snapshot over a certain integration time.
        self.logger.info('Snapshot %d sec', int_time)
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

        self.logger.info('Moving to position %s, %s.', az, el)
        while True:
            self.client.set_azimuth_position(az)
            self.client.set_elevation_position(el)
            time.sleep(1)
            status = self.client.status
            if status.get("ShutdownError") == 11:
                # Ignore elevation overvelocity
                self.logger.warning('Elevation overvelocity shutdown. Resetting.')
                self.client.i_know_what_i_am_doing_unsafe_exit_shutdown()
            elif not status.get("Moving"):
                return
            self.logger.debug('Still moving, current position (%g, %g).', self.client.azimuth_position, self.client.elevation_position)

    def park(self):
        self.logger.info("Parking")
        self.point(250,50)


class Mode(Enum):
    gal = 'gal'
    az = 'az'
    grid = 'grid'

    def __str__(self):
        return self.value

arg_groups = {
    'General': {
        'int-time': dict(type=int, default=30, help='integration time', metavar='seconds',
                         bokeh=dict(low=0)),
        'gain': dict(type=int, default=45, help='SDR gain', metavar='dB',
                    bokeh=dict(start=0, end=65)),
        'repeat': dict(type=int, default=1, help='number of times to repeat scan',
                       bokeh=dict(low=1)),
        'ref': dict(default=False, action='store_true', help='measure 50Ω reference load'),
    },
    'Iterator': {
        'mode': dict(type=Mode, choices=list(Mode), default=Mode.gal),
        'start': dict(type=float, default=0, help='start'),
        'stop': dict(type=float, default=360, help='end'),
        'step': dict(type=float, default=2.5, help='step'),
        'darksky-offset': dict(type=float, default=0, help='darksky offset', metavar='°'),
    },
    'mode=grid': {
        'obj-name': dict(help='named object'),
        'lat': dict(type=float, help='center galactic latitude', metavar='°',
                    bokeh=dict(low=-180, high=180)),
        'lon': dict(type=float, help='center galactic longitude', metavar='°',
                    bokeh=dict(low=0, high=360)),
        'rotation': dict(type=float, help='grid rotation', metavar='°'),
        'rotation-frame': dict(default='iers', choices=('iers', 'galactic'), help='grid rotation frame'),
    },
}

class LoggingArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            logging.error(message)
        sys.exit(status)

def parse_args(args, defaults={}):
    parser = LoggingArgumentParser(description='Galactic sky scan')
    parser.add_argument('output_dir', metavar='DIRECTORY',
                        help='output directory to write scan results')
    parser.add_argument('--sdr-frequency', type=float,
                        help='change SDR frequency')
    parser.add_argument('--bandwidth', metavar='HZ', type=float,
                        help='change filter bandwidth')
    for group_name, group_args in arg_groups.items():
        group = parser.add_argument_group(group_name)
        for arg_name, kwargs in group_args.items():
            if 'bokeh' in kwargs:
                del kwargs['bokeh']
            group.add_argument('--'+arg_name, **kwargs)
    parser.set_defaults(**defaults)
    return parser.parse_args(args)

def run(tb, args):
    try:
        os.mkdir(args.output_dir)
    except OSError:
        pass

    iterator_cls = {
        Mode.gal: survey_autoranging.longitude_iterator,
        Mode.az: survey_autoranging.azimuth_iterator,
        Mode.grid: survey_autoranging.grid_iterator,
        }[args.mode]

    iterator = iterator_cls(**vars(args))

    if args.repeat:
        iterator = survey_autoranging.repeat(iterator, args.repeat)

    band=0
    tb.client.set_band_rx(band, not args.ref)
    survey_autoranging.run_survey(tb, savefolder=args.output_dir, int_time=args.int_time, darksky_offset=args.darksky_offset, iterator=iterator, args=args)
    tb.client.set_band_rx(band, False)
    tb.park()

def main(top_block_cls=radiotelescope, options=None):
    logging.basicConfig(
        format="%(asctime)-15s %(levelname)-8s [%(name)s] [%(module)s:%(funcName)s] %(message)s",
        level=logging.DEBUG,
    )
    args = parse_args(args)

    client = rci.client.Client(client_name='gal_scan')
    client.set_offsets(AZ_OFFSET, EL_OFFSET)

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
    logging.info('Receiving ...')

    try:
        run(tb, args)
    finally:
        tb.stop()
        tb.wait()

if __name__ == '__main__':
    main()
