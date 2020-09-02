#!/usr/bin/env python3

from bokeh.application.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.events import Tap
from bokeh.layouts import column, row, grid
from bokeh.models import CustomJS, Button, ColumnDataSource, Spinner, Slider, Select, TextInput, DataTable, TableColumn, Panel, Tabs, Toggle, RadioButtonGroup, DateFormatter, HTMLTemplateFormatter, HoverTool, CrosshairTool
from bokeh.server.server import Server
from bokeh.plotting import curdoc
from bokeh.util import logconfig
from gnuradio import gr, blocks
import bokehgui
import base64
import collections
import datetime
import functools
import numpy as np
import json
import logging
import logging.handlers
import os
import os.path
import socket
import threading
import time
import tornado.web
from tornado.web import HTTPError
from tornado.escape import xhtml_escape
import rci.client
from galcoord import radome_observer
import run
from weather import Weather
from bokeh_models import Skymap, Knob, DownloadButton, UploadButton, ActiveButton, SortedDataTable

RUNS_DIR = "/runs/"

LOG_ROLLOVER = 100
LOG_EXCLUDE = (
    'bokeh.server.views.ws',
    'tornado.access',
)

class LogWatcher(logging.handlers.QueueHandler):
    def __init__(self):
        super().__init__(None)
        self.setLevel(logging.INFO)
        self.asctime = collections.deque(maxlen=LOG_ROLLOVER)
        self.levelname = collections.deque(maxlen=LOG_ROLLOVER)
        self.message = collections.deque(maxlen=LOG_ROLLOVER)

    def filter(self, record):
        return super().filter(record) and record.name not in LOG_EXCLUDE

    def enqueue(self, record):
        self.asctime.append(record.asctime)
        self.levelname.append(record.levelname)
        self.message.append(record.message)

    def get_table(self):
        with self.lock:
            return {
                'asctime': list(self.asctime),
                'levelname': list(self.levelname),
                'message': list(self.message),
            }

class BokehLogWatcher(logging.handlers.QueueHandler):
    def __init__(self, doc, cds):
        super().__init__(cds)
        self.setLevel(logging.INFO)
        self.doc = doc

    def filter(self, record):
        return super().filter(record) and record.name not in LOG_EXCLUDE

    def enqueue(self, record):
        self.doc.add_next_tick_callback(
            functools.partial(
                self.queue.stream,
                {
                    "asctime": [record.asctime],
                    "levelname": [record.levelname],
                    "message": [record.message],
                },
                rollover=LOG_ROLLOVER,
            )
        )

class vec_sink_f(bokehgui.vec_sink_f):
    def add_custom_tools(self):
        # N.B. Max hold comes from a different CDS so can't be shown in the same tooltip :(
        hover = HoverTool(
            tooltips = [
                ("freq", "$x{0,0.00} MHz"),
                ("power", "@y0 zW / Hz"),
            ],
            mode = 'vline', renderers = self.lines)
        crosshair = CrosshairTool()
        self.plot.add_tools(hover, crosshair)

