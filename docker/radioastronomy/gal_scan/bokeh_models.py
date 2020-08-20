from bokeh.core.properties import Angle, Tuple
from bokeh.io import show
from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.util.compiler import TypeScript

class Skymap(LayoutDOM):
    __implementation__ = "skymap.ts"
    __javascript__ = [
        "https://slowe.github.io/VirtualSky/stuquery.min.js",
        "https://slowe.github.io/VirtualSky/virtualsky.min.js",
    ]

    # Below are all the "properties" for this model. Bokeh properties are
    # class attributes that define the fields (and their types) that can be
    # communicated automatically between Python and the browser. Properties
    # also support type validation. More information about properties in
    # can be found here:
    #
    #    https://docs.bokeh.org/en/latest/docs/reference/core/properties.html#bokeh-core-properties

    latlon = Tuple(Angle, Angle)

    azel = Tuple(Angle, Angle)
    targetAzel = Tuple(Angle, Angle)
