#!/usr/bin/env python3

from bokeh.application.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.events import Tap
from bokeh.layouts import column, row, grid
from bokeh.models import CustomJS, Button, ColumnDataSource, Spinner, Slider, Select, TextInput, DataTable, TableColumn, Panel, Tabs, Toggle, RadioButtonGroup, DateFormatter, HTMLTemplateFormatter, HoverTool, CrosshairTool, Paragraph
from bokeh.server.server import Server
from bokeh.plotting import curdoc
from bokeh.util import logconfig
from gnuradio import gr, blocks
from astropy import units as u
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
import uuid
import tornado.web
from tornado.web import HTTPError
from tornado.escape import xhtml_escape
from zipstream import AioZipStream
from zipstream import consts as zconsts
import rci.client
from galcoord import radome_observer
import run
from weather import Weather
from bokeh_models import Skymap, Knob, DownloadButton, UploadButton, ActiveButton, SortedDataTable, ActionMenuColumn, ActionMenuClick

RUNS_DIR = "/runs/"

LOG_ROLLOVER = 100
LOG_EXCLUDE = (
    'bokeh.server.views.ws',
    'tornado.access',
    'stderr',
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
        with open('messier.json') as f:
            objects = json.load(f)
            self.messier = [{
                'ra': o['ra']['decimal'],
                'dec': o['dec']['decimal'],
                'label': o['target']['name'],
            } for o in objects]
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
        self.active_action = {}
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
                        self.active_action = {}
                if self.actions_exit:
                    return
                self.maybe_stop_tb()
                logging.debug("Waiting for next action")
                self.actions_cv.wait()

    def get_queue_data(self):
        with self.actions_cv:
            d = {
                'id': [a['id'] for a in self.actions],
                'time': [int(a['time']*1000) for a in self.actions],
                'user': ["" for a in self.actions],
                'name': [a['name'] for a in self.actions],
                'active': [False for a in self.actions],
            }
            if self.active_action:
                # TODO: Render active action differently (bold?)
                d['id'].insert(0, self.active_action['id'])
                d['time'].insert(0, int(self.active_action['time']*1000))
                d['user'].insert(0, "")
                d['name'].insert(0, self.active_action['name'])
                d['active'].insert(0, True)
            return d

    def enqueue_action(self, name, callable, allow_queue=False, **kwargs):
        with self.actions_cv:
            if self.actions:
                # Don't allow manual commands if a survey is queued
                if not allow_queue and sum(1 for a in self.actions if a.get('survey')):
                    logging.warning("Busy; ignoring manual command")
                    return
                logging.info("Busy; enqueueing %s", name)
            a = {
                'id': str(uuid.uuid4()),
                'time': time.time(),
                'name': name,
                'callable': callable,
            }
            a.update(kwargs)
            self.actions.append(a)
            logging.debug("Notifying of new action")
            self.actions_cv.notify()

    def cancel_action(self, id):
        with self.actions_cv:
            for i, a in enumerate(self.actions):
                if a['id'] == id:
                    logging.info("Removing queued action")
                    del self.actions[i]
                    return
            if self.active_action and self.active_action['id'] == id:
                if 'survey' in self.active_action:
                    logging.info("Aborting running survey")
                    self.active_action['survey'].abort()
                    return
            logging.warning("Couldn't cancel action")

    def enqueue_run(self, args):
        survey = run.Survey(args)
        self.enqueue_action(
            name=args.output_dir,
            callable=functools.partial(survey.run, self.tb),
            survey=survey,
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

    def set_frequency(self, f):
        self.enqueue_action(
            name="set frequency to %f" % f,
            callable=functools.partial(self.tb.set_sdr_frequency, f),
        )

    def set_bandwidth(self, f):
        self.enqueue_action(
            name="set bandwidth to %f" % f,
            callable=functools.partial(self.tb.set_bandwidth, f),
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
        def set_x_values():
            plot.set_x_values(np.linspace(self.tb.get_sdr_frequency()-(self.tb.get_output_vector_bandwidth()/2), self.tb.get_sdr_frequency()+(self.tb.get_output_vector_bandwidth()/2), self.tb.get_num_channels())/1e6)
        set_x_values()
        plot.enable_axis_labels(True)
        plot.set_layout(1,0)
        plot.enable_max_hold()
        plot.format_line(0, "blue", 1, "solid", None, 1.0)

        azimuth = Knob(title="Azimuth", max=360, min=0, unit="°")
        elevation = Knob(title="Elevation", max=360, min=0, unit="°")
        rx_power = Knob(title="Average RX Power", digits=4, decimals=1, unit="dB(mW/Hz)")
        plot.stream.js_on_change("streaming", CustomJS(
            args = dict(rx_power=rx_power),
            code = """
            const data = cb_obj.data
            const average = data['y0'].reduce((a,b) => a+b)/data['y0'].length
            rx_power.value = (10*Math.log10(average))-180
            """,
        ))

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

        frequency = Knob(title="center frequency", writable=True, value=self.tb.get_sdr_frequency(), digits=10, decimals=0, unit="Hz")
        frequency.on_change('value', lambda name, old, new: self.set_frequency(new))

        bandwidth = Knob(title="filter bandwidth", writable=False, value=self.tb.get_bandwidth(), digits=7, decimals=0, unit="Hz")
        bandwidth.on_change('value', lambda name, old, new: self.set_bandwidth(new))

        reset = Button(label="Reset")
        def on_reset():
            gain.value = run.flowgraph_defaults['sdr_gain']
            frequency.value = run.flowgraph_defaults['sdr_frequency']
            bandwidth.value = run.flowgraph_defaults['bandwidth']
        reset.on_click(on_reset)

        manual = Panel(title="Manual", child=column(
            row(rx, gain),
            row(frequency, bandwidth),
            reset,
        ))

        run_models = {}
        automated_panels = []
        for group, args in run.arg_groups.items():
            # TODO: show grouping
            panel_models = []
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
                    if arg.get('metavar') == 'Hz':
                        if 'digits' not in bokeh_args:
                            bokeh_args['digits'] = 10
                            if bokeh_args.get('max'):
                                bokeh_args['digits'] = len("%d" % bokeh_args['max'])
                        type = functools.partial(Knob, decimals=0, unit=arg['metavar'])
                        del bokeh_args['step']
                        del bokeh_args['tags']
                        if 'writable' not in bokeh_args:
                            bokeh_args['writable'] = True
                elif 'choices' in arg:
                    type = Select
                    bokeh_args['options'] = [str(x) for x in arg['choices']]
                    if 'value' in bokeh_args:
                        bokeh_args['value'] = str(bokeh_args['value'])
                elif arg.get('action') in ('store_true', 'store_false'):
                    type = Select
                    bokeh_args['options'] = [('0', 'False'), ('1', 'True')]
                    bokeh_args['value'] = str(int(bokeh_args['value']))
                    bokeh_args['tags'] = ['boolean'] + bokeh_args.get('tags', [])
                if group.startswith("mode="):
                    # Make this smarter if we ever have a mode=gal tab
                    bokeh_args['disabled'] = True
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

        plan_p = Paragraph(
            sizing_mode="stretch_width",
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
                    const tags = run_models[k].tags
                    if (tags && tags.indexOf("boolean") >= 0) {
                      out[k] = parseInt(out[k])
                    }
                  }
                }
                return JSON.stringify(out, null, 2);
                """))
        start = Button(label="Start scan")
        def get_args(output_dir):
            return run.parse_args(
                [output_dir],
                {k: int(v.value) if "boolean" in v.tags else v.value for k, v in run_models.items() if not v.disabled},
            )
        def on_start():
            try:
                output_dir = os.path.join(self.runs_dir, "run_"+datetime.datetime.now().replace(microsecond=0).isoformat())
                args = get_args(output_dir)
                self.enqueue_run(args)
            except SystemExit:
                pass
        start.on_click(on_start)
        automated = Panel(title="Plan", child=column(Tabs(tabs=automated_panels), plan_p, row(load, save, start)))

        # TODO: Show cancel buttons for active or queued actions
        queue_cds = ColumnDataSource(data=self.get_queue_data())
        action_column = ActionMenuColumn(
            field="id", title="Action",
            menu=[
                ("Cancel", "cancel"),
            ],
        )
        def on_action_menu_click(event):
            if event.item == "cancel":
                self.cancel_action(event.value)
            else:
                logging.warn("Unknown action clicked: %s", event.item)

        action_column.on_event(ActionMenuClick, on_action_menu_click)
        queue_table = SortedDataTable(
            source=queue_cds,
            columns=[
                TableColumn(
                    field="time", title="Time",
                    formatter=DateFormatter(format="%Y-%m-%d %H:%M:%S"),
                ),
                TableColumn(field="user", title="User"),
                TableColumn(field="name", title="Job"),
                action_column,
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

        tabs = Tabs(tabs=[manual, automated, queue, results])

        status_p = Paragraph(
            sizing_mode="stretch_width",
        )

        controls = column(
            row(azimuth, elevation, rx_power),
            status_p,
            tabs,
            log_table)

        def get_survey_data():
            pointers = {
                'ra': [],
                'dec': [],
                'label': [],
                'colour': [],
            }
            for o in self.messier:
                pointers['ra'].append(o['ra'])
                pointers['dec'].append(o['dec'])
                pointers['label'].append(o['label'])
                pointers['colour'].append('')
            survey = self.active_action.get('survey')
            out = {'pointers': pointers, 'status_message': 'Idle', 'plan_message': 'Invalid parameters'}
            if survey:
                groups = survey.coord_groups
                i = 0
                for sc, colour in zip(reversed(groups), ('rgb(0, 192, 0)', 'rgb(192, 0, 0)')):
                    sc = sc.icrs
                    for sc in sc:
                        pointers['ra'].append(sc.ra.to(u.degree).value)
                        pointers['dec'].append(sc.dec.to(u.degree).value)
                        pointers['label'].append(str(i+1))
                        pointers['colour'].append(colour)
                        i += 1
                out['status_message'] = 'Time remaining on current survey: %s' % (survey.time_remaining.to_datetime())
            survey = None
            try:
                survey = run.Survey(get_args('bogus'))
                out['plan_message'] = 'Estimated runtime: %s' % (survey.time_remaining.to_datetime())
                if tabs.tabs[tabs.active] == automated:
                    # TODO: Use the underlying numpy arrays
                    sc = survey.iterator.coords_now.icrs
                    for i, sc in enumerate(sc[:1000]):
                        pointers['ra'].append(sc.ra.to(u.degree).value)
                        pointers['dec'].append(sc.dec.to(u.degree).value)
                        pointers['label'].append(str(i+1))
                        pointers['colour'].append('rgb(148,0,211)')
            except:
                logging.getLogger('stderr').exception('Invalid parameters')
            return out
        sd = get_survey_data()
        pointers_cds = ColumnDataSource(data=sd['pointers'])
        def update_pointers(attr, old, new):
            logging.debug('Updating pointers')
            sd = get_survey_data()
            pointers_cds.data = sd['pointers']
            plan_p.text = sd['plan_message']
            status_p.text = sd['status_message']
        update_pointers(None, None, None)

        log_cds.on_change('data', update_pointers)
        tabs.on_change('active', update_pointers)
        for m in run_models.values():
            m.on_change('value', update_pointers)

        skymap = Skymap(
            height=600, sizing_mode="stretch_height",
            pointer_data_source=pointers_cds,
        )
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
            set_x_values()
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

async def empty():
    if False:
        yield

# Monkey patch to fix the constant
zconsts.DD_MAGIC = b'\x50\x4b\x07\x08'

class AioDirZipStream(AioZipStream):
    def _create_file_struct(self, data):
        file_struct = super()._create_file_struct(data)
        if data['name'][-1] == '/':
            # Clear the data descriptor flag for directories
            file_struct['flags'] &= ~0b00001000
        return file_struct

    def _make_cdir_file_header(self, file_struct):
        fields = {"signature": zconsts.CDFH_MAGIC,
                  # N.B. zipstream's struct definition has these flipped
                  "version": 0x03,  # 0x03 - unix
                  "system": zconsts.ZIP32_VERSION,
                  "version_ndd": zconsts.ZIP32_VERSION,
                  "flags": file_struct['flags'],
                  "compression": file_struct['cmpr_id'],
                  "mod_time": file_struct['mod_time'],
                  "mod_date": file_struct['mod_date'],
                  "uncomp_size": file_struct.get('size', 0),
                  "comp_size": file_struct.get('csize', 0),
                  "offset": file_struct['offset'],  # < file header offset
                  "crc": file_struct['crc'],
                  "fname_len": len(file_struct['fname']),
                  "extra_len": 0,
                  "fcomm_len": 0,  # comment length
                  "disk_start": 0,
                  "attrs_int": 0,
                  "attrs_ext": 0}
        logging.debug("Packing %s", file_struct['fname'])
        if file_struct['fname'].endswith(b'/'):
            fields['attrs_ext'] = (0o40755 << 16)# | 0x10 # | 0o40000
        else:
            fields['attrs_ext'] = (0o100644 << 16)
        cdfh = zconsts.CDLF_TUPLE(**fields)
        cdfh = zconsts.CDLF_STRUCT.pack(*cdfh)
        cdfh += file_struct['fname']
        return cdfh

    async def _stream_single_file(self, file_struct):
        if file_struct['fname'].endswith(b'/'):
            # Directories have no contents
            yield self._make_local_file_header(file_struct)
            return
        async for chunk in super()._stream_single_file(file_struct):
            yield chunk

class DirectoryHandler(tornado.web.RequestHandler):
    def initialize(self, path):
        self.root = path

    async def get(self, relative_path):
        abspath = os.path.abspath(os.path.join(self.root, relative_path))
        if not (abspath + os.path.sep).startswith(self.root):
            logging.warning("root %s abspath %s relative_path %s", self.root, abspath, relative_path)
            raise HTTPError(403, "%s is not in root static directory", relative_path)

        if os.path.isdir(abspath):
            if self.get_argument('zip', False) != False:
                files = [{'name': os.path.basename(abspath).replace(':', '_') + '/', 'stream': empty()}] + [
                    {
                        'file': os.path.join(abspath, name),
                        'name': os.path.join(os.path.basename(abspath), name).replace(':', '_'),
                    }
                    for name in sorted(os.listdir(abspath))
                ]
                self.set_header('Content-Type', 'application/zip')
                self.set_header('Content-Disposition', 'attachment; filename="%s.zip"' % os.path.basename(abspath).replace(':', '_').replace('\\', '\\\\').replace('"', '\\"'))
                async for chunk in AioDirZipStream(files, chunksize=1024*1024).stream():
                    self.write(chunk)
                    await self.flush()
                return self.finish()
            html = """
<html>
<title>Directory listing for %(relative_path)s</title>
<body>
<h2>Directory listing for %(relative_path)s</h2>
<a href="?zip">Download all</a>
<hr><ul>""" % {'relative_path': relative_path}
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
