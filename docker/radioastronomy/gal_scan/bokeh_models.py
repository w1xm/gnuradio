from bokeh.core.properties import Angle, Tuple, Bool, Int, Float, String, Instance
from bokeh.io import show
from bokeh.model import Model
from bokeh.models import CustomJS, ColumnDataSource, LayoutDOM, HTMLBox, Button, FileInput, ButtonLike
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

    latlon = Tuple(Angle, Angle, default=(0, 0))

    azel = Tuple(Angle, Angle, default=(0, 0))
    targetAzel = Tuple(Angle, Angle)

class Knob(HTMLBox):
    __implementation__ = "knob.ts"

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
    __implementation__ = "download_button.ts"

    data = Instance(CustomJS)
    filename = String(default="data.bin")
    mime_type = String(default="application/octet-stream")

class UploadButton(FileInput, ButtonLike):
    __implementation__ = "upload_button.ts"

    label = String("", help="""
    The text label for the button to display.
    """)

class ActiveButton(Button):
    __implementation__ = "active_button.ts"

    active = Bool(False)
