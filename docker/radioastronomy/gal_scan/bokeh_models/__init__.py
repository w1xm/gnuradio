from bokeh.core.properties import Angle, Tuple, Bool, Int, Float, String, Instance, Override
from bokeh.io import show
from bokeh.model import Model
from bokeh.models import CustomJS, DataTable, LayoutDOM, HTMLBox, Button, FileInput, ButtonLike, ColumnDataSource, TableColumn
import bokeh.util.compiler
from bokeh.util.compiler import TypeScript

# Fix bug in nodejs_compile:
old_nodejs_compile = bokeh.util.compiler.nodejs_compile
def nodejs_compile(code, lang="javascript", file=None):
    out = old_nodejs_compile(code, lang, file)
    if 'deps' not in out:
        out['deps'] = []
    return out
bokeh.util.compiler.nodejs_compile = nodejs_compile

class Skymap(LayoutDOM):
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

    latlon = Tuple(Angle, Angle, default=(0, 0))

    azel = Tuple(Angle, Angle, default=(0, 0))
    targetAzel = Tuple(Angle, Angle)

    pointer_data_source = Instance(ColumnDataSource)

class Knob(HTMLBox):
    title = String(default="")
    value = Float(default=0)
    writable = Bool(default=False)
    digits = Int(default=3)
    decimals = Int(default=3)
    max = Float()
    min = Float()
    wrap = Bool(default=False)
    unit = String()
    active = Bool(default=True)

class DownloadButton(Button):
    data = Instance(CustomJS)
    filename = String(default="data.bin")
    mime_type = String(default="application/octet-stream")

class UploadButton(FileInput, ButtonLike):
    label = String("", help="""
    The text label for the button to display.
    """)

class ActiveButton(Button):
    active = Bool(False)

class SortedDataTable(DataTable):
    sortable = Override(default=True)
    highlight_field = String()
    sort_ascending = Bool(False)

class ActionMenuColumn(TableColumn):
    width = Override(default=50)
