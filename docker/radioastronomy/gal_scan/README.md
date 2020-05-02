# Galactic Sky Scan

`gal_scan` is a radioastronomy tool that measures the Doppler shift of
the [Hydrogen emissions](https://en.wikipedia.org/wiki/H_I_region)
from our galaxy, producing a plot of the [Galactic Rotation
Curve](https://www.haystack.mit.edu/edu/undergrad/srt/SRT%20Projects/rotation.html). It
can also be used to quantify terrestrial interference and measure
emissions from other galaxies.

## Installation

See INSTALL.md for compilation instructions, if necessary. `gal_scan`
requires GNU Radio, astropy, astroplan, numpy, and matplotlib.

## Running

`gal_scan` is typically invoked as a Docker container. At MIT, we
launch the Docker container using a wrapper script that attaches the
correct radio and dish control hardware. A sample invocation of
`gal_scan` looks like:

```
grrun -t w1xm/radioastronomy/gal_scan /flowgraph/run.py --step=2.5 --int-time=60 run_quentin_20200326/
```

### Galactic scan mode

By default, `gal_scan` will trace a line across the sky (galactic
latitude 0) from one horizon to the other. The most important
parameters are `--step`, which specifies the step size in degrees, and
`--int-time`, which specifies the integration time. Decreasing the
step size and increasing the integration time will produce
higher-resolution output at the cost of a longer observing run.

While the scan is running, you can watch the output in your terminal
and follow the antenna status at <http://w1xm-radar-1.mit.edu:8502/>.

### Terrestrial noise scan mode

With `--mode=az`, `gal_scan` will instead trace a line across the
horizon at zero elevation. As with `--mode=gal`, the most important
parameters are `--step` and `--int-time`.

### Grid scan mode

With `--mode=grid`, `gal_scan` will survey a grid around a particular
galactic latitude and longitude. For example, to survey a 10°x10° grid
around Andromeda, `gal_scan` can be invoked as:

```
grrun -t w1xm/radioastronomy/gal_scan /flowgraph/run.py --start=-5 --step=1 --stop=5 --mode=grid --lat=-21.5729360 --lon=121.1744050 --int-time=60 ~/quentin/andromeda_202005021248
```

In this mode, `--start` and `--stop` are interpreted as offsets from
the central (latitude, longitude). Ensure that you carefully choose
the step size and integration time: a 10x10 grid such as the one above
will take 100 observations, which at an integration time of 60 seconds
will take almost two hours.

## Output

`gal_scan` produces multiple data files and plots in the specified
output directory. For each observing position, there will be two plots
showing average brightness of the Hydrogen line on the Y axis. In the
`freq` plot, the X axis is the frequency at which the emissions were
measured. In the `vel` plot, the frequency is converted to the
equivalent relative velocity.

A 2D plot is also produced showing the brightness and velocity across
the whole galactic disc in `2d_longitude_mesh_normalized.pdf`.

The raw data is saved as a CSV file named `vectors.csv` as well as
multiple Numpy files named `contour_data.npy`, `contour_freqs.npy`,
etc.

### Replotting

All of the plotting code using Numpy and Matplotlib live in
`plot.py`. Plots can easily be regenerated, using any changes you may
have made to `plot.py`, by running `plot.py` in the directory
containing the `*.npy` files:

```
run_20200415$ ../path/to/plot.py
```

Unlike `run.py`, `plot.py` does not require talking to radio and dish
control hardware, so it can be run from a local checkout on your
machine.

In addition, instead of generating PDF files, these plots can be
interactively viewed by running `plot.py` inside
[IPython](https://ipython.org/):

```
run_20200415$ ipython --pylab
In [1]: %run ../plot.py
```

### Manual data analysis and plotting

The data files can also be loaded into a Numpy session and plotted
with varying parameters:

```Python
import matplotlib.pyplot as plt
import matplotlib.colors
import numpy as np

contour_vels = np.load('contour_vels.npy')
contour_longs = np.load('contour_longitude.npy')
contour_data = np.load('contour_data.npy')

plt.figure()
plt.xlabel('Velocity (km/s)')
plt.ylabel('Galactic Longitude')
plt.ticklabel_format(useOffset=False)
pcm = plt.pcolormesh(contour_longs, contour_vels, contour_data, vmin=0.8e-16, vmax=np.percentile(contour_data, 90), shading='gouraud', norm=matplotlib.colors.LogNorm())
cbar = plt.colorbar(pcm, extend='max')
cbar.ax.set_ylabel('Power at feed (W/Hz)', rotation=-90, va="bottom")
plt.show()
```

It is convenient to run these commands in an interactive Python prompt
so the plotting parameters can be tweaked. Such an environment with
imports already done for you can be obtained with `ipython --pylab`.

## Advanced options

The full parameters that `gal_scan` supports are listed below:

```
usage: run.py [-h] [--int-time INT_TIME] [--gain GAIN] [--mode {az,gal,grid}]
              [--step STEP] [--start START] [--stop STOP] [--lat LAT]
              [--lon LON]
              DIRECTORY

Galactic sky scan

positional arguments:
  DIRECTORY             output directory to write scan results

optional arguments:
  -h, --help            show this help message and exit
  --int-time INT_TIME   integration time
  --gain GAIN           SDR gain
  --mode {az,gal,grid}
  --step STEP           position step size
  --start START         starting position
  --stop STOP           ending position
  --lat LAT             galactic latitude to scan (for grid mode)
  --lon LON             galactic longitude to scan (for grid mode)
```

`--start` and `--stop` can be used to limit the scan to a portion of
the sky. `--gain` can be used to increase or decrease the SDR's gain
(sensitivity). `--mode az` can be used to measure terrestrial noise
sources; instead of plotting a line across galactic latitude 0, it
plots a line across elevation 0. `--mode grid` can be used to measure
around a particular coordinate.
