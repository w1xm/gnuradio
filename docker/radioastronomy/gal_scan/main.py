# Run as "bokeh serve ."

from bokeh.plotting import curdoc
from gnuradio import blocks
import bokehgui
import numpy as np
import rci.client
import run

doc = curdoc()
doc.title = "Gal Scan"

client = rci.client.Client(client_name='gal_scan')
client.set_offsets(run.az_offset, run.el_offset)

tb = run.radiotelescope(client=client)

plot_lst = []

mag_to_db = blocks.nlog10_ff(20, tb.get_num_channels(), 0)
bokehgui_vector_sink_x_0 = bokehgui.vec_sink_f_proc(tb.get_num_channels(), "", 1)
plot = bokehgui.vec_sink_f(doc, plot_lst, bokehgui_vector_sink_x_0, is_message =False)

plot.initialize(update_time = 100, legend_list = [''])
plot.set_y_axis([0, 1])
plot.set_y_label("Spectral Power Density")
plot.set_x_label("Frequency (MHz)")
plot.set_x_values(np.linspace(tb.get_sdr_frequency()-(tb.get_output_vector_bandwidth()/2), tb.get_sdr_frequency()+(tb.get_output_vector_bandwidth()/2), tb.get_num_channels())/1e6)
plot.enable_axis_labels(True)
plot.set_layout(1,0)
plot.enable_max_hold()
plot.format_line(0, "blue", 1, "solid", None, 1.0)
layout_t = bokehgui.bokeh_layout.create_layout([plot], "fixed")
doc.add_root(layout_t)
tb.connect((tb.blocks_multiply_const_vxx_0, 0), (mag_to_db, 0))
tb.connect((mag_to_db, 0), (bokehgui_vector_sink_x_0, 0))

tb.start()

def cleanup_session(session_context):
    tb.stop()
    tb.wait()
doc.on_session_destroyed(cleanup_session)
