from astropy import units as u
import aprslib
import logging
import requests
import threading
from xml.etree import ElementTree

class Weather:
    logger = logging.getLogger('weather')

    def __init__(self, callback, station="KB1DML"):
        self.callback = callback
        self.station = station
        try:
            self._fetch_latest()
        except:
            self.logger.exception('fetching latest observation')
        logging.getLogger('aprslib.parsing').setLevel(logging.INFO)
        logging.getLogger('aprslib.inet.IS').setLevel(logging.INFO)
        logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)
        logging.getLogger('chardet.universaldetector').setLevel(logging.INFO)

    def start(self):
        self.ais = aprslib.IS("W1XM-RT", host="cwop.mesowest.org", port=30010)
        self.ais.set_filter("b/"+self.station)
        self.wx_thread = threading.Thread(target=self._run, name="weather", daemon=True)
        self.wx_thread.start()

    def _run(self):
        # TODO: Exit thread gracefully
        while True:
            self.ais.connect(blocking=True)
            try:
                self.ais.consumer(self._rx_packet)
            except (aprslib.ConnectionDrop, aprslib.ConnectionError):
                pass
            finally:
                self.ais.close()

    def _rx_packet(self, packet):
        # Unfortuately, the CWOP server does not actually support server-side filters, so we need to filter here as well.
        if packet.get("from") != self.station:
            return
        if "weather" not in packet:
            self.logger.debug("Ignoring non-weather packet %s", packet)
            return
        wx = packet["weather"]
        self.logger.debug("Received weather packet %s", packet)
        self.callback({
            'temperature': wx['temperature']*u.Celsius,
            'relative_humidity': wx['humidity']/100,
            'pressure': wx['pressure']*u.mbar,
        })

    def _fetch_latest(self):
        resp = requests.get("http://www.findu.com/cgi-bin/wxxml.cgi?last=1", {'call': self.station})
        try:
            resp.raise_for_status()
        except:
            self.logger.exception('fetching latest observations')
            return
        xml = ElementTree.XML(resp.text)
        report = xml.find("weatherReport")
        self.callback({
            'temperature': (
                int(report.find("temperature").text)*u.imperial.Fahrenheit
            ).to(u.Celsius, u.equivalencies.temperature()),
            'relative_humidity': int(report.find("humidity").text)/100,
            'pressure': float(report.find("barometer").text)*u.mbar,
        })

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    def callback(wx):
        print(wx)
    w = Weather(callback)
    w.start()
    w.wx_thread.join()
