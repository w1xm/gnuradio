# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import matplotlib as mpl
mpl.use('Agg')
from galcoord import HYDROGEN_FREQ
from galcoord import radome_observer
from galcoord import altaz_frame
from galcoord import freqs_to_vel
from galcoord import directional_offset_by
from enum import Enum
import numpy as np
from galcoord import get_time
import logging
import os.path
import itertools
import time
import csv
from collections import namedtuple
import plot
from astropy.coordinates import SkyCoord, SkyOffsetFrame, get_body
from astropy import units as u
from astropy.table import QTable, Column
from astropy.time import TimeDelta

AZ_OFFSET=5.5
EL_OFFSET=-5.5

class iterator(object):
    """iterator emits a series of SkyCoord objects that represent observation positions."""
    def __init__(self, start, stop, step, **kwargs):
        self.start = start
        self.stop = stop
        self.step = step

    @property
    def iter_source(self):
        return np.arange(self.start, self.stop+self.step, self.step)

    @property
    def coords(self):
        raise NotImplementedError('coords was not overridden')

    def __iter__(self):
        return self.coords

    def transform(self, value):
        return value

class longitude_iterator(iterator):
    @property
    def coords(self):
        return SkyCoord(l=self.iter_source*u.degree, b=0*u.degree, frame='galactic')

    def format_filename(self, pos):
        return 'lon_%05.1f' % (pos['longitude'].degree,)

    def format_title(self, pos):
        return 'l=%.1f az=%.1f' % (pos['longitude'].degree, pos['azimuth'].degree)

class azimuth_iterator(iterator):
    @property
    def coords(self):
        return SkyCoord(az=self.iter_source*u.degree, alt=0*u.degree, frame='altaz')

    def format_filename(self, pos):
        return 'az_%05.1f' % (pos['azimuth'].degree,)

    def format_title(self, pos):
        return 'az=%.1f' % (pos['azimuth'].degree,)

class grid_iterator(iterator):
    def __init__(self, start, stop, step, rotation, rotation_frame, obj_name, lat, lon, **kwargs):
        if obj_name:
            self.center = SkyCoord.from_name(obj_name)
        else:
            self.center = SkyCoord(l=lon*u.degree, b=lat*u.degree, frame='galactic')
        if rotation:
            self.center = self.center.transform_to(rotation_frame)
        else:
            rotation = 0
        steps = np.arange(start, stop+step, step)
        sc = directional_offset_by(
            directional_offset_by(self.center, rotation*u.degree, steps*u.degree),
            (rotation+90)*u.degree, np.expand_dims(steps, 1)*u.degree)
        self._coords = sc.galactic.flatten()

    @property
    def coords(self):
        return self._coords

    def format_filename(self, pos):
        return 'latlon_%05.1f_%05.1f' % (pos['latitude'], pos['longitude'])

    def format_title(self, pos):
        return 'l=%.1f b=%.1f az=%.1f el=%.1f' % (pos['longitude'].degree, pos['latitude'].degree, pos['azimuth'].degree, pos['elevation'].degree)

class solar_grid_iterator(iterator):
    def __init__(self, start, stop, step, body_name, **kwargs):
        super().__init__(start, stop, step)
        # Check that body_name is valid
        get_body(body_name, time=get_time())
        self.body_name = body_name

    @property
    def coords(self):
        t = get_time()
        body = get_body(self.body_name, time=t)
        grid = np.mgrid[self.start:(self.stop+self.step):self.step, self.start:(self.stop+self.step):self.step]
        return SkyCoord(grid[0]*u.degree, grid[1]*u.degree, frame=SkyOffsetFrame(origin=body, obstime=t)).flatten()

    def __iter__(self):
        def correct(point):
            t = get_time()
            body = get_body(self.body_name, time=t)
            return SkyCoord(point.lon, point.lat, frame=SkyOffsetFrame(origin=body, obstime=t))
        return (correct(point) for point in self.coords)

    def format_filename(self, pos):
        return 'offset_%05.1f_%05.1f' % (pos['skyoffset_latitude'], pos['skyoffset_longitude'])

    def format_title(self, pos):
        return '%s offset lon=%.1f lat=%.1f az=%.1f el=%.1f' % (self.body_name, pos['skyoffset_longitude'].degree, pos['latitude'].degree, pos['azimuth'].degree, pos['elevation'].degree)

POSITION_FIELDS = ('time', 'azimuth', 'elevation', 'longitude', 'latitude', 'ra', 'dec', 'rci_azimuth', 'rci_elevation')

class Mode(Enum):
    gal = 'gal'
    az = 'az'
    grid = 'grid'
    solar_grid = 'solar_grid'

    def __str__(self):
        return self.value