class SessionHandler(Handler):
    def __init__(self, lw, runs_dir):
        super().__init__()
        self.lw = lw
        self.runs_dir = runs_dir

    def on_server_loaded(self, server_context):
        self.server_context = server_context
        self.client = rci.client.Client(client_name='gal_scan')
        self.client.set_offsets(run.AZ_OFFSET, run.EL_OFFSET)

        self.tb = run.radiotelescope(client=self.client)
        self.mag_to_zW = blocks.multiply_const_vff([1e18] * self.tb.get_num_channels())
        self.tb.connect((self.tb.blocks_multiply_const_vxx_0, 0), (self.mag_to_zW, 0))
        null_sink = blocks.null_sink(gr.sizeof_float*self.tb.get_num_channels())
        self.tb.connect(self.mag_to_zW, null_sink)

        self.started = False
        self.actions = collections.deque()
        self.actions_cv = threading.Condition()
        self.actions_exit = False
        self.active_action = None
        self.actions_thread = threading.Thread(target=self.action_thread, name="radiotelescope")
        self.actions_thread.start()

    def action_thread(self):
        with self.actions_cv:
            while True:
                logging.debug("Looking for next action")
                while self.actions:
                    self.start_tb()
                    action = self.actions.popleft()
                    logging.info("Executing %s", action["name"])
                    self.active_action = action
                    # Release the lock so that the deque can be inspected and appended
                    self.actions_cv.release()
                    try:
                        action["callable"]()
                    except:
                        logging.exception("Exception while running %s", action["name"])
                    finally:
                        self.actions_cv.acquire()
                        self.active_action = None
                if self.actions_exit:
                    return
                self.maybe_stop_tb()
                logging.debug("Waiting for next action")
                self.actions_cv.wait()

    def get_queue_data(self):
        with self.actions_cv:
            d = {
                'time': [int(a['time']*1000) for a in self.actions],
                'user': ["" for a in self.actions],
                'name': [a['name'] for a in self.actions],
                'active': [False for a in self.actions],
            }
            if self.active_action:
                # TODO: Render active action differently (bold?)
                d['time'].insert(0, int(self.active_action['time']*1000))
                d['user'].insert(0, "")
                d['name'].insert(0, self.active_action['name'])
                d['active'].insert(0, True)
            return d

    def enqueue_action(self, name, callable, allow_queue=False):
        with self.actions_cv:
            if self.actions:
                if not allow_queue:
                    logging.warning("Busy; ignoring manual command")
                    return
                logging.info("Busy; enqueueing %s", name)
            self.actions.append({
                'time': time.time(),
                'name': name,
                'callable': callable,
            })
            logging.debug("Notifying of new action")
            self.actions_cv.notify()

    def enqueue_run(self, args):
        self.enqueue_action(
            name=args.output_dir,
            callable=functools.partial(run.run, self.tb, args),
            allow_queue=True,
        )

    def point(self, az, el):
        def callable():
            self.client.set_azimuth_position(az)
            self.client.set_elevation_position(el)
        self.enqueue_action(
            name="manual slew to (%.2f, %.2f)" % (az, el),
            callable=callable,
        )

    def set_gain(self, gain):
        self.enqueue_action(
            name="set gain to %d" % gain,
            callable=functools.partial(self.tb.set_sdr_gain, gain),
        )

    def set_rx(self, rx):
        self.enqueue_action(
            name="set rx to %s" % ("enabled" if rx else "disabled (50Ω load)"),
            callable=functools.partial(self.client.set_band_rx, 0, rx),
        )

    def on_server_unloaded(self, server_context):
        logging.info("on_server_unloaded")
        self.actions_exit = True
        self.actions_cv.notify()
        self.actions_thread.join()
        self.tb.stop()
        self.tb.wait()

    def start_tb(self):
        with self.actions_cv:
            if not self.started:
                logging.info("Starting flowgraph")
                self.tb.start()
                self.started = True

    def maybe_stop_tb(self):
        num_sessions = len(self.server_context.sessions)
        with self.actions_cv:
            if self.started and not self.actions and not self.active_action and not num_sessions:
                logging.info("Stopping flowgraph")
                self.tb.stop()
                self.started = False

    async def on_session_created(self, session_context):
        logging.info("Session %s created", session_context.id)
        self.start_tb()

    async def on_session_destroyed(self, session_context):
        logging.info("Session %s destroyed", session_context.id)
        self.maybe_stop_tb()

    def modify_document(self, doc):
        self.tb.lock()
        sink = bokehgui.vec_sink_f_proc(self.tb.get_num_channels(), "", 1)
        self.tb.connect((self.mag_to_zW, 0), (sink, 0))
        self.tb.unlock()

        log_cds = ColumnDataSource(data=self.lw.get_table())
        blw = BokehLogWatcher(doc, log_cds)
        logging.getLogger().addHandler(blw)

        def cleanup_session(session_context):
            self.tb.lock()
            self.tb.disconnect((self.mag_to_zW, 0), (sink, 0))
            self.tb.unlock()
            logging.getLogger().removeHandler(blw)
        doc.on_session_destroyed(cleanup_session)

        doc.title = "Gal Scan GUI"

        plot_lst = []

        plot = vec_sink_f(doc, plot_lst, sink, is_message =False)

        plot.initialize(update_time = 100, legend_list = [''])
        plot.get_figure().aspect_ratio = 2
        plot.set_y_axis([0, 10])
        plot.set_y_label("Power at feed (zW / Hz)")
        plot.set_x_label("Frequency (MHz)")
        plot.set_x_values(np.linspace(self.tb.get_sdr_frequency()-(self.tb.get_output_vector_bandwidth()/2), self.tb.get_sdr_frequency()+(self.tb.get_output_vector_bandwidth()/2), self.tb.get_num_channels())/1e6)
        plot.enable_axis_labels(True)
        plot.set_layout(1,0)
        plot.enable_max_hold()
        plot.format_line(0, "blue", 1, "solid", None, 1.0)

        azimuth = Knob(title="Azimuth", max=360, min=0, unit="°")
        elevation = Knob(title="Elevation", max=360, min=0, unit="°")

        log_table = SortedDataTable(
            source=log_cds,
            columns=[
                TableColumn(field="asctime", title="Time", width=140),
                TableColumn(field="levelname", title="Level", width=60),
                TableColumn(field="message", title="Message", width=1500),
            ],
            autosize_mode="none",
            aspect_ratio=2,
            sizing_mode="stretch_width",
            sortable=True,
        )

        gain = Slider(title="gain", value=self.tb.get_sdr_gain(), start=0, end=65)
        gain.on_change('value', lambda name, old, new: self.set_gain(new))

        rx = ActiveButton(label="RX enabled")
        rx.on_click(lambda: self.set_rx(not rx.active))

        manual = Panel(title="Manual", child=column(
            row(rx, gain),
        ))

        run_models = {}
        automated_panels = []
        for group, args in run.arg_groups.items():
            # TODO: show grouping
            panel_models = []
            # TODO: hide or disable mode=grid if grid is not selected
            for key, arg in args.items():
                key = key.replace('-', '_')
                bokeh_args = arg.get('bokeh', {})
                bokeh_args['name'] = key
                bokeh_args['tags'] = ['args']
                if 'default' in arg:
                    bokeh_args['value'] = arg['default']
                if 'help' in arg:
                    bokeh_args['title'] = arg['help']
                    if 'metavar' in arg:
                        bokeh_args['title'] += " (%s)" % (arg['metavar'])
                type = TextInput
                if arg.get('type') in (float, int):
                    type = Spinner
                    if 'bokeh' in arg and 'start' in arg['bokeh'] and 'end' in arg['bokeh']:
                        type = Slider
                    if 'step' not in bokeh_args:
                        if arg['type'] == int:
                            bokeh_args['step'] = 1
                        else:
                            bokeh_args['step'] = 0.01
                elif 'choices' in arg:
                    type = Select
                    bokeh_args['options'] = [str(x) for x in arg['choices']]
                    bokeh_args['value'] = str(bokeh_args['value'])
                elif arg.get('action') in ('store_true', 'store_false'):
                    type = Select
                    bokeh_args['options'] = [('0', 'False'), ('1', 'True')]
                    bokeh_args['value'] = str(int(bokeh_args['value']))
                    bokeh_args['tags'] = ['boolean'] + bokeh_args.get('tags', [])
                m = type(**bokeh_args)
                run_models[key] = m
                panel_models.append(m)
            automated_panels.append(Panel(title=group, child=grid(panel_models, ncols=2)))
        for panel in automated_panels:
            if panel.title.startswith("mode="):
                mode_str = panel.title.split('=')[1]
                run_models['mode'].js_on_change(
                    'value',
                    CustomJS(
                        args=dict(panel=panel, mode=mode_str),
                        code="""panel.select(Bokeh.require("models/widgets/control").Control).forEach(c => c.disabled = (this.value != mode))""",
                    )
                )
        load = UploadButton(name="load-settings", accept=".json,application/json", label="Load settings")
        def on_load(attr, old, new):
            data = json.loads(base64.b64decode(new))
            for key, value in data.items():
                if isinstance(run_models[key], Select):
                    value = str(value)
                run_models[key].value = value
        load.on_change('value', on_load)

        save = DownloadButton(
            label="Save settings",
            filename="gal_scan_settings.json",
            mime_type="application/json",
            data=CustomJS(
                args=dict(run_models=run_models),
                code="""
                const out = {}
                for (let k in run_models) {
                  if (!run_models[k].disabled) {
                    out[k] = run_models[k].value
                    if (run_models[k].tags.indexOf("boolean") >= 0) {
                      out[k] = parseInt(out[k])
                    }
                  }
                }
                return JSON.stringify(out, null, 2);
                """))
        start = Button(label="Start scan")
        def on_start():
            try:
                output_dir = os.path.join(self.runs_dir, "run_"+datetime.datetime.now().replace(microsecond=0).isoformat())
                args = run.parse_args(
                    [output_dir],
                    {k: int(v.value) if "boolean" in v.tags else v.value for k, v in run_models.items() if not v.disabled},
                )
                self.enqueue_run(args)
            except SystemExit:
                pass
        start.on_click(on_start)
        automated = Panel(title="Plan", child=column(Tabs(tabs=automated_panels), row(load, save, start)))

        # TODO: Show cancel buttons for active or queued actions
        queue_cds = ColumnDataSource(data=self.get_queue_data())
        queue_table = SortedDataTable(
            source=queue_cds,
            columns=[
                TableColumn(
                    field="time", title="Time",
                    formatter=DateFormatter(format="%Y-%m-%d %H:%M:%S"),
                ),
                TableColumn(field="user", title="User"),
                TableColumn(field="name", title="Job"),
            ],
            highlight_field="active",
            sort_ascending=True,
            autosize_mode="fit_viewport",
            aspect_ratio=2,
            sizing_mode="stretch_width",
        )
        queue = Panel(title="Queue", child=queue_table)

        results_cds = ColumnDataSource(data={"name": [], "mtime": []})
        results_table = SortedDataTable(
            source=results_cds,
            columns=[
                TableColumn(
                    field="mtime", title="Time",
                    formatter=DateFormatter(format="%Y-%m-%d %H:%M:%S"),
                ),
                TableColumn(
                    field="name", title="Name",
                    formatter=HTMLTemplateFormatter(template='<a href="/runs/<%= value %>/" target="_blank"><%= value %></a>')
                ),
            ],
            autosize_mode="fit_viewport",
            aspect_ratio=2,
            sizing_mode="stretch_width",
            sortable=True,
        )
        results = Panel(title="Results", child=results_table)

        controls = column(
            row(azimuth, elevation),
            Tabs(tabs=[manual, automated, queue, results]),
            log_table)

        skymap = Skymap(height=600, sizing_mode="stretch_height")
        skymap.on_event(Tap, lambda event: self.point(event.x, event.y))

        doc.add_root(
            row(
                column(
                    skymap,
                    plot.get_figure(),
                ),
                controls,
            ),
        )

        async def update_status(last_status={}):
            status = self.client.status
            skymap.latlon = (status['Latitude'], status['Longitude'])
            skymap.azel = (status['AzPos'], status['ElPos'])
            if status['CommandAzFlags'] == 'POSITION' or status['CommandElFlags'] == 'POSITION':
                skymap.targetAzel = (status['CommandAzPos'], status['CommandElPos'])
            else:
                skymap.targetAzel = None
            azimuth.value = status['AzPos']
            elevation.value = status['ElPos']
            rx_active = status['Sequencer']['Bands'][0]['CommandRX']
            if not last_status or rx_active != last_status['Sequencer']['Bands'][0]['CommandRX']:
                if rx_active:
                    rx.label = "RX enabled"
                else:
                    rx.label = "RX disabled (50Ω load)"
                rx.active = rx_active
            queue_data = self.get_queue_data()
            if queue_cds.data != queue_data:
                queue_cds.data = queue_data
            with os.scandir(self.runs_dir) as it:
                files = list(sorted(it, reverse=True, key=lambda f: f.stat().st_mtime))
                results_data = {
                    "name": [f.name for f in files],
                    "mtime": [int(f.stat().st_mtime*1000) for f in files],
                }
                if results_data != results_cds.data:
                    results_cds.data = results_data
            last_status.update(status)

        doc.add_periodic_callback(update_status, 200)

