#!/usr/bin/env python2
import sys
import logging
import threading
import top_block
import rigctld
from PyQt4 import Qt, QtCore
from gnuradio import gr

#class Signal(QtCore.QObject):
#    set_freq = QtCore.pyqtSignal(int)

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
#    signal = Signal()
#    signal.set_freq.connect(tb.set_freq)
    def runRigctld():
        s = rigctld.RigctlServer(tb)#, signal.set_freq.emit)
        s.serve_forever()
    t = threading.Thread(target=runRigctld)
    t.daemon = True
    t.start()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()
