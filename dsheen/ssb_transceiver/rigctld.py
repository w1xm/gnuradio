import logging
import SocketServer
import math
import time
from rci import client
import hamlib_constants
from hamlib_constants import *

class RigctlHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while True:
            cmd = self.rfile.readline().strip()
            args = []
            if len(cmd) == 0:
                continue
            send_rprt = True
            # Two forms of command: single character, or "+\" followed by command name.
            if len(cmd) > 1 and cmd[0] == "\\":
                parts = cmd.split(" ")
                cmd = parts[0][1:]
                if len(parts) > 1:
                    args = parts[1:]
                send_rprt = False
            elif len(cmd) > 2 and cmd[0:2] == "+\\":
                parts = cmd.split(" ")
                cmd = parts[0][2:]
                if len(parts) > 1:
                    args = parts[1:]
                self.wfile.write("%s:\n" % cmd)
            else:
                # Space after command is optional.
                if len(cmd) > 1:
                    args = cmd[1:].lstrip(' ').split(' ')
                cmd = cmd[0]
                send_rprt = False
            logging.info("command: %s args: %s", cmd, args)
            rprt = -1
            if cmd == "dump_state":
                self.wfile.write("0\n") # Protocol version
                self.wfile.write("1\n") # Rig model
                self.wfile.write("2\n") # ITU region
                FREQ_RANGE_FMT = "%(startf)lf %(endf)lf %(modes)lx %(low_power)d %(high_power)d %(vfo)x %(ant)x\n"
                # RX Freq ranges
                # startf endf modes low_power high_power vfo ant
                # %lf    %lf  %llx  %d        %d         %x  %x
                self.wfile.write(FREQ_RANGE_FMT % {
                    'startf': 1280e6,
                    'endf': 1300e6,
                    'modes': RIG_MODE_USB,
                    'low_power': -1,
                    'high_power': -1,
                    'vfo': RIG_VFO_A, # VFOA only
                    'ant': RIG_ANT_1, # Antenna 1 only
                })
                self.wfile.write("0 0 0 0 0 0 0\n") # End of RX freq range list
                # TX Freq ranges
                self.wfile.write(FREQ_RANGE_FMT % {
                    'startf': 1280e6,
                    'endf': 1300e6,
                    'modes': RIG_MODE_USB,
                    'low_power': 1,
                    'high_power': 100000,
                    'vfo': RIG_VFO_A, # VFOA only
                    'ant': RIG_ANT_1, # Antenna 1 only
                })
                self.wfile.write("0 0 0 0 0 0 0\n") # End of TX freq range list
                # Tuning step size
                self.wfile.write("%lx %ld\n" % (RIG_MODE_USB, 1)) # USB allows 1 Hz tuning
                self.wfile.write("0 0\n") # End of tuning step list
                # Filter list
                self.wfile.write("0 0\n") # End of filter list
                self.wfile.write("0\n") # max RIT
                self.wfile.write("0\n") # max XIT
                self.wfile.write("0\n") # max ifshift
                self.wfile.write("0\n") # announces
                self.wfile.write("10 20 30 40 50 60 70 0 \n") # Preamp gains list
                self.wfile.write("0 \n") # Attenuator losses list
                get_levels = RIG_LEVEL_PREAMP|RIG_LEVEL_AF|RIG_LEVEL_MICGAIN
                if self.server.has_level_strength():
                    get_levels |= RIG_LEVEL_STRENGTH
                for value in (
                        RIG_FUNC_NONE, # has_get_func
                        RIG_FUNC_NONE, # has_set_func
                        get_levels, # has_get_level
                        RIG_LEVEL_PREAMP|RIG_LEVEL_AF|RIG_LEVEL_MICGAIN, # has_set_level
                        RIG_PARM_NONE, # has_get_parm
                        RIG_PARM_NONE, # has_set_parm
                        ):
                    self.wfile.write("0x%x\n" % value)
                # TODO: Support RIG_LEVEL_RF (float 0-1)
                rprt = 0
            elif cmd in ("1", "dump_caps"):
                self.wfile.write("""Model name: ShinySDR
    Mfg name: ShinySDR
    Rig type: Other
    Can set Frequency: Y
    Can get Frequency: Y
    Can get Mode: Y
    Can get VFO: Y
    Can set PTT: Y
    Can get PTT: Y
    Can set Level: Y
    Can get Level: Y
    """)
                rprt = 0
            elif cmd in ("v", "get_vfo"):
                self.wfile.write("VFOA\n")
                rprt = 0
            elif cmd in ("s", "get_split"):
                self.wfile.write("0\nVFOA\n")
                rprt = 0
            elif cmd in ("m", "get_mode"):
                self.wfile.write("USB\n15000\n")
                rprt = 0
            elif cmd in ("f", "get_freq"):
                freq = self.server.get_freq()
                logging.info("freq = %f", freq)
                self.wfile.write("%d\n" % freq)
                rprt = 0
            elif cmd in ("F", "set_freq"):
                if len(args) != 1:
                    rprt = -22
                else:
                    freq = float(args[0])
                    self.server.set_freq(freq)
                    rprt = 0
                send_rprt = True
            elif cmd in ("t", "get_ptt"):
                # 0 = RX, 1 = TX
                self.wfile.write("%d\n" % self.server.get_ptt())
                rprt = 0
            elif cmd in ("T", "set_ptt"):
                if len(args) != 1:
                    rprt = -22
                else:
                    if int(args[0]) > 0:
                        self.server.set_ptt(True)
                    else:
                        self.server.set_ptt(False)
                    rprt = 0
                send_rprt = True
            elif cmd in ("l", "get_level"):
                if len(args) != 1:
                    rprt = -22
                else:
                    rprt = -1
                    func = getattr(self.server, "get_level_"+args[0].lower())
                    if func:
                        fmt = "%d\n"
                        if RIG_LEVEL_IS_FLOAT(getattr(hamlib_constants, "RIG_LEVEL_"+args[0].upper(), 0)):
                            fmt = "%f\n"
                        self.wfile.write(fmt % func())
                        rprt = 0
            elif cmd in ("L", "set_level"):
                if len(args) != 2:
                    rprt = -22
                else:
                    rprt = -1
                    func = getattr(self.server, "set_level_"+args[0].lower())
                    if func:
                        conv = int
                        if RIG_LEVEL_IS_FLOAT(getattr(hamlib_constants, "RIG_LEVEL_"+args[0].upper(), 0)):
                            conv = float
                        func(conv(args[1]))
                        rprt = 0
                send_rprt = True
            elif cmd == "q":
                return
            if rprt != 0 or send_rprt:
                self.wfile.write("RPRT %d\n" % rprt)

class RigctlServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def set_freq(self, freq):
        self.signal.set_RF_frequency.emit(freq)

    def get_freq(self):
        return self.tb.get_RF_frequency()

    def set_ptt(self, ptt):
        self.signal.set_ptt_command.emit(ptt)

    def get_ptt(self):
        return self.tb.get_ptt_command()

    def get_level_preamp(self):
        return self.tb.get_rx_gain()

    def set_level_preamp(self, gain):
        self.signal.set_rx_gain.emit(gain)

    def get_level_af(self):
        return self.tb.get_volume()

    def set_level_af(self, volume):
        self.signal.set_volume.emit(volume)

    def get_level_micgain(self):
        return self.tb.get_mic_gain() / 10

    def set_level_micgain(self, gain):
        self.signal.set_mic_gain.emit(gain * 10)

    def has_level_strength(self):
        return hasattr(self.tb, 'audio_mag_sqrd')

    def get_level_strength(self):
        if not self.has_level_strength():
            return 0
        # RIG_LEVEL_STRENGTH is relative to S9 or -79 dBm (S0 = -127 dBm)
        # Our noise floor is at -110 dB/Hz which shows up as -75 dB in audio_mag_sqrd.level()
        # Absent a real calibration, we'll just set -75 dBFS to S0.
        return int(10 * math.log10(self.tb.audio_mag_sqrd.level())) + 27
    
    def __init__(self, tb, signal):
        self.tb = tb
        self.signal = signal
        SocketServer.TCPServer.__init__(self, ("localhost", 4532), RigctlHandler)
        client_name = None
        try:
            client_name = open("client_name.txt", "r").read().strip()
        except IOError:
            pass
        self.rci = client.Client(client_name=client_name)

if __name__ == "__main__":
    # Create the server, binding to localhost on port 4532
    server = RigctlServer(None)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
