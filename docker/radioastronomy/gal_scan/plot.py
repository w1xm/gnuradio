#!/usr/bin/env python3
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
from astropy.coordinates import Angle, Latitude, Longitude, SkyCoord
from astropy.table import QTable, Column, ColumnGroups
from astropy.time import Time
from astropy.io import fits
from scipy import ndimage
from scipy.interpolate import griddata
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
    if freq is not None:
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
    if not axis_data.unit or not axis_data.unit.is_equivalent(u.degree) or isinstance(axis_data, Latitude):
        return all_data
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
        if isinstance(axis_data, Longitude):
            all_data[axis] = axis_data.wrap_at(axis_data[gap_index]-(gap/2))
        else:
            all_data[axis][gap_index:] -= 360*u.degree
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

GQRX_CMAP = colors.LinearSegmentedColormap.from_list(
    'gqrx', [
        (0, (0,0,0)),
        (20/256, (0,0,0)),
        (70/256, (0, 0, 140/255)),
        (100/256, (60/255, 125/255, 1)),
        (150/256, (1, 1, 0)),
        (250/256, (1, 0, 0)),
        (1, (1, 1, 1))
    ])

# https://ai.googleblog.com/2019/08/turbo-improved-rainbow-colormap-for.html
TURBO_CMAP = colors.ListedColormap(
    [[0.18995,0.07176,0.23217],[0.19483,0.08339,0.26149],[0.19956,0.09498,0.29024],[0.20415,0.10652,0.31844],[0.20860,0.11802,0.34607],[0.21291,0.12947,0.37314],[0.21708,0.14087,0.39964],[0.22111,0.15223,0.42558],[0.22500,0.16354,0.45096],[0.22875,0.17481,0.47578],[0.23236,0.18603,0.50004],[0.23582,0.19720,0.52373],[0.23915,0.20833,0.54686],[0.24234,0.21941,0.56942],[0.24539,0.23044,0.59142],[0.24830,0.24143,0.61286],[0.25107,0.25237,0.63374],[0.25369,0.26327,0.65406],[0.25618,0.27412,0.67381],[0.25853,0.28492,0.69300],[0.26074,0.29568,0.71162],[0.26280,0.30639,0.72968],[0.26473,0.31706,0.74718],[0.26652,0.32768,0.76412],[0.26816,0.33825,0.78050],[0.26967,0.34878,0.79631],[0.27103,0.35926,0.81156],[0.27226,0.36970,0.82624],[0.27334,0.38008,0.84037],[0.27429,0.39043,0.85393],[0.27509,0.40072,0.86692],[0.27576,0.41097,0.87936],[0.27628,0.42118,0.89123],[0.27667,0.43134,0.90254],[0.27691,0.44145,0.91328],[0.27701,0.45152,0.92347],[0.27698,0.46153,0.93309],[0.27680,0.47151,0.94214],[0.27648,0.48144,0.95064],[0.27603,0.49132,0.95857],[0.27543,0.50115,0.96594],[0.27469,0.51094,0.97275],[0.27381,0.52069,0.97899],[0.27273,0.53040,0.98461],[0.27106,0.54015,0.98930],[0.26878,0.54995,0.99303],[0.26592,0.55979,0.99583],[0.26252,0.56967,0.99773],[0.25862,0.57958,0.99876],[0.25425,0.58950,0.99896],[0.24946,0.59943,0.99835],[0.24427,0.60937,0.99697],[0.23874,0.61931,0.99485],[0.23288,0.62923,0.99202],[0.22676,0.63913,0.98851],[0.22039,0.64901,0.98436],[0.21382,0.65886,0.97959],[0.20708,0.66866,0.97423],[0.20021,0.67842,0.96833],[0.19326,0.68812,0.96190],[0.18625,0.69775,0.95498],[0.17923,0.70732,0.94761],[0.17223,0.71680,0.93981],[0.16529,0.72620,0.93161],[0.15844,0.73551,0.92305],[0.15173,0.74472,0.91416],[0.14519,0.75381,0.90496],[0.13886,0.76279,0.89550],[0.13278,0.77165,0.88580],[0.12698,0.78037,0.87590],[0.12151,0.78896,0.86581],[0.11639,0.79740,0.85559],[0.11167,0.80569,0.84525],[0.10738,0.81381,0.83484],[0.10357,0.82177,0.82437],[0.10026,0.82955,0.81389],[0.09750,0.83714,0.80342],[0.09532,0.84455,0.79299],[0.09377,0.85175,0.78264],[0.09287,0.85875,0.77240],[0.09267,0.86554,0.76230],[0.09320,0.87211,0.75237],[0.09451,0.87844,0.74265],[0.09662,0.88454,0.73316],[0.09958,0.89040,0.72393],[0.10342,0.89600,0.71500],[0.10815,0.90142,0.70599],[0.11374,0.90673,0.69651],[0.12014,0.91193,0.68660],[0.12733,0.91701,0.67627],[0.13526,0.92197,0.66556],[0.14391,0.92680,0.65448],[0.15323,0.93151,0.64308],[0.16319,0.93609,0.63137],[0.17377,0.94053,0.61938],[0.18491,0.94484,0.60713],[0.19659,0.94901,0.59466],[0.20877,0.95304,0.58199],[0.22142,0.95692,0.56914],[0.23449,0.96065,0.55614],[0.24797,0.96423,0.54303],[0.26180,0.96765,0.52981],[0.27597,0.97092,0.51653],[0.29042,0.97403,0.50321],[0.30513,0.97697,0.48987],[0.32006,0.97974,0.47654],[0.33517,0.98234,0.46325],[0.35043,0.98477,0.45002],[0.36581,0.98702,0.43688],[0.38127,0.98909,0.42386],[0.39678,0.99098,0.41098],[0.41229,0.99268,0.39826],[0.42778,0.99419,0.38575],[0.44321,0.99551,0.37345],[0.45854,0.99663,0.36140],[0.47375,0.99755,0.34963],[0.48879,0.99828,0.33816],[0.50362,0.99879,0.32701],[0.51822,0.99910,0.31622],[0.53255,0.99919,0.30581],[0.54658,0.99907,0.29581],[0.56026,0.99873,0.28623],[0.57357,0.99817,0.27712],[0.58646,0.99739,0.26849],[0.59891,0.99638,0.26038],[0.61088,0.99514,0.25280],[0.62233,0.99366,0.24579],[0.63323,0.99195,0.23937],[0.64362,0.98999,0.23356],[0.65394,0.98775,0.22835],[0.66428,0.98524,0.22370],[0.67462,0.98246,0.21960],[0.68494,0.97941,0.21602],[0.69525,0.97610,0.21294],[0.70553,0.97255,0.21032],[0.71577,0.96875,0.20815],[0.72596,0.96470,0.20640],[0.73610,0.96043,0.20504],[0.74617,0.95593,0.20406],[0.75617,0.95121,0.20343],[0.76608,0.94627,0.20311],[0.77591,0.94113,0.20310],[0.78563,0.93579,0.20336],[0.79524,0.93025,0.20386],[0.80473,0.92452,0.20459],[0.81410,0.91861,0.20552],[0.82333,0.91253,0.20663],[0.83241,0.90627,0.20788],[0.84133,0.89986,0.20926],[0.85010,0.89328,0.21074],[0.85868,0.88655,0.21230],[0.86709,0.87968,0.21391],[0.87530,0.87267,0.21555],[0.88331,0.86553,0.21719],[0.89112,0.85826,0.21880],[0.89870,0.85087,0.22038],[0.90605,0.84337,0.22188],[0.91317,0.83576,0.22328],[0.92004,0.82806,0.22456],[0.92666,0.82025,0.22570],[0.93301,0.81236,0.22667],[0.93909,0.80439,0.22744],[0.94489,0.79634,0.22800],[0.95039,0.78823,0.22831],[0.95560,0.78005,0.22836],[0.96049,0.77181,0.22811],[0.96507,0.76352,0.22754],[0.96931,0.75519,0.22663],[0.97323,0.74682,0.22536],[0.97679,0.73842,0.22369],[0.98000,0.73000,0.22161],[0.98289,0.72140,0.21918],[0.98549,0.71250,0.21650],[0.98781,0.70330,0.21358],[0.98986,0.69382,0.21043],[0.99163,0.68408,0.20706],[0.99314,0.67408,0.20348],[0.99438,0.66386,0.19971],[0.99535,0.65341,0.19577],[0.99607,0.64277,0.19165],[0.99654,0.63193,0.18738],[0.99675,0.62093,0.18297],[0.99672,0.60977,0.17842],[0.99644,0.59846,0.17376],[0.99593,0.58703,0.16899],[0.99517,0.57549,0.16412],[0.99419,0.56386,0.15918],[0.99297,0.55214,0.15417],[0.99153,0.54036,0.14910],[0.98987,0.52854,0.14398],[0.98799,0.51667,0.13883],[0.98590,0.50479,0.13367],[0.98360,0.49291,0.12849],[0.98108,0.48104,0.12332],[0.97837,0.46920,0.11817],[0.97545,0.45740,0.11305],[0.97234,0.44565,0.10797],[0.96904,0.43399,0.10294],[0.96555,0.42241,0.09798],[0.96187,0.41093,0.09310],[0.95801,0.39958,0.08831],[0.95398,0.38836,0.08362],[0.94977,0.37729,0.07905],[0.94538,0.36638,0.07461],[0.94084,0.35566,0.07031],[0.93612,0.34513,0.06616],[0.93125,0.33482,0.06218],[0.92623,0.32473,0.05837],[0.92105,0.31489,0.05475],[0.91572,0.30530,0.05134],[0.91024,0.29599,0.04814],[0.90463,0.28696,0.04516],[0.89888,0.27824,0.04243],[0.89298,0.26981,0.03993],[0.88691,0.26152,0.03753],[0.88066,0.25334,0.03521],[0.87422,0.24526,0.03297],[0.86760,0.23730,0.03082],[0.86079,0.22945,0.02875],[0.85380,0.22170,0.02677],[0.84662,0.21407,0.02487],[0.83926,0.20654,0.02305],[0.83172,0.19912,0.02131],[0.82399,0.19182,0.01966],[0.81608,0.18462,0.01809],[0.80799,0.17753,0.01660],[0.79971,0.17055,0.01520],[0.79125,0.16368,0.01387],[0.78260,0.15693,0.01264],[0.77377,0.15028,0.01148],[0.76476,0.14374,0.01041],[0.75556,0.13731,0.00942],[0.74617,0.13098,0.00851],[0.73661,0.12477,0.00769],[0.72686,0.11867,0.00695],[0.71692,0.11268,0.00629],[0.70680,0.10680,0.00571],[0.69650,0.10102,0.00522],[0.68602,0.09536,0.00481],[0.67535,0.08980,0.00449],[0.66449,0.08436,0.00424],[0.65345,0.07902,0.00408],[0.64223,0.07380,0.00401],[0.63082,0.06868,0.00401],[0.61923,0.06367,0.00410],[0.60746,0.05878,0.00427],[0.59550,0.05399,0.00453],[0.58336,0.04931,0.00486],[0.57103,0.04474,0.00529],[0.55852,0.04028,0.00579],[0.54583,0.03593,0.00638],[0.53295,0.03169,0.00705],[0.51989,0.02756,0.00780],[0.50664,0.02354,0.00863],[0.49321,0.01963,0.00955],[0.47960,0.01583,0.01055]]
)

