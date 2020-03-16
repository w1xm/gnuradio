
import numpy as np
import matplotlib.pyplot as plt
import time as pytime

#!/usr/bin/python

#darkskycal global variables
darksky_exists = False
darksky = None

#axis extremes
flo=1420.4-0.75
fhi=1420.4+0.75
##################################################
##################################################
##################################################
            # RCI STUFF #
##################################################
##################################################
##################################################
az_offset=5.5
el_offset=-5.5
import rci.client
client = rci.client.Client("ws://localhost:8502/api/ws")
client.set_offsets(az_offset, el_offset)

def point(az,el): #point the dish
    client.set_azimuth_position(az)
    client.set_elevation_position(el)
    print 'Moving to position ' + str(az)+' , '+str(el)+'.'
    return

def park():
    point(250,50)
    print "Parking"
    return

##################################################
##################################################
##################################################
            # GNU RADIO STUFF #
##################################################
##################################################
##################################################
#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# Generated: Sat Aug 11 17:48:29 2018
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt4 import Qt
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import pfb
from gnuradio.qtgui import Range, RangeWidget
from optparse import OptionParser
import limesdr
import sys
import threading
#import time


class top_block(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Top Block")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Top Block")
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 15e6
        self.integration_bandwidth = integration_bandwidth = 2.5e3
        self.if_bandwidth_2 = if_bandwidth_2 = .75e6
        self.dec_rate_1 = dec_rate_1 = 5
        self.samp_rate_2 = samp_rate_2 = samp_rate/dec_rate_1
        self.num_channels = num_channels = int(if_bandwidth_2/integration_bandwidth)
        self.samp_rate_3 = samp_rate_3 = samp_rate_2/num_channels
        self.integration_time = integration_time = .5
        self.variable_function_probe = variable_function_probe = 0
        self.output_samp_rate = output_samp_rate = 1.0/integration_time
        self.integration_dec_rate = integration_dec_rate = int(integration_time*samp_rate_3/2)
        self.if_bandwidth_0 = if_bandwidth_0 = 4.5e6
        self.gain = gain = 60
        self.freq = freq = 1.4204e9
        self.channel_map = channel_map = range(int(num_channels/2.0+1.0),num_channels,1)+range(0,int(num_channels/2.0+1.0),1)

        ##################################################
        # Blocks
        ##################################################
        self.probe_signal = blocks.probe_signal_vf(num_channels)
        self._gain_range = Range(0, 70, 1, 60, 200)
        self._gain_win = RangeWidget(self._gain_range, self.set_gain, "gain", "counter_slider", int)
        self.top_layout.addWidget(self._gain_win)
        
        def _variable_function_probe_probe():
            while True:
                val = self.probe_signal.level()
                try:
                    self.set_variable_function_probe(val)
                except AttributeError:
                    pass
                pytime.sleep(1.0 / (10))
        _variable_function_probe_thread = threading.Thread(target=_variable_function_probe_probe)
        _variable_function_probe_thread.daemon = True
        _variable_function_probe_thread.start()
            
        self.pfb_channelizer_ccf_0 = pfb.channelizer_ccf(
              num_channels,
              (firdes.low_pass(1, samp_rate_2, integration_bandwidth, 250, firdes.WIN_HAMMING)),
              1.0,
              0)
        self.pfb_channelizer_ccf_0.set_channel_map((channel_map))
        self.pfb_channelizer_ccf_0.declare_sample_delay(0)
            
        self.low_pass_filter_1 = filter.fir_filter_ccf(dec_rate_1, firdes.low_pass(
            10, samp_rate, if_bandwidth_2, 1e5, firdes.WIN_HAMMING, 6.76))
        self.limesdr_source_2 = limesdr.source('0009072C02873717',
                     2,
                     1,
                     0,
                     0,
                     '',
                     freq-800e3,
                     samp_rate,
                     0,
                     1,
                     15e6,
                     0,
                     10e6,
                     3,
                     2,
                     2,
                     1,
                     if_bandwidth_0,
                     1,
                     5e6,
                     1,
                     if_bandwidth_0,
                     0,
                     0,
                     gain,
                     30,
                     0,
                     0,
                     0,
                     0)
        self.blocks_streams_to_vector_0 = blocks.streams_to_vector(gr.sizeof_gr_complex*1, num_channels)
        self.blocks_multiply_xx_1 = blocks.multiply_vcc(1)
        self.blocks_integrate_xx_0_0 = blocks.integrate_ff(integration_dec_rate, num_channels)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, '/home/w1xm-admin/Documents/DSP/data_out/recieve_block_sink', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_copy_0_0 = blocks.copy(gr.sizeof_gr_complex*1)
        self.blocks_copy_0_0.set_enabled(False)
        self.blocks_copy_0 = blocks.copy(gr.sizeof_gr_complex*1)
        self.blocks_copy_0.set_enabled(True)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(num_channels)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_SIN_WAVE, -800e3, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_1, 1))    
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_integrate_xx_0_0, 0))    
        self.connect((self.blocks_copy_0, 0), (self.blocks_multiply_xx_1, 0))    
        self.connect((self.blocks_copy_0_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.blocks_integrate_xx_0_0, 0), (self.probe_signal, 0))    
        self.connect((self.blocks_multiply_xx_1, 0), (self.low_pass_filter_1, 0))    
        self.connect((self.blocks_streams_to_vector_0, 0), (self.blocks_complex_to_mag_squared_0, 0))    
        self.connect((self.limesdr_source_2, 0), (self.blocks_copy_0, 0))    
        self.connect((self.limesdr_source_2, 0), (self.blocks_copy_0_0, 0))    
        self.connect((self.low_pass_filter_1, 0), (self.pfb_channelizer_ccf_0, 0))    

        for i in range(num_channels):
            self.connect((self.pfb_channelizer_ccf_0, i), (self.blocks_streams_to_vector_0, i))

    def toggle_copy(self, tf):
        self.blocks_copy_0.set_enabled(tf)  

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_samp_rate_2(self.samp_rate/self.dec_rate_1)
        self.low_pass_filter_1.set_taps(firdes.low_pass(10, self.samp_rate, self.if_bandwidth_2, 1e5, firdes.WIN_HAMMING, 6.76))
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_integration_bandwidth(self):
        return self.integration_bandwidth

    def set_integration_bandwidth(self, integration_bandwidth):
        self.integration_bandwidth = integration_bandwidth
        self.set_num_channels(int(self.if_bandwidth_2/self.integration_bandwidth))
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, self.samp_rate_2, self.integration_bandwidth, 250, firdes.WIN_HAMMING)))

    def get_if_bandwidth_2(self):
        return self.if_bandwidth_2

    def set_if_bandwidth_2(self, if_bandwidth_2):
        self.if_bandwidth_2 = if_bandwidth_2
        self.set_num_channels(int(self.if_bandwidth_2/self.integration_bandwidth))
        self.low_pass_filter_1.set_taps(firdes.low_pass(10, self.samp_rate, self.if_bandwidth_2, 1e5, firdes.WIN_HAMMING, 6.76))

    def get_dec_rate_1(self):
        return self.dec_rate_1

    def set_dec_rate_1(self, dec_rate_1):
        self.dec_rate_1 = dec_rate_1
        self.set_samp_rate_2(self.samp_rate/self.dec_rate_1)

    def get_samp_rate_2(self):
        return self.samp_rate_2

    def set_samp_rate_2(self, samp_rate_2):
        self.samp_rate_2 = samp_rate_2
        self.set_samp_rate_3(self.samp_rate_2/self.num_channels)
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, self.samp_rate_2, self.integration_bandwidth, 250, firdes.WIN_HAMMING)))

    def get_num_channels(self):
        return self.num_channels

    def set_num_channels(self, num_channels):
        self.num_channels = num_channels
        self.set_channel_map(range(int(self.num_channels/2.0+1.0),self.num_channels,1)+range(0,int(self.num_channels/2.0+1.0),1))
        self.set_samp_rate_3(self.samp_rate_2/self.num_channels)

    def get_samp_rate_3(self):
        return self.samp_rate_3

    def set_samp_rate_3(self, samp_rate_3):
        self.samp_rate_3 = samp_rate_3
        self.set_integration_dec_rate(int(self.integration_time*self.samp_rate_3/2))

    def get_integration_time(self):
        return self.integration_time

    def set_integration_time(self, integration_time):
        self.integration_time = integration_time
        self.set_integration_dec_rate(int(self.integration_time*self.samp_rate_3/2))
        self.set_output_samp_rate(1.0/self.integration_time)

    def get_variable_function_probe(self):
        return self.variable_function_probe

    def set_variable_function_probe(self, variable_function_probe):
        self.variable_function_probe = variable_function_probe

    def get_output_samp_rate(self):
        return self.output_samp_rate

    def set_output_samp_rate(self, output_samp_rate):
        self.output_samp_rate = output_samp_rate

    def get_integration_dec_rate(self):
        return self.integration_dec_rate

    def set_integration_dec_rate(self, integration_dec_rate):
        self.integration_dec_rate = integration_dec_rate

    def get_if_bandwidth_0(self):
        return self.if_bandwidth_0

    def set_if_bandwidth_0(self, if_bandwidth_0):
        self.if_bandwidth_0 = if_bandwidth_0
        self.limesdr_source_2.set_analog_filter(1,self.if_bandwidth_0,0)
        self.limesdr_source_2.set_digital_filter(1,self.if_bandwidth_0,0)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.limesdr_source_2.set_gain(self.gain,0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq

    def get_channel_map(self):
        return self.channel_map

    def set_channel_map(self, channel_map):
        self.channel_map = channel_map
        self.pfb_channelizer_ccf_0.set_channel_map((self.channel_map))


def main(top_block_cls=top_block, options=None):

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

 ######## ACTUALLY WHERE STUFF HAPPENS #######
    tb = top_block_cls()
    tb.start()
    tb.show()
    print('Receiving ...')

    global darksky
    global darksky_exists

    def snapshot(int_time): #straight snapshot over a certain integration time.
        tb.set_integration_time(int_time)
       # print 'Integration time set to '+str(int_time)+ ' seconds.'
        print 'Snapshot '+ str(int_time) + ' sec'
        vec=tb.get_variable_function_probe() #old vector
        pointa=vec[0]
        pointb=vec[-1]
        tb.toggle_copy(True) #start copying
        while vec[0]==pointa and vec[-1]==pointb:
            pytime.sleep(1)
            vec=tb.get_variable_function_probe()
        tb.toggle_copy(False) #stop copying
        return np.array(vec)

    def dark_sky_calib(int_time): #for use when pointing at the dark sky
        global darksky
        darksky=snapshot(int_time)
        global darksky_exists
        darksky_exists=True
        return

    def observe(int_time): #dark sky calbrated snapshot
        vec=snapshot(int_time)
        wait(int_time)
        global darksky_exists
        if darksky_exists:
            calib=vec-darksky
            return calib
        else:
            print('Warning: No dark sky calibration has been performed.')
            return vec

    def wait(sec):
        pytime.sleep(sec)
        return

    def graphing(int_time, iter=float('inf')):
        plt.ion()
        plt.figure()
        vec=tb.get_variable_function_probe() #vector
        n=len(vec)
        x=np.linspace(flo, fhi, n)
        i=0
        while(i<iter):
            plt.pause(int_time)
            y=observe(int_time)
            plt.clf()
            plt.xlabel('Frequency (MHz)')
            plt.ylabel('Power (unit?)')
            plt.plot(x,y)
            plt.draw()
            i+=1
        return()

    def track(N):
        client.track(N)
    #runs in background

