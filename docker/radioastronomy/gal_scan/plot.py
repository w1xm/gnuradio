#!/usr/bin/env python
# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os.path

def plot_freq(freq_range, data, title):
    #frequency binned figure
    plt.figure()
    plt.title(title)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Power at Feed (W/Hz)')
    plt.axvline(x=freq, color='black', ls='--')
    plt.ticklabel_format(useOffset=False)
    plt.plot(freq_range, data)

def plot_velocity(vel_range, data, title):
    #velocity binned figure
    plt.figure()
    plt.title(title)
    plt.xlabel('Velocity (km/s)')
    plt.ylabel('Power at Feed (W)')
    plt.axvline(x=0, color='black', ls='--')
    plt.ticklabel_format(useOffset=False)
    plt.plot(vel_range, data)

AXIS_NAMES = {'azimuth': 'Azimuth', 'longitude': 'Galactic Longitude'}

def find_shift(axis_data, ydata, contour_data):
    # If there is a discontinuity in the axis (e.g. missed scan data
    # below the horizon), find the number of rows to move from the end
    # to the start.
    axis = axis_data[:,0]
    diffs = np.diff(axis)
    gap_index = diffs.argmax()
    gap = diffs[gap_index]
    if abs(gap) > 3*np.median(diffs):
        gap_index += 1
        prefix = axis_data[gap_index:]
        suffix = axis_data[:gap_index]
        if diffs[0] > 0:
            prefix -= 360
        axis_data = np.concatenate((prefix, suffix))
        ydata = np.roll(ydata, -gap_index, 0)
        contour_data = np.roll(contour_data, -gap_index, 0)
    return axis_data, ydata, contour_data

def plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes, savefolder=None):
    # TODO: Plot both
    ydata = contour_freqs
    ylabel = 'Frequency (MHz)'
    if contour_vels is not None:
        ydata = contour_vels
        ylabel = 'Velocity (km/s)'

    for xaxis in contour_iter_axes:
        axis_data = contour_iter_axes[xaxis]
        shifted_xdata, shifted_ydata, shifted_contour_data = find_shift(axis_data, ydata, contour_data)
        plt.figure()
        plt.xlabel(AXIS_NAMES[xaxis])
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        plt.contourf(shifted_xdata, shifted_ydata, shifted_contour_data, 100, vmin=0.8e-16, vmax=3e-16)
        if savefolder:
            plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_contour.pdf'))
            plt.close()

        plt.figure()
        plt.xlabel(AXIS_NAMES[xaxis])
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        pcm = plt.pcolormesh(shifted_xdata, shifted_ydata, shifted_contour_data, vmin=0.8e-16, vmax=np.percentile(contour_data, 90), shading='gouraud', norm=colors.LogNorm())
        cbar = plt.colorbar(pcm, extend='max')
        cbar.ax.set_ylabel('Power at feed (W/Hz)', rotation=-90, va="bottom")
        if savefolder:
            plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_mesh.pdf'))
            plt.close()

def main():
    # Invoke plot.py to replot an existing dataset
    contour_iter_axes = {}
    for f in glob.glob("contour_*.npy"):
        key = f.split('_', 1)[1].rsplit('.', 1)[0]
        contour_iter_axes[key] = np.load(f)

    contour_freqs = contour_iter_axes.pop('freqs')
    contour_data = contour_iter_axes.pop('data')
    contour_vels = None
    if 'vels' in contour_iter_axes:
        contour_vels = contour_iter_axes.pop('vels')

    print("Plotting axes:", contour_iter_axes.keys())

    plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes)

if __name__ == '__main__':
    main()
    plt.show()