def plot_2d(all_data, xaxis, yaxis='freqs', normalized=False, cmap=TURBO_CMAP, savefolder=None):
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
    ylabel = {
        'freqs': 'Frequency (%s)',
        'vels': 'Velocity (%s)',
    }[yaxis] % (all_data[yaxis].unit)
    xlabel = AXIS_NAMES.get(xaxis,xaxis)
    print('Plotting %s%s vs %s' % ((normalized+' ' if normalized else ''), xlabel, ylabel))
    if len(np.unique(all_data[xaxis])) == 1:
        # 2D plots require multiple points
        print('Skipped due to a single point')
        return
    @contextmanager
    def figure(name):
        figsize = plt.figaspect(.5)
        fig = plt.figure(figsize=figsize)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ticklabel_format(useOffset=False)
        yield fig
        if savefolder:
            plt.savefig(os.path.join(savefolder, '2d_'+xaxis+'_'+name+suffix+'.png'), bbox_inches='tight')
            plt.close()

    suffix = ('_'+normalized) if normalized else ''
    all_data = find_shift(all_data, xaxis)

    xdata = all_data[xaxis]
    ydata = all_data[yaxis]

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
                            vmin=vmin.value, vmax=vmax.value,
                            cmap=cmap)
        add_colorbar(cntr, contour_data.unit, normalized)

    norm = None

    with figure('mesh'):
        # pcolormesh without shading treats x and y as the
        # coordinates of the top left corner of the box.
        # So we need to shift the points up and to the left one half step so that the boxes are centered on the correct position.
        mesh_xdata = center_mesh_coords(xdata)
        mesh_ydata = center_mesh_coords(ydata)
        pcm = plt.pcolormesh(mesh_xdata, mesh_ydata, contour_data,
                             vmin=vmin.value, vmax=vmax.value,
                             norm=norm, cmap=cmap)
        add_colorbar(pcm, contour_data.unit, normalized)

    with figure('mesh_interpolated'):
        pcm = plt.pcolormesh(xdata, ydata, contour_data,
                             vmin=vmin.value, vmax=vmax.value,
                             shading='gouraud',
                             norm=norm, cmap=cmap)
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
    correction_matrix = u.Quantity(correction_matrix, unit=all_data['data'].unit)

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
    i0s, i1s = groups.indices[:-1], groups.indices[1:]
    out_cols = []
    keep = set(groups.key_colnames) | {'mode', 'freqs', 'vels', 'body_name'}
    for col in all_data.columns.values():
        if col.info.name in keep:
            # Keep columns get passed through
            new_col = col[i0s]
        elif col.info.name == 'data':
            # Data gets averaged (with optional velocity correction)
            if velocity_correction and 'vels' in all_data.columns:
                data = np.vstack(tuple(
                    average_point(group['data'], group['vels'])
                    for group in groups
                ))
                new_col = Column(name='data', data=data)
            else:
                new_col = Column(
                    name='data',
                    data=(np.add.reduceat(
                        all_data['data'],
                        i0s,
                    ).T/np.diff(groups.indices)).T
                )
        else:
            minmax = np.stack(
                [ufunc.reduceat(col, i0s, axis=0)
                 for ufunc in (np.fmin, np.fmax)],
                axis=-1,
            )
            new_col = Column(
                name=col.info.name,
                data=minmax)
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

    return u.Quantity(np.mean(scans_shifted, 0), unit=scans.unit)

