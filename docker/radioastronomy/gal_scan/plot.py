#!/usr/bin/env python
# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import numpy as np
from numpy.polynomial.polynomial import polyfit, polyval
import matplotlib as mpl
import sys
if 'matplotlib.backends' not in sys.modules:
    mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os.path

def plot_freq(freq, freq_range, data, title):
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

AXIS_NAMES = {'azimuth': 'Azimuth', 'elevation': 'Elevation', 'longitude': 'Galactic Longitude', 'latitude': 'Galactic Latitude'}

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
            prefix = prefix - 360
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

    for suffix in ('', '_normalized'):
        for xaxis in contour_iter_axes:
            axis_data = contour_iter_axes[xaxis]
            shifted_xdata, shifted_ydata, shifted_contour_data = find_shift(axis_data, ydata, contour_data)

            if suffix:
                shifted_contour_data = correct_contour_data(shifted_contour_data)

            vmin = 0.8e-16
            vmin = max(vmin, np.percentile(shifted_contour_data[:, CORRECTION_POLY_POINTS], 50))
            vmax = np.percentile(shifted_contour_data, 95)

            plt.figure()
            plt.xlabel(AXIS_NAMES[xaxis])
            plt.ylabel(ylabel)
            plt.ticklabel_format(useOffset=False)
            plt.contourf(shifted_xdata, shifted_ydata, shifted_contour_data, 100, vmin=vmin, vmax=vmax)
            if savefolder:
                plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_contour'+suffix+'.pdf'))
                plt.close()

            plt.figure()
            plt.xlabel(AXIS_NAMES[xaxis])
            plt.ylabel(ylabel)
            plt.ticklabel_format(useOffset=False)
            pcm = plt.pcolormesh(shifted_xdata, shifted_ydata, shifted_contour_data, vmin=vmin, vmax=vmax, shading='gouraud', norm=colors.LogNorm())
            cbar = plt.colorbar(pcm, extend='max')
            cbar.ax.set_ylabel('Power at feed (W/Hz)', rotation=-90, va="bottom")
            if False: # show polynomial lines
                plt.plot(shifted_xdata[:,CORRECTION_POLY_POINTS], shifted_ydata[:,CORRECTION_POLY_POINTS])
            if savefolder:
                plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_mesh'+suffix+'.pdf'))
                plt.close()

CORRECTION_POLY_POINTS = np.array([75,100,125,150,175])# dsheen had 200,225,250 but those are within real data

def correct_contour_data(contour_data):
    # dsheen@'s polynomial fit algorithm

    points = CORRECTION_POLY_POINTS

    coefficients = polyfit(points, np.transpose(contour_data[:, points]), 1)

    correction_matrix = polyval(np.arange(contour_data.shape[1]), coefficients)

    if False: # visualize correction matrix
        plt.figure()
        pcm = plt.pcolormesh(correction_matrix)
        cbar = plt.colorbar(pcm, extend='max')
        plt.show()

    return contour_data - correction_matrix + np.median(coefficients[0])

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

    savefolder = None
    if mpl.get_backend().lower() == 'agg':
        savefolder = '.'

    plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes, savefolder=savefolder)

if __name__ == '__main__':
    main()
    plt.show()