class Survey:
    logger = logging.getLogger("survey")

    def __init__(self, args):
        self.args = args
        iterator_cls = {
            Mode.gal: longitude_iterator,
            Mode.az: azimuth_iterator,
            Mode.grid: grid_iterator,
            Mode.solar_grid: solar_grid_iterator,
        }[args.mode]

        self.iterator = iterator_cls(**vars(args))
        self.repeat = args.repeat or 1

    def run(self, tb):
        try:
            os.mkdir(self.args.output_dir)
        except OSError:
            pass
        band=0
        tb.client.set_band_rx(band, not self.args.ref)
        self._run_survey(tb)
        tb.client.set_band_rx(band, False)
        tb.park()

    @property
    def time_remaining(self):
        # TODO: Track how many points have already been done
        pos = self.iterator.coords._apply(np.tile, self.repeat)
        aaf = altaz_frame(get_time())
        if pos.frame.name == 'altaz':
            # Replace altaz frame with one that has obstime and location
            pos_altaz = SkyCoord(pos, frame=aaf)
        else:
            pos_altaz = pos.transform_to(aaf)
        above_horizon = len(pos_altaz[pos_altaz.alt >= EL_OFFSET*u.degree])
        if self.args.darksky_offset:
            above_horizon *= 2
        return TimeDelta((above_horizon * (self.args.int_time + 5)) * u.second)

    @property
    def coords(self):
        return itertools.chain(*((self.iterator,)*self.repeat))

    def _run_survey(self, tb, ref_frequency=HYDROGEN_FREQ):
        savefolder = self.args.output_dir
        int_time = self.args.int_time
        darksky_offset = self.args.darksky_offset

        tb.set_sdr_gain(self.args.gain)
        freq=tb.get_sdr_frequency()*u.Hz
        gain=tb.get_sdr_gain()*u.dB
        freq_offset=tb.get_output_vector_bandwidth()*u.Hz/2
        freq_range=np.linspace(freq-freq_offset, freq+freq_offset, tb.get_num_channels())

        #########################################
        # BEGIN COMMANDS #
        #########################################

        file=open(os.path.join(savefolder, 'info.txt'), 'w')
        csvwriter = csv.writer(open(os.path.join(savefolder, 'vectors.csv'), 'w'))
        file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
        file.write('Original arguments:\n' + str(self.args))
        file.close()

        csvwriter.writerow(['# Integration time: %d seconds Center frequency: %s' % (int_time, freq)])
        freq_count = 2
        csvwriter.writerow(list(POSITION_FIELDS) + [str(f) for f in freq_range]*freq_count)

        # all_data is a list of dictionaries containg all information about a run;
        # 'data' contains the raw data, 'freqs' contains the frequency for each sample
        # 'time' contains the observation time
        # 'rci_azimuth' and 'rci_elevation' contain the actual azimuth and elevation for the observation
        # all other fields come from pos
        all_data = []

        try:
            for number, pos in enumerate(self.coords):
                for darksky in (False, True):
                    if darksky and not darksky_offset:
                        continue
                    apytime=get_time()
                    aaf = altaz_frame(apytime, obswl=freq.to(u.cm, u.spectral()))
                    if pos.frame.name == 'altaz':
                        # Replace altaz frame with one that has obstime and location
                        pos = SkyCoord(pos, frame=aaf)
                        pos_altaz = pos
                    else:
                        pos_altaz = pos.transform_to(aaf)

                    row = {}

                    if isinstance(pos.frame, SkyOffsetFrame):
                        row.update({
                            'body_name': self.args.body_name,
                            'skyoffset_latitude': pos.lat,
                            'skyoffset_longitude': pos.lon,
                        })

                    if darksky:
                        pos_altaz = directional_offset_by(pos_altaz, 90*u.degree, darksky_offset*u.degree)
                        pos = pos_altaz
                    if pos_altaz.alt < EL_OFFSET*u.degree:
                        self.logger.warning("Can't observe at %s; target alt %s is below the horizon", pos, pos_altaz.alt)
                        continue
                    tb.point(pos_altaz.az.degree, pos_altaz.alt.degree)

                    if pos.location is None:
                        pos.location = radome_observer.location
                    if pos.obstime is None:
                        pos.obstime = apytime

                    self.logger.info("Observing at coordinates %s.", pos)
                    data=tb.observe(int_time)*(u.mW/u.Hz)

                    apytime.format = 'unix'
                    row.update({
                        'mode': str(self.args.mode),
                        'gain': gain,
                        'number': number,
                        'data': data,
                        'freqs': freq_range,
                        'time': apytime.value*u.second,
                        'temperature': pos_altaz.frame.temperature,
                        'relative_humidity': pos_altaz.frame.relative_humidity,
                        'pressure': pos_altaz.frame.pressure,
                        'azimuth': pos_altaz.az,
                        'elevation': pos_altaz.alt,
                        'longitude': pos.galactic.l,
                        'latitude': pos.galactic.b,
                        'ra': pos.icrs.ra,
                        'dec': pos.icrs.dec,
                        'rci_azimuth': tb.client.azimuth_position*u.degree,
                        'rci_elevation': tb.client.elevation_position*u.degree,
                    })
                    # TODO: When we move to AstroPy 3+ (with Python 3+) we can
                    # just write time, pos and pos_altaz directly to the table.
                    if darksky_offset:
                        row['darksky'] = darksky

                    vel_range = None
                    if ref_frequency is not None and pos.frame.name != 'altaz':
                        vel_range=freqs_to_vel(ref_frequency, freq_range.to(u.MHz), pos)
                        row['vels'] = vel_range

                    all_data.append(row)

                    if not darksky:
                        # Only generate legacy data and plots for non-darksky data.
                        apytime.format = 'fits'
                        csvrow = [str(row[x]) for x in POSITION_FIELDS]
                        if vel_range is not None:
                            csvrow += [str(f) for f in vel_range]
                        csvrow += [str(f) for f in data]
                        csvwriter.writerow(csvrow)

                        prefix=os.path.join(savefolder, 'observation_%d' % (number))

                        plot.plot_freq(freq, freq_range, data, self.iterator.format_title(row) + ' ' + str(apytime), prefix+'_freq.pdf')

                        if 'vels' in row:
                            plot.plot_velocity(vel_range, data, self.iterator.format_title(row) + ' '+ str(apytime), prefix+'_vel.pdf')

                    self.logger.info('Data logged.')

        finally:
            if not all_data:
                self.logger.warning('No observations found! Not saving data.')
            else:
                all_data = QTable(all_data)

                plot.save_data(all_data, savefolder)

                plot.plot(all_data, savefolder=savefolder)