# .npy files can't store units; these are the units to apply when
# saving and loading data.
COLUMN_UNITS = {
    'gain': u.dB,
    'freqs': u.MHz,
    'data': u.mW/u.Hz,
    'vels': u.km/u.s,
    'azimuth': u.degree,
    'elevation': u.degree,
    'longitude': u.degree,
    'latitude': u.degree,
    'ra': u.degree,
    'dec': u.degree,
    'rci_azimuth': u.degree,
    'rci_elevation': u.degree,
}

def save_data(all_data, savefolder):
    """Save a Table to savefolder.

    Currently, this writes two files:
        - all_data.fits, compatible with astropy.table.Table.read
        - all_data.npy, compatible with np.load
    """
    for field, unit in COLUMN_UNITS.items():
        if field in all_data.columns:
            all_data[field] = all_data[field].to(unit)
    all_data.write(os.path.join(savefolder, 'all_data.fits'), overwrite=True)
    all_data = all_data.copy()
    # Turn 'time' into a unix timestamp, since np.save would otherwise pickle it.
    all_data['time'] = all_data['time'].value
    all_data['time'].unit = u.second
    np.save(os.path.join(savefolder, 'all_data.npy'), all_data, allow_pickle=False)

def load_data(savefolder='.'):
    """Load existing data files.

    Returns:
        QTable containg information about each observation
        Fields include:
        - 'number' contains the observation number
        - 'data' contains the raw data
        - 'freqs' contains the frequency for each sample
        - 'vels' contains relative velocity for each sample
        - 'time' contains the observation time as a Time object
        - 'rci_azimuth' and 'rci_elevation' contain the actual azimuth and elevation for the observation
        - 'azimuth' and 'elevation' contain the commanded azimuth and elevation
        - 'longitude' and 'latitude' contain the Galactic coordinates
        - 'ra' and 'dec' contain the ICRS coordinates
        - 'darksky' indicates if the observation was a darksky correction (use 'number' to correlate darksky (False, True))
    """
    try:
        all_data = QTable.read(os.path.join(savefolder, 'all_data.fits'))
        for field, unit in COLUMN_UNITS.items():
            if field in all_data.columns and not all_data[field].unit:
                all_data[field].unit = unit
        if not isinstance(all_data['time'], Time):
            # Old FITS files are not marked as times.
            all_data['time'] = Time(all_data['time'].value, format='unix')
        for column in all_data.columns.values():
            # I have no idea why this is necessary but sometimes this attribute is None :(
            column.info.indices = []
        return all_data
    except IOError:
        # Revert to loading legacy data
        pass
    try:
        a = np.load(os.path.join(savefolder, 'all_data.npy'))
    except IOError:
        # Revert to loading legacy data
        axis_names = []
        axes = []
        contour_iter_axes = {}
        for name in glob.glob(os.path.join(savefolder, "contour_*.npy")):
            key = name.split('_', 1)[1].rsplit('.', 1)[0]
            axis_names.append(key)
            data = np.load(name)
            if key not in ('data', 'freqs', 'vels'):
                data = data[:,0]
            axes.append(data)
        dtype = [(x, axes[i].dtype, axes[i].shape[1:]) for i,x in enumerate(axis_names)]
        a = np.array([tuple(x) for x in zip(*axes)], dtype=dtype)
    all_data = QTable(a)
    if 'time' in all_data.colnames:
        all_data['time'] = Time(all_data['time'], format='unix')
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
    sc = SkyCoord(l=all_data['longitude'], b=all_data['latitude'], obstime=all_data['time'], location=galcoord.radome_observer.location, frame='galactic')
    all_data['vels'] = galcoord.freqs_to_vel(galcoord.HYDROGEN_FREQ, all_data['freqs'].T, sc).T
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
    parser.add_argument('--max-pointing-error', metavar='DEGREES', type=Angle, default=2*u.degree,
                        help='reject observations where abs(rci_azimuth-azimuth) > DEGREES')
    parser.add_argument('--recalculate-velocities', action='store_true',
                        help='recalculate velocities')
    parser.add_argument('--skip-1d', action='store_true',
                        help='skip generating 1D plots')
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

