#!/usr/bin/env python
"""Plotting functions and command.

plot contains functions used by survey_autoranging to plot
observations in several different ways. It can also be run directly
from the command line or IPython to regenerate those plots; see
README.md for further instructions.

"""

# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import sys
import os.path
import numpy as np
from numpy.polynomial.polynomial import polyfit, polyval
import matplotlib as mpl
if 'matplotlib.backends' not in sys.modules:
    mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors

def plot_freq(freq, freq_range, data, title):
    """Plot a frequency binned figure."""
    plt.figure()
    plt.title(title)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Power at Feed (W/Hz)')
    plt.axvline(x=freq, color='black', ls='--')
    plt.ticklabel_format(useOffset=False)
    plt.plot(freq_range, data)

def plot_velocity(vel_range, data, title):
    """Plot a velocity binned figure."""
    plt.figure()
    plt.title(title)
    plt.xlabel('Velocity (km/s)')
    plt.ylabel('Power at Feed (W)')
    plt.axvline(x=0, color='black', ls='--')
    plt.ticklabel_format(useOffset=False)
    plt.plot(vel_range, data)

AXIS_NAMES = {
    'azimuth': 'Azimuth',
    'elevation': 'Elevation',
    'longitude': 'Galactic Longitude',
    'latitude': 'Galactic Latitude',
}

def find_shift(axis_data, ydata, contour_data):
    """Eliminate wraparound discontinuities if necessary.

    If there is a discontinuity in the axis (e.g. missed scan data
    below the horizon), find the number of rows to move from the end
    to the start, and reattach the discontinuous rows.

    Returns:
        The input arrays, possibly shifted to remove a discontinuity.

    """
    axis = axis_data[:, 0]
    diffs = np.diff(axis)
    gap_index = diffs.argmax()
    gap = diffs[gap_index]
    if abs(gap) > 3*np.median(diffs):
        # We found a gap > 3x the median gap. This probably means
        # there was a discontinuity in the plot when the scan wrapped
        # around the horizon.
        # np.diff returns x[n+1]-x[n], so gap_index points at the last element before the gap.

        # Remove gap_index rows from the axis and data arrays and prepend those rows.
        gap_index += 1
        prefix = axis_data[gap_index:]
        suffix = axis_data[:gap_index]
        if diffs[0] > 0:
            prefix = prefix - 360
        axis_data = np.concatenate((prefix, suffix))
        ydata = np.roll(ydata, -gap_index, 0)
        contour_data = np.roll(contour_data, -gap_index, 0)
    return axis_data, ydata, contour_data

def plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes, savefolder=None, show_polynomial_lines=False):
    """2D plot of (position, frequency, brightness).

    If velocity information is available, the Y-axis shows velocity
    instead of frequency.

    Args:
        contour_freqs: 2D array of frequencies corresponding to each point in contour_data
        contour_vels: None or 2D array of velocities corresponding to each point in contour_data
        contour_data: 2D array of observations
        contour_iter_axes: dictionary of {
            position type: 2D array of positions corresponding to each point in contour_data
            }
        savefolder: string location to save plots, if specified
    """
    # TODO: Plot both frequency and velocity
    ydata = contour_freqs
    ylabel = 'Frequency (MHz)'
    if contour_vels is not None:
        ydata = contour_vels
        ylabel = 'Velocity (km/s)'

    for normalized in (False, True):
        for xaxis in contour_iter_axes:
            suffix = '_normalized' if normalized else ''
            shifted_xdata, shifted_ydata, shifted_contour_data = find_shift(
                contour_iter_axes[xaxis], ydata, contour_data)

            if normalized:
                shifted_contour_data = correct_contour_data(shifted_contour_data)

            # Calculate reasonable bounds for the Z axis.
            # The minimum is selected as the median value in the background portion of the plot.
            # The maximum is the 95th percentile value across the whole plot.
            vmin = np.percentile(shifted_contour_data[:, CORRECTION_POLY_POINTS], 50)
            if not normalized:
                vmin = max(0.8e-16, vmin)
            vmax = np.percentile(shifted_contour_data, 95)

            plt.figure()
            plt.xlabel(AXIS_NAMES[xaxis])
            plt.ylabel(ylabel)
            plt.ticklabel_format(useOffset=False)
            plt.contourf(shifted_xdata, shifted_ydata, shifted_contour_data, 100,
                         vmin=vmin, vmax=vmax)
            if savefolder:
                plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_contour'+suffix+'.pdf'))
                plt.close()

            plt.figure()
            plt.xlabel(AXIS_NAMES[xaxis])
            plt.ylabel(ylabel)
            plt.ticklabel_format(useOffset=False)
            norm = None
            if not normalized:
                norm = colors.LogNorm()
            pcm = plt.pcolormesh(shifted_xdata, shifted_ydata, shifted_contour_data,
                                 vmin=vmin, vmax=vmax,
                                 shading='gouraud',
                                 norm=norm)
            cbar = plt.colorbar(pcm, extend='max')
            ylabel = 'Estimated signal power' if normalized else 'Power'
            cbar.ax.set_ylabel(ylabel+' at feed (W/Hz)', rotation=-90, va="bottom")
            if show_polynomial_lines:
                plt.plot(shifted_xdata[:, CORRECTION_POLY_POINTS],
                         shifted_ydata[:, CORRECTION_POLY_POINTS])
            if savefolder:
                plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_mesh'+suffix+'.pdf'))
                plt.close()

# Hand-tuned points that fall outside the region of interest.
# These indices are used to estimate background noise level.
CORRECTION_POLY_POINTS = np.array([75, 100, 125, 150, 175])
# dsheen had 200, 225, 250 but those are within real data

def correct_contour_data(contour_data, visualize=False):
    """dsheen@'s polynomial fit algorithm

    This algorithm performs a first-order fit on noise information
    found in the first half of the spectrum for each position, then
    subtracts that estimated noise.

    If visualize is true, the estimated background noise will be plotted.

    The returned data represents the estimated observed signal power.
    """

    points = CORRECTION_POLY_POINTS

    coefficients = polyfit(points, np.transpose(contour_data[:, points]), 1)

    correction_matrix = polyval(np.arange(contour_data.shape[1]), coefficients)

    if visualize: # visualize correction matrix
        plt.figure()
        pcm = plt.pcolormesh(correction_matrix)
        plt.colorbar(pcm, extend='max')
        plt.show()

    # To restore average background noise level: + np.median(coefficients[0])
    return contour_data - correction_matrix

def load_data():
    """Load existing data files.

    Returns:
        dict of {type: array}
    """
    contour_iter_axes = {}
    for name in glob.glob("contour_*.npy"):
        key = name.split('_', 1)[1].rsplit('.', 1)[0]
        contour_iter_axes[key] = np.load(name)
    return contour_iter_axes

def main():
    # Invoke plot.py to replot an existing dataset

    contour_iter_axes = load_data()
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
