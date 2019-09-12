import logging
import SocketServer
import time
from rci import client

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
                # RX Freq ranges
                self.wfile.write("0 0 0 0 0 0 0\n") # End of RX freq range list
                # TX Freq ranges
                self.wfile.write("0 0 0 0 0 0 0\n") # End of TX freq range list
                # Tuning step size
                self.wfile.write("0 0\n") # End of tuning step list
                # Filter list
                self.wfile.write("0 0\n") # End of filter list
                self.wfile.write("0\n") # max RIT
                self.wfile.write("0\n") # max XIT
                self.wfile.write("0\n") # max ifshift
                self.wfile.write("0\n") # announces
                self.wfile.write("0 \n") # Preamp gains list
                self.wfile.write("0 \n") # Attenuator losses list
                for value in (
                        0, # has_get_func
                        0, # has_set_func
                        0, # has_get_level
                        0, # has_set_level
                        0, # has_get_parm
                        0, # has_set_parm
                        ):
                    self.wfile.write("0x%x\n" % value)
                rprt = 0
            elif cmd in ("1", "dump_caps"):
                self.wfile.write("""Model name: ShinySDR
    Mfg name: ShinySDR
    Rig type: Other
    Can set Frequency: Y
    Can get Frequency: Y
    Can set PTT: Y
    Can get PTT: Y
    """)
                rprt = 0
            elif cmd in ("v", "get_vfo"):
                self.wfile.write("VFO\n")
                rprt = 0
            elif cmd in ("s", "get_split"):
                self.wfile.write("0\nVFO\n")
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
            elif cmd == "q":
                return
            if send_rprt:
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
    
    def __init__(self, tb, signal):
        self.tb = tb
        self.signal = signal
        SocketServer.TCPServer.__init__(self, ("localhost", 4532), RigctlHandler)
        self.rci = client.Client()

if __name__ == "__main__":
    # Create the server, binding to localhost on port 4532
    server = RigctlServer(None)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