class DirectoryHandler(tornado.web.RequestHandler):
    def initialize(self, path):
        self.root = path

    async def get(self, relative_path):
        abspath = os.path.abspath(os.path.join(self.root, relative_path))
        if not (abspath + os.path.sep).startswith(self.root):
            logging.warning("root %s abspath %s relative_path %s", self.root, abspath, relative_path)
            raise HTTPError(403, "%s is not in root static directory", relative_path)

        if os.path.isdir(abspath):
            html = '<html><title>Directory listing for %s</title><body><h2>Directory listing for %s</h2><hr><ul>' % (relative_path, relative_path)
            for filename in sorted(os.listdir(abspath)):
                force_slash = ''
                full_path = filename
                if os.path.isdir(os.path.join(abspath, filename)):
                    force_slash = '/'

                html += '<li><a href="%s%s">%s%s</a>' % (xhtml_escape(full_path), force_slash, xhtml_escape(filename), force_slash)

            return self.finish(html + '</ul><hr>')
        raise HTTPError(404, "%s does not exist", relative_path)

def wx_received(wx):
    # TODO: Does this need locking?
    radome_observer.temperature = wx['temperature']
    radome_observer.relative_humidity = wx['relative_humidity']
    radome_observer.pressure = wx['pressure']
    logging.info("Performing refraction correction for %s %s %s", radome_observer.temperature, radome_observer.relative_humidity, radome_observer.pressure)

if __name__ == '__main__':
    logconfig.basicConfig(
        format="%(asctime)-15s %(levelname)-8s [%(name)s] [%(module)s:%(funcName)s] %(message)s",
        level=logging.DEBUG,
    )
    os.makedirs(RUNS_DIR, exist_ok=True)
    lw = LogWatcher()
    logging.getLogger().addHandler(lw)
    wx = Weather(callback=wx_received)
    wx.start()
    server = Server(
        {'/': Application(SessionHandler(lw=lw, runs_dir=RUNS_DIR))},
        allow_websocket_origin=[socket.getfqdn().lower()+":5006"],
        extra_patterns=[
            (r'/runs/()', DirectoryHandler, {'path': RUNS_DIR}),
            (r'/runs/(.*)/', DirectoryHandler, {'path': RUNS_DIR}),
            (r'/runs/(.*)', tornado.web.StaticFileHandler, {'path': RUNS_DIR}),
        ],
    )
    server.start()
    server.io_loop.start()
