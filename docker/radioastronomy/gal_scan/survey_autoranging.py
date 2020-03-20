# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from galcoord import gal_to_altaz
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from galcoord import get_time
import os.path
import time
import csv
from collections import namedtuple

#convert frequency f to radial velocity at galactic coordinate l
#account for movement of the sun relative to galactic center
def freq_to_vel(center_freq, f,l):
    c=2.998e5 #km/s
    v_rec=(center_freq-f)*c/center_freq
    v_sun=220 #km/s
    correction=v_sun*np.sin(np.deg2rad(l))
    return v_rec+correction

class iterator(object):
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step
        self.pos = start

    def __iter__(self):
        return self

    def __next__(self):
        while self.pos <= self.stop:
            translated = self.translate(self.pos)
            self.pos += self.step
            if translated:
                return translated
        raise StopIteration
    next = __next__

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

def run_survey(tb, savefolder, iterator, gain=60, int_time=30):
    tb.set_sdr_gain(gain)
    freq=tb.get_sdr_frequency()/1000000 #MHzx
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)

    #########################################
    # BEGIN COMMANDS #
    #########################################
    large_step=1 #signals that the dish just moved a bunch and we need to wait longer for it to settle

    #do the survey
    file=open(os.path.join(savefolder, 'vectors.txt'), 'w')
    csvwriter = csv.writer(open(os.path.join(savefolder, 'vectors.csv'), 'w'))
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    csvwriter.writerow(['# Integration time: %d seconds Center frequency: %f MHz' % (int_time, freq)])
    csvwriter.writerow(['time'] + list(iterator.fields) + [str(f) for f in freq_range]*2)
    file.write(' '.join(iterator.fields) + ' Time Center Data_vector \n \n')

    contour_iter_axes = {field: [] for field in iterator.axes}
    contour_freqs = []
    contour_vels = []
    contour_data = []

    for pos in iterator:
        tb.point(pos.azimuth, pos.elevation)
        if large_step:
            time.sleep(10)
        else:
            time.sleep(2)
        large_step=0

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

        if hasattr(pos, 'longitude'):
            vel_range=np.array([freq_to_vel(freq, f,pos.longitude) for f in freq_range])
            contour_vels.append(vel_range)

        contour_data.append(data)

        apytime.format = 'fits'
        csvwriter.writerow([str(apytime)] + [str(x) for x in pos] + [str(f) for f in vel_range] + [str(f) for f in data])

        #frequency binned figure
        plt.figure()
        plt.title(iterator.format_title(pos)+ ' '+ str(apytime))
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Power at Feed (W/Hz)')
        plt.axvline(x=freq, color='black', ls='--')
        plt.ticklabel_format(useOffset=False)
        plt.plot(freq_range, data)
        plt.savefig(os.path.join(savefolder, iterator.format_filename(pos)+'_freq.pdf'))
        plt.close()

        if hasattr(pos, 'longitude'):
            #velocity binned figure
            center_vel=freq_to_vel(freq, freq, pos.longitude)

            plt.figure()
            plt.title(iterator.format_title(pos) + ' '+ str(apytime))
            plt.xlabel('Velocity (km/s)')
            plt.ylabel('Power at Feed (W)')
            plt.axvline(x=0, color='black', ls='--')
            plt.ticklabel_format(useOffset=False)
            plt.plot(vel_range, data)
            plt.savefig(os.path.join(savefolder, iterator.format_filename(pos)+'_vel.pdf'))
            plt.close()

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

    # TODO: Plot both
    ydata = contour_freqs
    ylabel = 'Frequency (MHz)'
    if contour_vels:
        contour_vels = np.array(contour_vels)
        np.save(os.path.join(savefolder, 'contour_vels.npy'), contour_vels)
        ydata = contour_vels
        ylabel = 'Velocity (km/s)'

    for xaxis, xlabel in iterator.axes.items():
        plt.figure()
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        plt.contourf(contour_iter_axes[xaxis], ydata, contour_data, 100, vmin=0.8e-16, vmax=3e-16)
        plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_contour.pdf'))
        plt.close()

        plt.figure()
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        pcm = plt.pcolormesh(contour_iter_axes[xaxis], ydata, contour_data, vmin=0.8e-16, vmax=2e-16, shading='gouraud', norm=colors.PowerNorm(0.6))
        cbar = plt.colorbar(pcm, extend='max')
        cbar.ax.set_ylabel('Power at feed (W/Hz)', rotation=-90, va="bottom")
        plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_mesh.pdf'))
        plt.close()
