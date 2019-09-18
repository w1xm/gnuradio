#!/usr/bin/env python2
import sys
import logging
import threading
import top_block
import rigctld
from PyQt4 import Qt, QtCore
from gnuradio import gr

class Signal(QtCore.QObject):
    set_RF_frequency = QtCore.pyqtSignal(int)
    set_ptt_command = QtCore.pyqtSignal(bool)
    set_rx_gain = QtCore.pyqtSignal(int)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(levelname)s %(message)s")
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable real-time scheduling."

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block.top_block()
    tb.start()
    tb.show()
    signal = Signal()
    signal.set_RF_frequency.connect(tb.set_RF_frequency)
    signal.set_ptt_command.connect(tb.set_ptt_command)
    signal.set_rx_gain.connect(tb.set_rx_gain)
    s = rigctld.RigctlServer(tb, signal)
    t = threading.Thread(target=s.serve_forever)
    t.daemon = True
    t.start()

    def quitting():
        s.shutdown()
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()
