To build `gal_scan` as a Docker container, just run `make` in the
source directory. To build it by hand, install the dependencies:

```
sudo apt install gnuradio python-matplotlib python-astropy python-astroplan
```

and build the flowgraph:

```
grcc -d . flowgraph.grc
```
