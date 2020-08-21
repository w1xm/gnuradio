#!/usr/bin/env python3

from bokeh.application.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.events import Tap
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput, DataTable, TableColumn
from bokeh.server.server import Server
from bokeh.plotting import curdoc
from bokeh.util import logconfig
from gnuradio import gr, blocks
import bokehgui
import functools
import numpy as np
import logging
import logging.handlers
import socket
import rci.client
import run
from bokeh_models import Skymap

class LogWatcher(logging.handlers.QueueHandler):
    def __init__(self, doc, cds):
        super().__init__(cds)
        self.setLevel(logging.INFO)
        self.doc = doc
        self.rollover = 100

    def filter(self, record):
        if not super().filter(record):
            return False
        if record.name in (
                'bokeh.server.views.ws',
                'tornado.access',
        ):
            return False
        return True

    def enqueue(self, record):
        self.doc.add_next_tick_callback(
            functools.partial(
                self.queue.stream,
                {
                    "asctime": [record.asctime],
                    "levelname": [record.levelname],
                    "message": [record.message],
                },
                rollover=self.rollover,
            )
        )

class SessionHandler(Handler):
    def __init__(self):
        super().__init__()

    def on_server_loaded(self, server_context):
        self.client = rci.client.Client(client_name='gal_scan')
        self.client.set_offsets(run.az_offset, run.el_offset)

        self.tb = run.radiotelescope(client=self.client)
        self.mag_to_aW = blocks.multiply_const_vff([1e18] * self.tb.get_num_channels())
        self.tb.connect((self.tb.blocks_multiply_const_vxx_0, 0), (self.mag_to_aW, 0))
        null_sink = blocks.null_sink(gr.sizeof_float*self.tb.get_num_channels())
        self.tb.connect(self.mag_to_aW, null_sink)

        self.tb.start()

    def on_server_unloaded(self, server_context):
        self.tb.stop()
        self.tb.wait()

    async def on_session_created(self, session_context):
        session_context.test_variable = 123

    async def on_session_destroyed(self, session_context):
        logging.info("Session %s destroyed", session_context.id)
        logging.debug("test_variable = %s", getattr(session_context, 'test_variable'))

    def modify_document(self, doc):
        self.tb.lock()
        sink = bokehgui.vec_sink_f_proc(self.tb.get_num_channels(), "", 1)
        self.tb.connect((self.mag_to_aW, 0), (sink, 0))
        self.tb.unlock()

        # TODO: Populate with a snapshot of log messages
        log_cds = ColumnDataSource(data=dict(asctime=[''], levelname=[''], message=['']))
        lw = LogWatcher(doc, log_cds)
        logging.getLogger().addHandler(lw)

        def cleanup_session(session_context):
            self.tb.lock()
            self.tb.disconnect((self.mag_to_aW, 0), (sink, 0))
            self.tb.unlock()
            logging.getLogger().removeHandler(lw)
        doc.on_session_destroyed(cleanup_session)

        doc.title = "Gal Scan GUI"

        plot_lst = []

        plot = bokehgui.vec_sink_f(doc, plot_lst, sink, is_message =False)

        plot.initialize(update_time = 100, legend_list = [''])
        plot.get_figure().aspect_ratio = 2
        plot.set_y_axis([0, 10])
        plot.set_y_label("Power at feed (aW / Hz)")
        plot.set_x_label("Frequency (MHz)")
        plot.set_x_values(np.linspace(self.tb.get_sdr_frequency()-(self.tb.get_output_vector_bandwidth()/2), self.tb.get_sdr_frequency()+(self.tb.get_output_vector_bandwidth()/2), self.tb.get_num_channels())/1e6)
        plot.enable_axis_labels(True)
        plot.set_layout(1,0)
        plot.enable_max_hold()
        plot.format_line(0, "blue", 1, "solid", None, 1.0)

        gain = Slider(title="gain", value=self.tb.get_sdr_gain(), start=0, end=65)
        gain.on_change('value', lambda name, old, new: self.tb.set_sdr_gain(new))

        # TODO: Automatically sort by asctime descending
        # TODO: Autoscale columns
        log_table = DataTable(
            source=log_cds,
            columns=[
                TableColumn(field="asctime", title="Time"),
                TableColumn(field="levelname", title="Level"),
                TableColumn(field="message", title="Message"),
            ],
            aspect_ratio=2,
            sizing_mode="stretch_width",
            sortable=True,
        )

        controls = column(gain, log_table)

        skymap = Skymap(height=600, sizing_mode="stretch_height")
        def on_tap(event):
            # TODO: Dispatch self.tb.point on the execution thread instead
            logging.info("Manually slewing to (%.2f, %.2f)", event.x, event.y)
            self.client.set_azimuth_position(event.x)
            self.client.set_elevation_position(event.y)
        skymap.on_event(Tap, on_tap)

        doc.add_root(
            row(
                column(
                    skymap,
                    plot.get_figure(),
                ),
                controls,
            ),
        )

        async def update_status():
            status = self.client.status
            skymap.latlon = (status['Latitude'], status['Longitude'])
            skymap.azel = (status['AzPos'], status['ElPos'])
            if status['CommandAzFlags'] == 'POSITION' or status['CommandElFlags'] == 'POSITION':
                skymap.targetAzel = (status['CommandAzPos'], status['CommandElPos'])
            else:
                skymap.targetAzel = None

        doc.add_periodic_callback(update_status, 200)

if __name__ == '__main__':
    logconfig.basicConfig(
        format="%(asctime)-15s %(levelname)-8s [%(name)s] [%(module)s:%(funcName)s] %(message)s",
        level=logging.DEBUG,
    )
    server = Server(
        {'/': Application(SessionHandler())},
        allow_websocket_origin=[socket.getfqdn().lower()+":5006"],
    )
    server.start()
    server.io_loop.start()
