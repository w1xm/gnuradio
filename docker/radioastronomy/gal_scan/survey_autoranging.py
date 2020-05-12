# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import matplotlib as mpl
mpl.use('Agg')
from galcoord import altaz_frame
from galcoord import freqs_to_vel
from galcoord import gal_to_altaz
from galcoord import directional_offset_by
import numpy as np
from galcoord import get_time
import os.path
import itertools
import time
import csv
from collections import namedtuple
import plot
from astropy.coordinates import SkyCoord
from astropy import units as u

class iterator(object):
    """iterator emits a series of SkyCoord objects that represent observation positions."""
    def __init__(self, start, stop, step, **kwargs):
        self.start = start
        self.stop = stop
        self.step = step
        self.iter_source = np.arange(start, stop+step, step)

    def __iter__(self):
        self.iter = iter(self.iter_source)
        return self

    def __next__(self):
        while True:
            pos = next(self.iter)
            translated = self.translate(pos)
            if translated:
                return translated
    next = __next__

class repeat(object):
    def __init__(self, wrapped, count):
        self.wrapped = wrapped
        self.count = count

    def __iter__(self):
        return itertools.chain(*((self.wrapped,)*self.count))

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

class longitude_iterator(iterator):
    def translate(self, lon):
        return SkyCoord(l=lon*u.degree, b=0*u.degree, frame='galactic')

    def format_filename(self, pos):
        return 'lon_%05.1f' % (pos['longitude'],)

    def format_title(self, pos):
        return 'l=%.1f az=%.1f' % (pos['longitude'], pos['azimuth'])

class azimuth_iterator(iterator):
    def translate(self, az):
        return SkyCoord(az=az*u.degree, alt=0*u.degree, frame=altaz_frame())

    def format_filename(self, pos):
        return 'az_%05.1f' % (pos['azimuth'],)

    def format_title(self, pos):
        return 'az=%.1f' % (pos['azimuth'],)

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
        self.coords = sc.galactic.flatten()
        self.iter_source = self.coords

    def translate(self, sc):
        return sc

    def format_filename(self, pos):
        return 'latlon_%05.1f_%05.1f' % (pos['latitude'], pos['longitude'])

    def format_title(self, pos):
        return 'l=%.1f b=%.1f az=%.1f el=%.1f' % (pos['longitude'], pos['latitude'], pos['azimuth'], pos['elevation'])

POSITION_FIELDS = ('time', 'azimuth', 'elevation', 'longitude', 'latitude', 'ra', 'dec', 'rci_azimuth', 'rci_elevation')