def remove_pointing_error(all_data, max_pointing_error):
    if max_pointing_error is not None and set(all_data.colnames).issuperset(('azimuth', 'elevation', 'rci_azimuth', 'rci_elevation')):
        count = len(all_data)
        cmd_pos = u.Quantity(structured_to_unstructured(all_data[['azimuth', 'elevation']]))
        cmd_pos[cmd_pos[:,1] > 180*u.degree, 1] -= 360*u.degree
        obs_pos = structured_to_unstructured(all_data[['rci_azimuth', 'rci_elevation']])
        obs_pos[obs_pos[:,1] > 180*u.degree, 1] -= 360*u.degree
        all_data['bad'] = np.linalg.norm(cmd_pos-obs_pos, axis=1) < max_pointing_error

        # TODO: Just leave the bad rows in all_data and have normalize_data filter them out?
        bad_data = all_data[~all_data['bad']]
        all_data = all_data[all_data['bad']]
        if len(all_data) != count:
            print("Removed %d of %d points with pointing error > %f°" % (count-len(all_data), count, max_pointing_error.to_value(u.degree)))
        return all_data, bad_data
    return all_data, all_data[0:0]

def plot_interference(all_data, filename=None):
    """Plot a view of interference across the run.

    Requires that all_data contain a 'max_interference' column; this can be generated as

    all_data['max_interference'] = np.fmax.reduce(all_data['data'], axis=1)
    """
    t = mpl.dates.date2num(all_data['time'].replicate('datetime').value)#.replicate('mjd')
    fig, ax1 = plt.subplots()
    fig.subplots_adjust(right=0.8)
    p1, = ax1.plot_date(t, all_data['max_interference'], 'k-', label='Interference', lw=0.5)
    ax1.set_ylabel('Interference (%s)' % (all_data['max_interference'].unit))
    ax2 = ax1.twinx()
    p2, = ax2.plot_date(t, all_data['rci_azimuth'], 'c-', label='Azimuth', lw=0.5)
    ax2.set_ylabel('Azimuth (%s)' % (all_data['rci_azimuth'].unit))
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('axes', 1.1))
    p3, = ax3.plot_date(t, all_data['rci_elevation'], 'm-', label='Elevation', lw=0.5)
    ax3.set_ylabel('Elevation (%s)' % (all_data['rci_elevation'].unit))
    ax2.tick_params(axis='y', colors=p2.get_color())
    ax3.tick_params(axis='y', colors=p3.get_color())
    fig.autofmt_xdate()
    if filename:
        plt.savefig(filename)
        plt.close()

