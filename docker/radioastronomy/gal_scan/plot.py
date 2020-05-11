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

from contextlib import contextmanager
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
    'rci_elevation': 'Actual Elevation',
    'rci_azimuth': 'Actual Azimuth',
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
    adiffs = np.abs(diffs)
    gap_index = adiffs.argmax()
    gap = adiffs[gap_index]
    if gap > 3*np.median(adiffs):
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

def add_colorbar(mappable, normalized):
    """Add a colorbar to the plot for mappable."""
    cbar = plt.colorbar(mappable, extend='max')
    cbar_ylabel = 'Estimated signal power' if normalized else 'Power'
    cbar.ax.set_ylabel(cbar_ylabel+' at feed (W/Hz)', rotation=-90, va="bottom")

def plot_observations(contour_iter_axes, savefolder=None):
    deg2rad = (2*np.pi)/360
    for (x, y) in (('longitude', 'latitude'), ('azimuth', 'elevation')):
        if x not in contour_iter_axes or y not in contour_iter_axes:
            continue
        plt.figure(figsize=(8,4.2))
        plt.subplot(111, projection="aitoff")
        plt.title("(%s, %s) observation positions" % (x,y))
        plt.grid(True)
        plt.plot(contour_iter_axes[x][:,0]*deg2rad, contour_iter_axes[y][:,0]*deg2rad, 'o', markersize=2, alpha=0.3)
        plt.subplots_adjust(top=0.95,bottom=0.0)
        plt.show()
        if savefolder:
            plt.savefig(os.path.join(savefolder, 'observations_'+x+'_'+y+'.pdf'))
            plt.close()

def plot_2d(contour_freqs, contour_vels, contour_data, contour_iter_axes, savefolder=None):
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
            if len(np.unique(contour_iter_axes[xaxis])) == 1:
                # 2D plots require multiple points
                continue
            @contextmanager
            def figure(name):
                fig = plt.figure()
                plt.xlabel(AXIS_NAMES.get(xaxis,xaxis))
                plt.ylabel(ylabel)
                plt.ticklabel_format(useOffset=False)
                yield fig
                if savefolder:
                    plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_'+name+suffix+'.pdf'))
                    plt.close()

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

            with figure('contour'):
                cntr = plt.contourf(shifted_xdata, shifted_ydata,
                                    np.clip(
                                        shifted_contour_data,
                                        vmin, vmax),
                                    100,
                                    extend='both',
                                    vmin=vmin, vmax=vmax)
                add_colorbar(cntr, normalized)

            norm = None
            if not normalized:
                norm = colors.LogNorm()

            with figure('mesh'):
                # pcolormesh without shading treats x and y as the
                # coordinates of the top left corner of the box.
                # So we need to shift the points up and to the left one half step so that the boxes are centered on the correct position.
                mesh_xdata = center_mesh_coords(shifted_xdata)
                mesh_ydata = center_mesh_coords(shifted_ydata)
                pcm = plt.pcolormesh(mesh_xdata, mesh_ydata, shifted_contour_data,
                                     vmin=vmin, vmax=vmax,
                                     norm=norm)
                add_colorbar(pcm, normalized)

            with figure('mesh_interpolated'):
                pcm = plt.pcolormesh(shifted_xdata, shifted_ydata, shifted_contour_data,
                                     vmin=vmin, vmax=vmax,
                                     shading='gouraud',
                                     norm=norm)
                add_colorbar(pcm, normalized)

def center_mesh_coords(data):
    """Shift coordinates in data by one half step,
    so that pcolormesh draws boxes in the right place."""
    mesh_data = (data[:-1] + data[1:]) / 2
    return np.concatenate((
        [2*data[0] - mesh_data[0]],
        mesh_data,
        [2*data[-1] - mesh_data[-1]],
    ))

def plot_polynomial_lines(xdata, ydata):
    """Plot lines showing where the polynomial fit was taken.

    Currently unused."""
    plt.plot(xdata[:, CORRECTION_POLY_POINTS],
             ydata[:, CORRECTION_POLY_POINTS])

def plot_sample_grid(xdata, ydata):
    """Show sample positions as thin grid lines.

    Currently unused.
    """
    ax = plt.gca()
    # Vertical grid lines
    segs1 = np.stack((xdata, ydata), axis=2)
    ax.add_collection(mpl.collections.LineCollection(segs1, color='lightgrey', linewidths=0.1))
    # Horizontal grid lines (too many lines if enabled)
    #segs2 = segs1.transpose(1, 0, 2)
    #ax.add_collection(mpl.collections.LineCollection(segs2))

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
    plot_observations(contour_iter_axes, savefolder=savefolder)

if __name__ == '__main__':
    main()
    plt.show()