def run_survey(tb, savefolder, iterator, args, gain=60, int_time=30, darksky_offset=0):
    tb.set_sdr_gain(gain)
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    freq_range=np.linspace(freq-freq_offset, freq+freq_offset, tb.get_num_channels())

    #########################################
    # BEGIN COMMANDS #
    #########################################

    file=open(os.path.join(savefolder, 'info.txt'), 'w')
    csvwriter = csv.writer(open(os.path.join(savefolder, 'vectors.csv'), 'w'))
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    file.write('Original arguments:\n' + str(args))
    file.close()

    csvwriter.writerow(['# Integration time: %d seconds Center frequency: %f MHz' % (int_time, freq)])
    freq_count = 2
    csvwriter.writerow(list(POSITION_FIELDS) + [str(f) for f in freq_range]*freq_count)

    # all_data is a list of dictionaries containg all information about a run;
    # 'data' contains the raw data, 'freqs' contains the frequency for each sample
    # 'time' contains the observation time
    # 'rci_azimuth' and 'rci_elevation' contain the actual azimuth and elevation for the observation
    # all other fields come from pos
    all_data = []
    # Legacy arrays
    contour_iter_axes = {field: [] for field in POSITION_FIELDS}
    contour_freqs = []
    contour_vels = []
    contour_data = []

    for number, pos in enumerate(iterator):
        for darksky in (False, True):
            if darksky and not darksky_offset:
                continue
            apytime=get_time()
            pos_altaz = pos.transform_to(altaz_frame(apytime))
            if darksky:
                pos_altaz = SkyCoord(pos_altaz.az+darksky_offset*u.degree, pos_altaz.alt, frame=pos_altaz.frame)
                pos = pos_altaz
            if pos_altaz.alt < 0:
                print("Can't observe at %s; target is below the horizon" % pos)
                continue
            tb.point(pos_altaz.az.degree, pos_altaz.alt.degree)

            print("Observing at coordinates "+str(pos)+'.')
            data=tb.observe(int_time)

            apytime.format = 'unix'
            row = {
                'mode': str(args.mode),
                'number': number,
                'data': data,
                'freqs': freq_range,
                'time': apytime.value,
                'azimuth': pos_altaz.az.degree,
                'elevation': pos_altaz.alt.degree,
                'longitude': pos.galactic.l.degree,
                'latitude': pos.galactic.b.degree,
                'ra': pos.icrs.ra.degree,
                'dec': pos.icrs.dec.degree,
                'rci_azimuth': tb.client.azimuth_position,
                'rci_elevation': tb.client.elevation_position,
            }
            if darksky_offset:
                row['darksky'] = darksky

            vel_range = None
            if 'longitude' in row:
                vel_range=np.array(freqs_to_vel(freq, freq_range, row['longitude'],row.get('latitude', 0)))
                row['vels'] = vel_range

            all_data.append(row)

            if not darksky:
                # Only generate legacy data and plots for non-darksky data.
                for field in POSITION_FIELDS:
                    contour_iter_axes[field].append(np.full(len(freq_range), row[field]))

                contour_freqs.append(freq_range)
                if vel_range is not None:
                    contour_vels.append(vel_range)

                contour_data.append(data)

                apytime.format = 'fits'
                csvrow = [str(row[x]) for x in POSITION_FIELDS]
                if vel_range is not None:
                    csvrow += [str(f) for f in vel_range]
                csvrow += [str(f) for f in data]
                csvwriter.writerow(csvrow)

                prefix=os.path.join(savefolder, 'observation_%d' % (number))

                plot.plot_freq(freq, freq_range, data, iterator.format_title(row) + ' ' + str(apytime), prefix+'_freq.pdf')

                if 'longitude' in row:
                    plot.plot_velocity(vel_range, data, iterator.format_title(row) + ' '+ str(apytime), prefix+'_vel.pdf')

            print('Data logged.')
            print()

    all_data = dicts2array(all_data)
    np.save(os.path.join(savefolder, 'all_data.npy'), all_data)

    contour_iter_axes = {x: np.array(y) for x, y in contour_iter_axes.items()}
    contour_freqs = np.array(contour_freqs)
    contour_data = np.array(contour_data)

    for field, data in contour_iter_axes.items():
        np.save(os.path.join(savefolder, 'contour_'+field+'.npy'), data)
    np.save(os.path.join(savefolder, 'contour_data.npy'), contour_data)
    np.save(os.path.join(savefolder, 'contour_freqs.npy'), contour_freqs)
    if contour_vels:
        contour_vels = np.array(contour_vels)
        np.save(os.path.join(savefolder, 'contour_vels.npy'), contour_vels)

    plot.plot(all_data, savefolder=savefolder)

def dicts2array(dicts):
    dt_tuples = []
    for key, value in dicts[0].items():
        if not isinstance(value, str):
            value_dtype = np.array([value]).dtype
            shape = np.array([value]).shape[1:]
        else:
            value_dtype = '|S{}'.format(max([len(d[key]) for d in dicts]))
            shape = ()
        dt_tuples.append((key, value_dtype, shape))
    dt = np.dtype(dt_tuples)
    values = [tuple(d[name] for name in dt.names) for d in dicts]
    try:
        return np.array(values, dtype=dt)
    except ValueError:
        print(values, dt)
        raise
