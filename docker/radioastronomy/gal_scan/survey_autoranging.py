# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import matplotlib as mpl
mpl.use('Agg')
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

LongitudePos = namedtuple('LongitudePos', 'azimuth elevation longitude latitude'.split())

class longitude_iterator(iterator):
    axes = {'azimuth': 'Azimuth', 'longitude': 'Galactic Longitude'}
    fields = LongitudePos._fields
    
    def translate(self, lon):
        pos=gal_to_altaz(lon,0)
        if pos[1] > 0:
            print('Moving to galactic longitude l=' + str(lon))
            return LongitudePos(*(pos + (lon, 0)))
        return None

    def format_filename(self, pos):
        return 'lat_%05.1f' % (pos.longitude,)

    def format_title(self, pos):
        return 'l=%.1f az=%.1f' % (pos.longitude, pos.azimuth)

AzimuthPos = namedtuple('AzimuthPos', 'azimuth elevation'.split())

class azimuth_iterator(iterator):
    axes = {'azimuth': 'Azimuth'}
    fields = AzimuthPos._fields

    def translate(self, az):
        return AzimuthPos(az, 0)

    def format_filename(self, pos):
        return 'az_%05.1f' % (pos.azimuth,)

    def format_title(self, pos):
        return 'az=%.1f' % (pos.azimuth,)

class grid_iterator(iterator):
    axes = {'azimuth': 'Azimuth', 'elevation': 'Elevation', 'latitude': 'Galactic Latitude', 'longitude': 'Galactic Longitude'}
    fields = LongitudePos._fields

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
        az, el = gal_to_altaz(sc.l/u.degree, sc.b/u.degree)
        if el > 0:
            return LongitudePos(az, el, sc.l/u.degree, sc.b/u.degree)
        return None

    def format_filename(self, pos):
        return 'latlon_%05.1f_%05.1f' % (pos.latitude, pos.longitude)

    def format_title(self, pos):
        return 'l=%.1f b=%.1f az=%.1f el=%.1f' % (pos.longitude, pos.latitude, pos.azimuth, pos.elevation)

def run_survey(tb, savefolder, iterator, gain=60, int_time=30):
    tb.set_sdr_gain(gain)
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)

    #########################################
    # BEGIN COMMANDS #
    #########################################

    #do the survey
    file=open(os.path.join(savefolder, 'vectors.txt'), 'w')
    csvwriter = csv.writer(open(os.path.join(savefolder, 'vectors.csv'), 'w'))
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    csvwriter.writerow(['# Integration time: %d seconds Center frequency: %f MHz' % (int_time, freq)])
    freq_count = 2 if 'pos' in iterator.fields else 1
    csvwriter.writerow(['time'] + list(iterator.fields) + [str(f) for f in freq_range]*freq_count)
    file.write(' '.join(iterator.fields) + ' Time Center Data_vector \n \n')

    contour_iter_axes = {field: [] for field in iterator.axes}
    contour_freqs = []
    contour_vels = []
    contour_data = []

    for pos in iterator:
        tb.point(pos.azimuth, pos.elevation)

        print("Observing at coordinates "+str(pos)+'.')
        apytime=get_time()
        data=tb.observe(int_time)

        #write to file
        file.write(' '.join(str(x) for x in pos) + ' ')
        file.write(str(apytime)+' ')
        file.write(str(data)+'\n \n')

        for field in iterator.axes:
            contour_iter_axes[field].append(np.full(len(freq_range), getattr(pos, field)))

        contour_freqs.append(freq_range)

        vel_range = None
        if hasattr(pos, 'longitude'):
            vel_range=np.array(freqs_to_vel(freq, freq_range, pos.longitude,pos.latitude))
            contour_vels.append(vel_range)

        contour_data.append(data)

        apytime.format = 'fits'
        row = [str(apytime)] + [str(x) for x in pos]
        if vel_range is not None:
            row += [str(f) for f in vel_range]
        row += [str(f) for f in data]
        csvwriter.writerow(row)

        plot.plot_freq(freq, freq_range, data, iterator.format_title(pos) + ' ' + str(apytime))
        plot.plt.savefig(os.path.join(savefolder, iterator.format_filename(pos)+'_freq.pdf'))
        plot.plt.close()

        if hasattr(pos, 'longitude'):
            plot.plot_velocity(vel_range, data, iterator.format_title(pos) + ' '+ str(apytime))
            plot.plt.savefig(os.path.join(savefolder, iterator.format_filename(pos)+'_vel.pdf'))
            plot.plt.close()

        print('Data logged.')
        print()

    file.close()

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

    plot.plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes, savefolder)
    plot.plot_observations(contour_iter_axes, savefolder)