def project_image(all_data, xaxis):
    """Project an image from all_data into a FITS PrimaryHDU image.

    This image can be written to disk with hdu.writeto("image.fits")
    and viewed with industry-standard viewers.

    """
    all_data = find_shift(all_data, xaxis)
    xmin, xmax, xstep = np.min(all_data[xaxis]), np.max(all_data[xaxis]), 1*u.degree
    ymin, ymax, ystep = np.min(all_data['vels']), np.max(all_data['vels']), np.abs(all_data['vels'][0,1]-all_data['vels'][0,0])

    grid = np.mgrid[
        ymin:ymax:ystep,
        xmin:xmax:xstep
    ]

    points = np.stack(
        [
            np.broadcast_to(
                all_data[xaxis].value,
                all_data['vels'].T.shape).T.flatten(),
            all_data['vels'].value.flatten()
        ]
    )

    proj = griddata((points[0], points[1]), all_data['data'].value.flatten(), (grid[1], grid[0]), method='linear')

    fu = lambda unit: u.format.Fits().to_string(unit)

    header = fits.Header()
    header['BUNIT'] = fu(all_data['data'].unit)
    header['CTYPE1'] = fu(all_data[xaxis].unit)
    header['CRPIX1'] = 1
    header['CRVAL1'] = xmin.value
    header['CDELT1'] = xstep.value
    header['CROTA1'] = 0
    header['CTYPE2'] = fu(all_data['vels'].unit)
    header['CRPIX2'] = 1
    header['CRVAL2'] = ymin.value
    header['CDELT2'] = ystep.value
    header['CROTA2'] = 0
    return fits.PrimaryHDU(proj, header)

