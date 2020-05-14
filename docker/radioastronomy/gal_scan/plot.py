#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Plotting functions and command.

plot contains functions used by survey_autoranging to plot
observations in several different ways. It can also be run directly
from the command line or IPython to regenerate those plots; see
README.md for further instructions.

"""

# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
from contextlib import contextmanager
import glob
import sys
import os.path
import numpy as np
from numpy.polynomial.polynomial import polyfit, polyval
try:
    from numpy.lib.recfunctions import izip_records
except ImportError:
    from numpy.lib.recfunctions import _izip_records as izip_records
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
from astropy.table import Column, Table
from astropy.time import Time
from scipy import ndimage
import matplotlib as mpl
if 'matplotlib.backends' not in sys.modules:
    mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from astropy.visualization import quantity_support
quantity_support()

def plot_freq(freq, freq_range, data, title, filename):
    """Plot a frequency binned figure."""
    plt.figure()
    plt.title(title)
    plt.xlabel('Frequency (%s)' % (freq_range.unit,))
    plt.ylabel('Power at Feed (%s)' % (data.unit,))
    plt.ticklabel_format(useOffset=False)
    plt.plot(freq_range, data)
    if freq:
        plt.axvline(x=freq.to_value(freq_range.unit), color='black', ls='--')
    if filename:
        plt.savefig(filename)
        plt.close()

def plot_velocity(vel_range, data, title, filename):
    """Plot a velocity binned figure."""
    plt.figure()
    plt.title(title)
    plt.xlabel('Velocity (%s)' % (vel_range.unit,))
    plt.ylabel('Power at Feed (%s)' % (data.unit,))
    plt.ticklabel_format(useOffset=False)
    plt.plot(vel_range, data)
    plt.axvline(x=0, color='black', ls='--')
    if filename:
        plt.savefig(filename)
        plt.close()

AXIS_NAMES = {
    'azimuth': 'Azimuth',
    'elevation': 'Elevation',
    'longitude': 'Galactic Longitude',
    'latitude': 'Galactic Latitude',
    'rci_elevation': 'Actual Elevation',
    'rci_azimuth': 'Actual Azimuth',
}

def find_shift(all_data, axis):
    """Eliminate wraparound discontinuities if necessary.

    If there is a discontinuity in the axis (e.g. missed scan data
    below the horizon), find the number of rows to move from the end
    to the start, and reattach the discontinuous rows.

    Returns:
        The input array, possibly shifted to remove a discontinuity.

    """
    all_data = all_data.copy()
    all_data.sort(axis)
    axis_data = all_data[axis]
    diffs = np.diff(axis_data)
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
        all_data[axis][gap_index:] -= 360
        all_data.sort(axis)
    return all_data

def add_colorbar(mappable, unit, normalized):
    """Add a colorbar to the plot for mappable."""
    cbar = plt.colorbar(mappable, extend='max')
    cbar_ylabel = 'Estimated signal power' if normalized else 'Power'
    cbar.ax.set_ylabel(cbar_ylabel+' at feed (%s)' % (unit,), rotation=-90, va="bottom")

def plot_observations(all_data, bad_data, savefolder=None):
    deg2rad = (2*np.pi)/360
    for (x, y) in (('longitude', 'latitude'), ('azimuth', 'elevation'), ('rci_azimuth', 'rci_elevation'), ('ra', 'dec')):
        if x not in all_data.dtype.fields or y not in all_data.dtype.fields:
            continue
        plt.figure(figsize=(8,4.2))
        plt.subplot(111, projection="aitoff")
        plt.title("(%s, %s) observation positions" % (x,y), y=1.08)
        plt.grid(True)
        for data, marker, cmap in ((all_data, 'o', 'winter'), (bad_data, 'x', 'autumn')):
            c = None
            if 'darksky' in data.dtype.fields:
                c = data['darksky']
            xaxis = Angle(data[x], unit=u.deg).wrap_at(180*u.deg).radian
            yaxis = Angle(data[y], unit=u.deg).wrap_at(90*u.deg).radian
            plt.scatter(xaxis, yaxis, c=c, cmap=cmap, marker=marker, s=2, alpha=0.3)
        plt.subplots_adjust(top=0.95,bottom=0.0)
        plt.show()
        if savefolder:
            plt.savefig(os.path.join(savefolder, 'observations_'+x+'_'+y+'.pdf'))
            plt.close()

def plot_2d(all_data, xaxis, yaxis='freqs', normalized=False, savefolder=None):
    """2D plot of (position, frequency, brightness).

    If velocity information is available, the Y-axis shows velocity
    instead of frequency.

    Args:
        all_data: np.array containing a struct with at least 'freqs' and 'data' fields
        xaxis: name of field to use as xaxis
        yaxis: name ot field to use as yaxis ('freqs' or 'vels')
        normalized: whether to use polynomial fitting to remove background noise
        savefolder: string location to save plots, if specified
    """
    # TODO: Plot both frequency and velocity
    ydata = all_data[yaxis]
    ylabel = {
        'freqs': 'Frequency (%s)',
        'vels': 'Velocity (%s)',
    }[yaxis] % (all_data[yaxis].unit)
    xlabel = AXIS_NAMES.get(xaxis,xaxis)
    print('Plotting %s vs %s' % (xlabel, ylabel))
    if len(np.unique(all_data[xaxis])) == 1:
        # 2D plots require multiple points
        print('Skipped due to a single point')
        return
    @contextmanager
    def figure(name):
        fig = plt.figure()
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        yield fig
        if savefolder:
            plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_'+name+suffix+'.pdf'))
            plt.close()

    suffix = ('_'+normalized) if normalized else ''
    all_data = find_shift(all_data, xaxis)

    xdata = all_data[xaxis]
    # TODO: AstroPy 3+ can work on the Quantity instead of the array
    contour_data = all_data['data']
    # Some fields are scalar
    if xdata.shape != contour_data.shape:
        xdata = np.broadcast_to(xdata, reversed(contour_data.shape)).transpose()

    # Calculate reasonable bounds for the Z axis.
    # The minimum is selected as the median value in the background portion of the plot.
    # The maximum is the 95th percentile value across the whole plot.
    vmin = np.percentile(contour_data[:, CORRECTION_POLY_POINTS], 50)
    vmax = np.percentile(contour_data, 95)

    with figure('contour'):
        cntr = plt.contourf(xdata, ydata,
                            np.clip(
                                contour_data,
                                vmin, vmax),
                            100,
                            extend='both',
                            vmin=vmin, vmax=vmax)
        add_colorbar(cntr, contour_data.unit, normalized)

    norm = None

    with figure('mesh'):
        # pcolormesh without shading treats x and y as the
        # coordinates of the top left corner of the box.
        # So we need to shift the points up and to the left one half step so that the boxes are centered on the correct position.
        mesh_xdata = center_mesh_coords(xdata)
        mesh_ydata = center_mesh_coords(ydata)
        pcm = plt.pcolormesh(mesh_xdata, mesh_ydata, contour_data,
                             vmin=vmin, vmax=vmax,
                             norm=norm)
        add_colorbar(pcm, contour_data.unit, normalized)

    with figure('mesh_interpolated'):
        pcm = plt.pcolormesh(xdata, ydata, contour_data,
                             vmin=vmin, vmax=vmax,
                             shading='gouraud',
                             norm=norm)
        add_colorbar(pcm, contour_data.unit, normalized)

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

def normalize_data(all_data, visualize=False):
    """dsheen@'s polynomial fit algorithm

    This algorithm performs a first-order fit on noise information
    found in the first half of the spectrum for each position, then
    subtracts that estimated noise.

    If visualize is true, the estimated background noise will be plotted.

    The returned data represents the estimated observed signal power.
    """
    # Make a copy so we don't modify the original
    all_data = all_data.copy()

    points = CORRECTION_POLY_POINTS

    coefficients = polyfit(points, np.transpose(all_data['data'][:, points]), 1)

    correction_matrix = polyval(np.arange(all_data['data'].shape[1]), coefficients)

    if visualize: # visualize correction matrix
        plt.figure()
        pcm = plt.pcolormesh(correction_matrix)
        plt.colorbar(pcm, extend='max')
        plt.show()

    # To restore average background noise level: + np.median(coefficients[0])
    all_data['data'] -= correction_matrix
    return all_data

def average_data(all_data, keys, velocity_correction=True):
    """Average data with identical values for keys.

    Any columns other than {'freqs', 'vels'}+keys will be turned into (min,mean,max) values.

    Useful when --repeat is specified to gal_scan.
    """
    all_data = all_data.group_by(keys)
    groups = all_data.groups
    out_cols = []
    keep = set(groups.key_colnames) | {'mode', 'freqs', 'vels'}
    for col in all_data.columns.values():
        if col.info.name in keep:
            # Keep columns get passed through
            new_col = col[groups.indices[:-1]]
        elif col.info.name == 'data':
            # Data gets averaged (with optional velocity correction)
            if velocity_correction:
                data = [
                    average_point(group['data'], group['vels'])
                    for group in groups
                ]
                new_col = Column(name='data', data=data)
            else:
                new_col = col.groups.aggregate(np.mean)
        else:
            new_col = col.groups.aggregate(lambda x: (np.min(x), np.mean(x), np.max(x)))
        out_cols.append(new_col)
    out_cols.append(Column(name='count', data=groups.indices[1:]-groups.indices[:-1]))
    # Turn it back into a Table object
    return all_data.__class__(out_cols, meta=all_data.meta)

def average_point(scans, vels):
    """Average samples across a run.
    Takes in 2D data array and corresponding velocities.
    Aligns to correct for Doppler shift.
    Used for multiple observations of a single point.

    Returns:
           single-axis numpy array with average of data points
    """

    num_scans = scans.shape[0] #get number of scans
    num_samples = scans.shape[1] #get number of samples per scan

    vel_step = vels[0,0]-vels[0,1] #compute sample offset based on previously computed velocities
    differential_doppler_ratio= [(vels[0,0]/vels[i,0]) for i in range(num_scans)] #compute velocity shifts (this works correctly)

    sample_vel_offset = vels[:,0] #velocity of sample index zero
    sample_vel_slope = [(vels[i,(num_samples-1)] - vels[i,0])/num_samples for i in range(num_scans)]

    """

    backsolve for desired indices

    velocity values for first scan are given by vel[i,n] = sample_vel_offset[0] + n * sample_vel_slope[0]

    n = (vel - sample_vel_offset[i])/sample_vel_slope[i]

    """

    indices = np.zeros((2,num_scans,num_samples))
    for i in range(num_scans):
        for j in range(num_samples):
            indices[:,i,j] = [i, np.float128(vels[0,j] - sample_vel_offset[i])/np.float128(sample_vel_slope[i])]

    scans_shifted = ndimage.map_coordinates(scans, indices)

    return np.mean(scans_shifted, 0)

# .npy files can't store units; these are the units to apply when
# saving and loading data.
COLUMN_UNITS = {
    'freqs': u.MHz,
    'data': u.mW/u.Hz,
    'vels': u.km/u.s,
    'time': u.second,
    'azimuth': u.degree,
    'elevation': u.degree,
    'longitude': u.degree,
    'latitude': u.degree,
    'ra': u.degree,
    'dec': u.degree,
    'rci_azimuth': u.degree,
    'rci_elevation': u.degree,
}

# TODO: Switch to QTable when moving to AstroPy 3+ and Python 3+

def save_data(all_data, savefolder):
    """Save a Table to savefolder.

    Currently, this writes two files:
        - all_data.fits, compatible with astropy.table.Table.read
        - all_data.npy, compatible with np.load
    """
    for field, unit in COLUMN_UNITS.items():
        if field in all_data.columns:
            all_data[field] = all_data[field].to(unit).value
            all_data[field].unit = unit
    all_data.write(os.path.join(savefolder, 'all_data.fits'), overwrite=True)
    np.save(os.path.join(savefolder, 'all_data.npy'), all_data, allow_pickle=False)

def load_data():
    """Load existing data files.

    Returns:
        Table containg information about each observation
        Fields include:
        - 'number' contains the observation number
        - 'data' contains the raw data
        - 'freqs' contains the frequency for each sample
        - 'vels' contains relative velocity for each sample
        - 'time' contains the observation time
        - 'rci_azimuth' and 'rci_elevation' contain the actual azimuth and elevation for the observation
        - 'azimuth' and 'elevation' contain the commanded azimuth and elevation
        - 'longitude' and 'latitude' contain the Galactic coordinates
        - 'ra' and 'dec' contain the ICRS coordinates
        - 'darksky' indicates if the observation was a darksky correction (use 'number' to correlate darksky (False, True))
    """
    try:
        all_data = Table.read('all_data.fits')
        for field, unit in COLUMN_UNITS.items():
            if field in all_data.columns and not all_data[field].unit:
                all_data[field].unit = unit
        return all_data
    except IOError:
        # Revert to loading legacy data
        pass
    try:
        a = np.load('all_data.npy')
    except IOError:
        # Revert to loading legacy data
        axis_names = []
        axes = []
        contour_iter_axes = {}
        for name in glob.glob("contour_*.npy"):
            key = name.split('_', 1)[1].rsplit('.', 1)[0]
            axis_names.append(key)
            data = np.load(name)
            if key not in ('data', 'freqs', 'vels'):
                data = data[:,0]
            axes.append(data)
        dtype = [(x, axes[i].dtype, axes[i].shape[1:]) for i,x in enumerate(axis_names)]
        a = np.array([tuple(x) for x in zip(*axes)], dtype=dtype)
    all_data = Table(a)
    for field, unit in COLUMN_UNITS.items():
        if field in all_data.columns:
            all_data[field].unit = unit
    return all_data

def apply_darksky(all_data):
    """Apply darksky corrections.

    Returns:
        (uncorrected observations, corrected observations, darksky observations)
    """
    # Keep only observations that have a darksky calibration.
    all_data = all_data.group_by('number').groups.filter(lambda t, _: len(t) == 2)

    darksky_obs = all_data[all_data['darksky']]
    uncorrected_obs = all_data[~all_data['darksky']]
    corrected_obs = all_data.__class__(uncorrected_obs, meta=all_data.meta)
    corrected_obs['data'] -= darksky_obs['data']
    return uncorrected_obs, corrected_obs, darksky_obs

def recalculate_vels(all_data):
    """Replace the vels column with recalculated velocities"""

    import galcoord
    t = Time(all_data['time'].quantity.value, format='unix')
    sc = SkyCoord(l=all_data['longitude'].quantity, b=all_data['latitude'].quantity, obstime=t, location=galcoord.radome_observer.location, frame='galactic')
    all_data['vels'] = galcoord.freqs_to_vel(galcoord.HYDROGEN_FREQ, all_data['freqs'].quantity.T, sc).T
    return all_data

def main():
    # Invoke plot.py to replot an existing dataset
    parser = argparse.ArgumentParser(description='Replot existing data')
    parser.add_argument('--xaxes', nargs='*',
                        help='axes to plot')
    parser.add_argument('--yaxis',
                        help='yaxis to plot')
    #parser.add_argument('--outlier-percentile', metavar='PERCENT', type=float,
    #                    help='reject the first and last PERCENT runs as outliers')
    parser.add_argument('--max-pointing-error', metavar='DEGREES', type=float, default=2,
                        help='reject observations where abs(rci_azimuth-azimuth) > DEGREES')
    parser.add_argument('--recalculate-velocities', action='store_true',
                        help='recalculate velocities')
    args = parser.parse_args()

    savefolder = None
    if mpl.get_backend().lower() == 'agg':
        savefolder = '.'

    all_data = load_data()
    plot(all_data, savefolder=savefolder, **vars(args))

def structured_to_unstructured(a):
    """Backport of numpy.lib.recfunctions.structured_to_unstructured.

    Unlike the original, this function does not create a view on the original array.
    """
    return np.stack([a[f] for f in a.dtype.names], axis=1)

def plot(all_data, xaxes=None, yaxis=None, outlier_percentile=None, max_pointing_error=2, recalculate_velocities=False, savefolder=None):
    """Regenerate all default plots for all_data"""

    def path(name):
        if savefolder:
            return os.path.join(savefolder, name)
        return None

    fields = set(all_data.columns)

    if recalculate_velocities:
        all_data = recalculate_vels(all_data)

    # TODO: This could remove a measurement without its corresponding darksky measurement, or vice versa.
    if max_pointing_error and fields.issuperset(('azimuth', 'elevation', 'rci_azimuth', 'rci_elevation')):
        count = len(all_data)
        cmd_pos = structured_to_unstructured(all_data[['azimuth', 'elevation']])
        obs_pos = structured_to_unstructured(all_data[['rci_azimuth', 'rci_elevation']])
        all_data['bad'] = np.linalg.norm(cmd_pos-obs_pos, axis=1) < max_pointing_error

        # TODO: Just leave the bad rows in all_data and have normalize_data filter them out?
        bad_data = all_data[~all_data['bad']]
        all_data = all_data[all_data['bad']]
        if len(all_data) != count:
            print("Removed %d of %d points with pointing error > %f°" % (count-len(all_data), count, max_pointing_error))

    has_darksky = 'darksky' in fields
    if has_darksky:
        raw_data, calibrated_data, darksky_obs = apply_darksky(all_data)
        # plot average darksky_obs
        plot_freq(None, darksky_obs['freqs'].quantity[0], np.mean(darksky_obs['data'].quantity, axis=0), 'Average Darksky Measurement', path('darksky.pdf'))
    else:
        raw_data = all_data

    if not xaxes:
        all_axes = set(all_data.columns)
        xaxes = all_axes - set('freqs vels data'.split())
        if 'mode' in all_data.columns:
            mode = all_data['mode'][0]
            if mode == 'az':
                xaxes = 'number azimuth rci_azimuth'.split()
            elif mode == 'gal':
                xaxes = 'number rci_azimuth longitude'.split()
            elif mode == 'grid':
                xaxes = 'number rci_azimuth longitude latitude'.split()
        xaxes = all_axes & set(xaxes)
    print("Plotting axes:", xaxes)

    if not yaxis:
        yaxis = 'freqs'
        if 'vels' in all_data.columns:
            yaxis = 'vels'

    if not has_darksky:
        normalized_data = normalize_data(raw_data)

    def plot_averaged(data, suffix=''):
        for i, row in enumerate(data):
            # TODO: Fix this when we switch to QTable
            plot_velocity(data['vels'].quantity[i], data['data'].quantity[i], '%s=%s (n=%s)' % (xaxis, row[xaxis], row['count']), path('%s_%s_averaged%s.pdf' % (xaxis, row[xaxis], suffix)))

    for xaxis in xaxes:
        averaged_data = average_data(raw_data, [xaxis])
        plot_averaged(averaged_data)

        plot_2d(raw_data, xaxis, yaxis, savefolder=savefolder)
        if has_darksky:
            averaged_data = average_data(calibrated_data, [xaxis])
            plot_averaged(averaged_data, '_calibrated')
            plot_2d(calibrated_data, xaxis, yaxis, normalized='calibrated', savefolder=savefolder)
        else:
            averaged_data = average_data(normalized_data, [xaxis])
            plot_averaged(averaged_data, '_normalized')
            plot_2d(normalized_data, xaxis, yaxis, normalized='normalized', savefolder=savefolder)
    plot_observations(all_data, bad_data, savefolder=savefolder)

if __name__ == '__main__':
    main()
    plt.show()
