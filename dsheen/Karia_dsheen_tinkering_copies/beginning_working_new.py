import numpy as np
import matplotlib as mpl
mpl.use('Agg')
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
client = rci.client.Client()
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
# Generated: Mon Aug 20 14:28:17 2018
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
from optparse import OptionParser
import limesdr
import numpy as np
import sys
import threading
import time


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
        self.if_bandwidth_1 = if_bandwidth_1 = 2e6
        self.sdr_gain = sdr_gain = 60
        self.integration_bandwidth = integration_bandwidth = 5e3
        self.if_filter_decimation_rate = if_filter_decimation_rate = int(samp_rate/(1.1*if_bandwidth_1))
        self.sdr_power_offset = sdr_power_offset = 1.0
        self.sdr_gain_lin = sdr_gain_lin = 10**(sdr_gain/20)
        self.num_channels = num_channels = int((samp_rate/if_filter_decimation_rate)/integration_bandwidth)
        self.lna_gain_measured = lna_gain_measured = 33.33
        self.integration_time = integration_time = 10
        self.if_samp_rate = if_samp_rate = samp_rate/if_filter_decimation_rate
        self.cable_loss = cable_loss = 0.25
        self.variable_function_probe = variable_function_probe = 0
        self.sdr_frequency = sdr_frequency = 1420.406e6
        self.output_vector_bandwidth = output_vector_bandwidth = samp_rate/if_filter_decimation_rate
        self.offset_frequency = offset_frequency = if_bandwidth_1/2+1e5
        self.integration_scale_factor = integration_scale_factor = np.full((num_channels),float(1.0/(integration_time*integration_bandwidth*50)),dtype=float)
        self.integration_dec_rate = integration_dec_rate = int(integration_time*if_samp_rate/num_channels)
        self.if_filter_gain = if_filter_gain = 1/(lna_gain_measured*cable_loss*sdr_gain_lin*sdr_power_offset)
        self.if_bandwidth_0 = if_bandwidth_0 = 5.5e6
        self.channel_skirt = channel_skirt = integration_bandwidth/100
        self.channel_map = channel_map = range(int(num_channels/2.0+1.0),num_channels,1)+range(0,int(num_channels/2.0+1.0),1)
        self.antenna_gain_estimated = antenna_gain_estimated = 173

        ##################################################
        # Blocks
        ##################################################
        self.probe_signal = blocks.probe_signal_vf(num_channels)
        
        def _variable_function_probe_probe():
            while True:
                val = self.probe_signal.level()
                try:
                    self.set_variable_function_probe(val)
                except AttributeError:
                    pass
                time.sleep(1.0 / (10))
        _variable_function_probe_thread = threading.Thread(target=_variable_function_probe_probe)
        _variable_function_probe_thread.daemon = True
        _variable_function_probe_thread.start()
            
        self.pfb_channelizer_ccf_0 = pfb.channelizer_ccf(
              num_channels,
              (firdes.low_pass(1, if_samp_rate, (integration_bandwidth/2-channel_skirt), channel_skirt, firdes.WIN_HAMMING)),
              1.0,
              0)
        self.pfb_channelizer_ccf_0.set_channel_map((channel_map))
        self.pfb_channelizer_ccf_0.declare_sample_delay(0)
            
        self.low_pass_filter_1 = filter.fir_filter_ccf(if_filter_decimation_rate, firdes.low_pass(
            if_filter_gain, samp_rate, if_bandwidth_1/2, 1e5, firdes.WIN_HAMMING, 6.76))
        self.limesdr_source_2 = limesdr.source('0009060B00471B22', 0, '')
        self.limesdr_source_2.set_sample_rate(samp_rate)
        self.limesdr_source_2.set_center_freq(sdr_frequency-offset_frequency, 0)
        self.limesdr_source_2.set_bandwidth(if_bandwidth_0, 0)
        self.limesdr_source_2.set_digital_filter(if_bandwidth_0, 0)
        self.limesdr_source_2.set_gain(sdr_gain, 0)
        self.limesdr_source_2.set_antenna(2, 0)
        self.limesdr_source_2.calibrate(samp_rate, 0)

        self.blocks_streams_to_vector_0 = blocks.streams_to_vector(gr.sizeof_gr_complex*1, num_channels)
        self.blocks_multiply_xx_1 = blocks.multiply_vcc(1)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((integration_scale_factor))
        self.blocks_integrate_xx_0_0 = blocks.integrate_ff(integration_dec_rate, num_channels)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'receive_block_sink', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_copy_0_0 = blocks.copy(gr.sizeof_gr_complex*1)
        self.blocks_copy_0_0.set_enabled(False)
        self.blocks_copy_0 = blocks.copy(gr.sizeof_gr_complex*1)
        self.blocks_copy_0.set_enabled(True)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(num_channels)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_SIN_WAVE, -offset_frequency, 1, 0)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_1, 1))    
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_integrate_xx_0_0, 0))    
        self.connect((self.blocks_copy_0, 0), (self.blocks_multiply_xx_1, 0))    
        self.connect((self.blocks_copy_0_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.blocks_integrate_xx_0_0, 0), (self.blocks_multiply_const_vxx_0, 0))    
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.probe_signal, 0))    
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
        self.set_num_channels(int((self.samp_rate/self.if_filter_decimation_rate)/self.integration_bandwidth))
        self.set_if_filter_decimation_rate(int(self.samp_rate/(1.1*self.if_bandwidth_1)))
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, (self.samp_rate/self.if_filter_decimation_rate), (self.integration_bandwidth/2-self.channel_skirt), self.channel_skirt, firdes.WIN_HAMMING)))
        self.set_output_vector_bandwidth(self.samp_rate/self.if_filter_decimation_rate)
        self.low_pass_filter_1.set_taps(firdes.low_pass(self.if_filter_gain, self.samp_rate, self.if_bandwidth_1/2, self.if_bandwidth_1/100, firdes.WIN_HAMMING, 6.76))
        self.set_if_samp_rate(self.samp_rate/self.if_filter_decimation_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_if_bandwidth_1(self):
        return self.if_bandwidth_1

    def set_if_bandwidth_1(self, if_bandwidth_1):
        self.if_bandwidth_1 = if_bandwidth_1
        self.set_offset_frequency(self.if_bandwidth_1/2+1e5)
        self.set_if_filter_decimation_rate(int(self.samp_rate/(1.1*self.if_bandwidth_1)))
        self.low_pass_filter_1.set_taps(firdes.low_pass(self.if_filter_gain, self.samp_rate, self.if_bandwidth_1/2, self.if_bandwidth_1/100, firdes.WIN_HAMMING, 6.76))

    def get_sdr_gain(self):
        return self.sdr_gain

    def set_sdr_gain(self, sdr_gain):
        self.sdr_gain = sdr_gain
        self.set_sdr_gain_lin(10**(self.sdr_gain/10))
        self.limesdr_source_2.set_gain(self.sdr_gain,0)

    def get_integration_bandwidth(self):
        return self.integration_bandwidth

    def set_integration_bandwidth(self, integration_bandwidth):
        self.integration_bandwidth = integration_bandwidth
        self.set_num_channels(int((self.samp_rate/self.if_filter_decimation_rate)/self.integration_bandwidth))
        self.set_channel_skirt(self.integration_bandwidth/100)
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, (self.samp_rate/self.if_filter_decimation_rate), (self.integration_bandwidth/2-self.channel_skirt), self.channel_skirt, firdes.WIN_HAMMING)))

    def get_if_filter_decimation_rate(self):
        return self.if_filter_decimation_rate

    def set_if_filter_decimation_rate(self, if_filter_decimation_rate):
        self.if_filter_decimation_rate = if_filter_decimation_rate
        self.set_num_channels(int((self.samp_rate/self.if_filter_decimation_rate)/self.integration_bandwidth))
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, (self.samp_rate/self.if_filter_decimation_rate), (self.integration_bandwidth/2-self.channel_skirt), self.channel_skirt, firdes.WIN_HAMMING)))
        self.set_output_vector_bandwidth(self.samp_rate/self.if_filter_decimation_rate)
        self.set_if_samp_rate(self.samp_rate/self.if_filter_decimation_rate)

    def get_sdr_power_offset(self):
        return self.sdr_power_offset

    def set_sdr_power_offset(self, sdr_power_offset):
        self.sdr_power_offset = sdr_power_offset
        self.set_if_filter_gain(1/(self.lna_gain_measured*self.cable_loss*self.sdr_gain_lin*self.sdr_power_offset))

    def get_sdr_gain_lin(self):
        return self.sdr_gain_lin

    def set_sdr_gain_lin(self, sdr_gain_lin):
        self.sdr_gain_lin = sdr_gain_lin
        self.set_if_filter_gain(1/(self.lna_gain_measured*self.cable_loss*self.sdr_gain_lin*self.sdr_power_offset))

    def get_num_channels(self):
        return self.num_channels

    def set_num_channels(self, num_channels):
        self.num_channels = num_channels
        self.set_integration_scale_factor(np.full((self.num_channels),float(1.0/(self.integration_time*50)),dtype=float))
        self.set_integration_dec_rate(int(self.integration_time*self.if_samp_rate/self.num_channels))
        self.set_channel_map(range(int(self.num_channels/2.0+1.0),self.num_channels,1)+range(0,int(self.num_channels/2.0+1.0),1))

    def get_lna_gain_measured(self):
        return self.lna_gain_measured

    def set_lna_gain_measured(self, lna_gain_measured):
        self.lna_gain_measured = lna_gain_measured
        self.set_if_filter_gain(1/(self.lna_gain_measured*self.cable_loss*self.sdr_gain_lin*self.sdr_power_offset))

    def get_integration_time(self):
        return self.integration_time

    def set_integration_time(self, integration_time):
        self.integration_time = integration_time
        self.set_integration_scale_factor(np.full((self.num_channels),float(1.0/(self.integration_time*50)),dtype=float))
        self.set_integration_dec_rate(int(self.integration_time*self.if_samp_rate/self.num_channels))

    def get_if_samp_rate(self):
        return self.if_samp_rate

    def set_if_samp_rate(self, if_samp_rate):
        self.if_samp_rate = if_samp_rate
        self.set_integration_dec_rate(int(self.integration_time*self.if_samp_rate/self.num_channels))

    def get_cable_loss(self):
        return self.cable_loss

    def set_cable_loss(self, cable_loss):
        self.cable_loss = cable_loss
        self.set_if_filter_gain(1/(self.lna_gain_measured*self.cable_loss*self.sdr_gain_lin*self.sdr_power_offset))

    def get_variable_function_probe(self):
        return self.variable_function_probe

    def set_variable_function_probe(self, variable_function_probe):
        self.variable_function_probe = variable_function_probe

    def get_sdr_frequency(self):
        return self.sdr_frequency

    def set_sdr_frequency(self, sdr_frequency):
        self.sdr_frequency = sdr_frequency
        self.limesdr_source_2.set_rf_freq(self.sdr_frequency-self.offset_frequency)

    def get_output_vector_bandwidth(self):
        return self.output_vector_bandwidth

    def set_output_vector_bandwidth(self, output_vector_bandwidth):
        self.output_vector_bandwidth = output_vector_bandwidth

    def get_offset_frequency(self):
        return self.offset_frequency

    def set_offset_frequency(self, offset_frequency):
        self.offset_frequency = offset_frequency
        self.limesdr_source_2.set_rf_freq(self.sdr_frequency-self.offset_frequency)
        self.analog_sig_source_x_0.set_frequency(-self.offset_frequency)

    def get_integration_scale_factor(self):
        return self.integration_scale_factor

    def set_integration_scale_factor(self, integration_scale_factor):
        self.integration_scale_factor = integration_scale_factor
        self.blocks_multiply_const_vxx_0.set_k((self.integration_scale_factor))

    def get_integration_dec_rate(self):
        return self.integration_dec_rate

    def set_integration_dec_rate(self, integration_dec_rate):
        self.integration_dec_rate = integration_dec_rate

    def get_if_filter_gain(self):
        return self.if_filter_gain

    def set_if_filter_gain(self, if_filter_gain):
        self.if_filter_gain = if_filter_gain
        self.low_pass_filter_1.set_taps(firdes.low_pass(self.if_filter_gain, self.samp_rate, self.if_bandwidth_1/2, self.if_bandwidth_1/100, firdes.WIN_HAMMING, 6.76))

    def get_if_bandwidth_0(self):
        return self.if_bandwidth_0

    def set_if_bandwidth_0(self, if_bandwidth_0):
        self.if_bandwidth_0 = if_bandwidth_0
        self.limesdr_source_2.set_analog_filter(1,self.if_bandwidth_0,0)
        self.limesdr_source_2.set_digital_filter(1,self.if_bandwidth_0,0)

    def get_channel_skirt(self):
        return self.channel_skirt

    def set_channel_skirt(self, channel_skirt):
        self.channel_skirt = channel_skirt
        self.pfb_channelizer_ccf_0.set_taps((firdes.low_pass(1, (self.samp_rate/self.if_filter_decimation_rate), (self.integration_bandwidth/2-self.channel_skirt), self.channel_skirt, firdes.WIN_HAMMING)))

    def get_channel_map(self):
        return self.channel_map

    def set_channel_map(self, channel_map):
        self.channel_map = channel_map
        self.pfb_channelizer_ccf_0.set_channel_map((self.channel_map))

    def get_antenna_gain_estimated(self):
        return self.antenna_gain_estimated

    def set_antenna_gain_estimated(self, antenna_gain_estimated):
        self.antenna_gain_estimated = antenna_gain_estimated

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
            plt.ylabel('Scaled power')
            plt.axvline(x=1420.406, color='black', ls='--')
            plt.ticklabel_format(useOffset=False)
            plt.plot(x,y)
            plt.draw()
            i+=1
        return()

    def track(N):
        client.track(N)
    #runs in background