def plot(all_data, xaxes=None, yaxis=None, skip_1d=False, outlier_percentile=None, max_pointing_error=2*u.degree, recalculate_velocities=False, savefolder=None):
    """Regenerate all default plots for all_data"""

    def path(name):
        if savefolder:
            return os.path.join(savefolder, name)
        return None

    fields = set(all_data.columns)

    if recalculate_velocities:
        all_data = recalculate_vels(all_data)

    all_data, bad_data = remove_pointing_error(all_data, max_pointing_error)

    has_darksky = 'darksky' in fields
    if has_darksky:
        print('Applying darksky calibrations')
        raw_data, calibrated_data, darksky_obs = apply_darksky(all_data)
        # plot average darksky_obs
        plot_freq(None, darksky_obs[0]['freqs'], np.mean(darksky_obs['data'], axis=0), 'Average Darksky Measurement', path('darksky.pdf'))
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
            elif mode == 'solar_grid':
                xaxes = 'number skyoffset_latitude skyoffset_longitude'.split()
        xaxes = all_axes & set(xaxes)
    print("Plotting axes:", xaxes)

    if not yaxis:
        yaxis = 'freqs'
        if 'vels' in all_data.columns:
            yaxis = 'vels'

    if not has_darksky:
        normalized_data = normalize_data(raw_data)

    def plot_averaged(data, suffix=''):
        if not skip_1d:
            for row in data:
                if yaxis == 'vels':
                    plot_velocity(row['vels'],
                                  row['data'],
                                  '%s=%s (n=%s)' % (xaxis, row[xaxis], row['count']),
                                  path('%s_%s_averaged%s.pdf' % (xaxis, row[xaxis], suffix)))
                else:
                    plot_freq(None,
                              row['freqs'],
                              row['data'],
                              '%s=%s (n=%s)' % (xaxis, row[xaxis], row['count']),
                              path('%s_%s_averaged%s.pdf' % (xaxis, row[xaxis], suffix)))


    for xaxis in xaxes:
        averaged_data = average_data(find_shift(raw_data, xaxis), [xaxis])
        print("Plotting 1D averaged %s" % (xaxis,))
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
