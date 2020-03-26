# Galactic Sky Scan

`gal_scan` is a radioastronomy tool that measures the Doppler shift of
the [Hydrogen emissions](https://en.wikipedia.org/wiki/H_I_region)
from our galaxy, producing a plot of the [Galactic Rotation
Curve](https://www.haystack.mit.edu/edu/undergrad/srt/SRT%20Projects/rotation.html).

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

By default, `gal_scan` will trace a line across the sky (galactic
latitude 0) from one horizon to the other. The most important
parameters are `--step`, which specifies the step size in degrees, and
`--int-time`, which specifies the integration time. Decreasing the
step size and increasing the integration time will produce
higher-resolution output at the cost of a longer observing run.

While the scan is running, you can watch the output in your terminal
and follow the antenna status at <http://w1xm-radar-1.mit.edu:8502/>.

## Output

`gal_scan` produces multiple data files and plots in the specified
output directory. For each observing position, there will be two plots
showing average brightness of the Hydrogen line on the Y axis. In the
`freq` plot, the X axis is the frequency at which the emissions were
measured. In the `vel` plot, the frequency is converted to the
equivalent relative velocity.

A 2D plot is also produced showing the brightness and velocity across
the whole galactic disc in `2d_longitude_mesh.pdf`.

The raw data is saved as a CSV file named `vectors.csv` as well as
multiple Numpy files named `contour_data.npy`, `contour_freqs.npy`,
etc. These files can be loaded into a numpy session and plotted with varying parameters:

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
usage: run.py [-h] [--int-time INT_TIME] [--gain GAIN] [--mode {az,gal}]
              [--step STEP] [--start START] [--stop STOP]
              DIRECTORY

Galactic sky scan

positional arguments:
  DIRECTORY            output directory to write scan results

optional arguments:
  -h, --help           show this help message and exit
  --int-time INT_TIME  integration time
  --gain GAIN          SDR gain
  --mode {az,gal}
  --step STEP          position step size
  --start START        starting position
  --stop STOP          ending position
```

`--start` and `--stop` can be used to limit the scan to a portion of
the sky. `--gain` can be used to increase or decrease the SDR's gain
(sensitivity). `--mode az` can be used to measure terrestrial noise
sources; instead of plotting a line across galactic latitude 0, it
plots a line across elevation 0.
