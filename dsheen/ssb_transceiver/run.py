#!/usr/bin/env python2
import sys
import signal
import logging
import threading
import top_block
import rigctld
from rci import client
from PyQt5 import Qt, QtCore
from gnuradio import gr

class Signal(QtCore.QObject):
    set_RF_frequency = QtCore.pyqtSignal(int)
    set_ptt_command = QtCore.pyqtSignal(bool)
    set_rx_gain = QtCore.pyqtSignal(int)
    set_volume = QtCore.pyqtSignal(float)
    set_mic_gain = QtCore.pyqtSignal(float)

class top_block(top_block.top_block):
    def __init__(self):
        super(top_block, self).__init__()
        self._client = client.Client()

    def set_ptt_command(self, ptt):
        with self._lock:
            if ptt != self.get_ptt_command():
                super(top_block, self).set_ptt_command(ptt)
                if ptt:
                    try:
                        self._client.set_band_tx(0, True)
                    except IOError as e:
                        logging.exception("failed to enable tx")
                    else:
                        self.set_ptt_allowed(1)
                else:
                    self.set_ptt_allowed(0)
                    self._client.set_band_rx(0, True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format="%(asctime)-15s %(levelname)s %(message)s")
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable real-time scheduling."

    from distutils.version import StrictVersion
    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)
    if "-v" in sys.argv:
        logging.getLogger().setLevel(logging.INFO)

    tb = top_block()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    signal = Signal()
    signal.set_RF_frequency.connect(tb.set_RF_frequency, type=QtCore.Qt.BlockingQueuedConnection)
    signal.set_ptt_command.connect(tb.set_ptt_command, type=QtCore.Qt.BlockingQueuedConnection)
    signal.set_rx_gain.connect(tb.set_rx_gain, type=QtCore.Qt.BlockingQueuedConnection)
    signal.set_volume.connect(tb.set_volume, type=QtCore.Qt.BlockingQueuedConnection)
    signal.set_mic_gain.connect(tb.set_mic_gain, type=QtCore.Qt.BlockingQueuedConnection)
    s = rigctld.RigctlServer(tb, signal)
    t = threading.Thread(target=s.serve_forever)
    t.daemon = True
    t.start()

    def quitting():
        s.shutdown()
        tb.stop()
        tb.wait()
    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()
