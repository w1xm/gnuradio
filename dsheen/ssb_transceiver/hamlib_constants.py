# Constants from <hamlib/rig.h>, massaged to Python.

RIG_MODE_NONE =     0          # -- None
RIG_MODE_AM =       (1 << 0)   # AM -- Amplitude Modulation
RIG_MODE_CW =       (1 << 1)   # CW -- CW "normal" sideband
RIG_MODE_USB =      (1 << 2)   # USB -- Upper Side Band
RIG_MODE_LSB =      (1 << 3)   # LSB -- Lower Side Band
RIG_MODE_RTTY =     (1 << 4)   # RTTY -- Radio Teletype
RIG_MODE_FM =       (1 << 5)   # FM -- "narrow" band FM
RIG_MODE_WFM =      (1 << 6)   # WFM -- broadcast wide FM
RIG_MODE_CWR =      (1 << 7)   # CWR -- CW "reverse" sideband
RIG_MODE_RTTYR =    (1 << 8)   # RTTYR -- RTTY "reverse" sideband
RIG_MODE_AMS =      (1 << 9)   # AMS -- Amplitude Modulation Synchronous
RIG_MODE_PKTLSB =   (1 << 10)  # PKTLSB -- Packet/Digital LSB mode (dedicated port)
RIG_MODE_PKTUSB =   (1 << 11)  # PKTUSB -- Packet/Digital USB mode (dedicated port)
RIG_MODE_PKTFM =    (1 << 12)  # PKTFM -- Packet/Digital FM mode (dedicated port)
RIG_MODE_ECSSUSB =  (1 << 13)  # ECSSUSB -- Exalted Carrier Single Sideband USB
RIG_MODE_ECSSLSB =  (1 << 14)  # ECSSLSB -- Exalted Carrier Single Sideband LSB
RIG_MODE_FAX =      (1 << 15)  # FAX -- Facsimile Mode
RIG_MODE_SAM =      (1 << 16)  # SAM -- Synchronous AM double sideband
RIG_MODE_SAL =      (1 << 17)  # SAL -- Synchronous AM lower sideband
RIG_MODE_SAH =      (1 << 18)  # SAH -- Synchronous AM upper (higher) sideband
RIG_MODE_DSB =      (1 << 19)  # DSB -- Double sideband suppressed carrier
RIG_MODE_FMN =      (1 << 21)  # FMN -- FM Narrow Kenwood ts990s
RIG_MODE_PKTAM =    (1 << 22)  # PKTAM -- Packet/Digital AM mode e.g. IC7300

RIG_MODE_SSB = (RIG_MODE_USB|RIG_MODE_LSB)
RIG_MODE_ECSS = (RIG_MODE_ECSSUSB|RIG_MODE_ECSSLSB)

RIG_VFO_NONE =    0
RIG_VFO_TX_FLAG = (1<<30)
RIG_VFO_CURR =    (1<<29)
RIG_VFO_MEM =     (1<<28)
RIG_VFO_VFO =     (1<<27)
def RIG_VFO_TX_VFO(v): return ((v)|RIG_VFO_TX_FLAG)
RIG_VFO_TX =      RIG_VFO_TX_VFO(RIG_VFO_CURR)
RIG_VFO_RX =      RIG_VFO_CURR
RIG_VFO_MAIN =    (1<<26)
RIG_VFO_SUB =     (1<<25)
def RIG_VFO_N(n): return (1<<(n))
RIG_VFO_A =       RIG_VFO_N(0)
RIG_VFO_B =       RIG_VFO_N(1)
RIG_VFO_C =       RIG_VFO_N(2)

RIG_ANT_NONE =    0
def RIG_ANT_N(n): return (1<<(n))
RIG_ANT_1 =       RIG_ANT_N(0)
RIG_ANT_2 =       RIG_ANT_N(1)
RIG_ANT_3 =       RIG_ANT_N(2)
RIG_ANT_4 =       RIG_ANT_N(3)
RIG_ANT_5 =       RIG_ANT_N(4)

RIG_FUNC_NONE =    0          # -- No Function
RIG_FUNC_FAGC =    (1L<<0)    # FAGC -- Fast AGC
RIG_FUNC_NB =      (1L<<1)    # NB -- Noise Blanker
RIG_FUNC_COMP =    (1L<<2)    # COMP -- Speech Compression
RIG_FUNC_VOX =     (1L<<3)    # VOX -- Voice Operated Relay
RIG_FUNC_TONE =    (1L<<4)    # TONE -- CTCSS Tone
RIG_FUNC_TSQL =    (1L<<5)    # TSQL -- CTCSS Activate/De-activate
RIG_FUNC_SBKIN =   (1L<<6)    # SBKIN -- Semi Break-in (CW mode)
RIG_FUNC_FBKIN =   (1L<<7)    # FBKIN -- Full Break-in (CW mode)
RIG_FUNC_ANF =     (1L<<8)    # ANF -- Automatic Notch Filter (DSP)
RIG_FUNC_NR =      (1L<<9)    # NR -- Noise Reduction (DSP)
RIG_FUNC_AIP =     (1L<<10)   # AIP -- RF pre-amp (AIP on Kenwood, IPO on Yaesu, etc.)
RIG_FUNC_APF =     (1L<<11)   # APF -- Auto Passband/Audio Peak Filter
RIG_FUNC_MON =     (1L<<12)   # MON -- Monitor transmitted signal
RIG_FUNC_MN =      (1L<<13)   # MN -- Manual Notch
RIG_FUNC_RF =      (1L<<14)   # RF -- RTTY Filter
RIG_FUNC_ARO =     (1L<<15)   # ARO -- Auto Repeater Offset
RIG_FUNC_LOCK =    (1L<<16)   # LOCK -- Lock
RIG_FUNC_MUTE =    (1L<<17)   # MUTE -- Mute
RIG_FUNC_VSC =     (1L<<18)   # VSC -- Voice Scan Control
RIG_FUNC_REV =     (1L<<19)   # REV -- Reverse transmit and receive frequencies
RIG_FUNC_SQL =     (1L<<20)   # SQL -- Turn Squelch Monitor on/off
RIG_FUNC_ABM =     (1L<<21)   # ABM -- Auto Band Mode
RIG_FUNC_BC =      (1L<<22)   # BC -- Beat Canceller
RIG_FUNC_MBC =     (1L<<23)   # MBC -- Manual Beat Canceller
RIG_FUNC_RIT =     (1L<<24)   # RIT -- Receiver Incremental Tuning
RIG_FUNC_AFC =     (1L<<25)   # AFC -- Auto Frequency Control ON/OFF
RIG_FUNC_SATMODE = (1L<<26)   # SATMODE -- Satellite mode ON/OFF
RIG_FUNC_SCOPE =   (1L<<27)   # SCOPE -- Simple bandscope ON/OFF
RIG_FUNC_RESUME =  (1L<<28)   # RESUME -- Scan auto-resume
RIG_FUNC_TBURST =  (1L<<29)   # TBURST -- 1750 Hz tone burst
RIG_FUNC_TUNER =   (1L<<30)   # TUNER -- Enable automatic tuner
RIG_FUNC_XIT =     (1L<<31)   # XIT -- Transmitter Incremental Tuning

RIG_LEVEL_NONE =        0              # -- No Level
RIG_LEVEL_PREAMP =      (1 << 0)       # PREAMP -- Preamp, arg int (dB)
RIG_LEVEL_ATT =         (1 << 1)       # ATT -- Attenuator, arg int (dB)
RIG_LEVEL_VOX =         (1 << 2)       # VOX -- VOX delay, arg int (tenth of seconds)
RIG_LEVEL_AF =          (1 << 3)       # AF -- Volume, arg float [0.0 ... 1.0]
RIG_LEVEL_RF =          (1 << 4)       # RF -- RF gain (not TX power), arg float [0.0 ... 1.0]
RIG_LEVEL_SQL =         (1 << 5)       # SQL -- Squelch, arg float [0.0 ... 1.0]
RIG_LEVEL_IF =          (1 << 6)       # IF -- IF, arg int (Hz)
RIG_LEVEL_APF =         (1 << 7)       # APF -- Audio Peak Filter, arg float [0.0 ... 1.0]
RIG_LEVEL_NR =          (1 << 8)       # NR -- Noise Reduction, arg float [0.0 ... 1.0]
RIG_LEVEL_PBT_IN =      (1 << 9)       # PBT_IN -- Twin PBT (inside), arg float [0.0 ... 1.0]
RIG_LEVEL_PBT_OUT =     (1 << 10)      # PBT_OUT -- Twin PBT (outside), arg float [0.0 ... 1.0]
RIG_LEVEL_CWPITCH =     (1 << 11)      # CWPITCH -- CW pitch, arg int (Hz)
RIG_LEVEL_RFPOWER =     (1 << 12)      # RFPOWER -- RF Power, arg float [0.0 ... 1.0]
RIG_LEVEL_MICGAIN =     (1 << 13)      # MICGAIN -- MIC Gain, arg float [0.0 ... 1.0]
RIG_LEVEL_KEYSPD =      (1 << 14)      # KEYSPD -- Key Speed, arg int (WPM)
RIG_LEVEL_NOTCHF =      (1 << 15)      # NOTCHF -- Notch Freq., arg int (Hz)
RIG_LEVEL_COMP =        (1 << 16)      # COMP -- Compressor, arg float [0.0 ... 1.0]
RIG_LEVEL_AGC =         (1 << 17)      # AGC -- AGC, arg int (see enum agc_level_e)
RIG_LEVEL_BKINDL =      (1 << 18)      # BKINDL -- BKin Delay, arg int (tenth of dots)
RIG_LEVEL_BALANCE =     (1 << 19)      # BAL -- Balance (Dual Watch), arg float [0.0 ... 1.0]
RIG_LEVEL_METER =       (1 << 20)      # METER -- Display meter, arg int (see enum meter_level_e)
RIG_LEVEL_VOXGAIN =     (1 << 21)      # VOXGAIN -- VOX gain level, arg float [0.0 ... 1.0]
RIG_LEVEL_VOXDELAY =    RIG_LEVEL_VOX, # synonym of RIG_LEVEL_VOX
RIG_LEVEL_ANTIVOX =     (1 << 22)      # ANTIVOX -- anti-VOX level, arg float [0.0 ... 1.0]
RIG_LEVEL_SLOPE_LOW =   (1 << 23)      # SLOPE_LOW -- Slope tune, low frequency cut,
RIG_LEVEL_SLOPE_HIGH =  (1 << 24)      # SLOPE_HIGH -- Slope tune, high frequency cut,
RIG_LEVEL_BKIN_DLYMS =  (1 << 25)      # BKIN_DLYMS -- BKin Delay, arg int Milliseconds
# These are not settable
RIG_LEVEL_RAWSTR =      (1 << 26)      # RAWSTR -- Raw (A/D) value for signal strength, specific to each rig, arg int
RIG_LEVEL_SQLSTAT =     (1 << 27)      # SQLSTAT -- SQL status, arg int (open=1/closed=0). Deprecated, use get_dcd instead
RIG_LEVEL_SWR =         (1 << 28)      # SWR -- SWR, arg float [0.0 ... infinite]
RIG_LEVEL_ALC =         (1 << 29)      # ALC -- ALC, arg float
RIG_LEVEL_STRENGTH =    (1 << 30)      # STRENGTH -- Effective (calibrated) signal strength relative to S9, arg int (dB)

RIG_LEVEL_FLOAT_LIST = (RIG_LEVEL_AF|RIG_LEVEL_RF|RIG_LEVEL_SQL|RIG_LEVEL_APF|RIG_LEVEL_NR|RIG_LEVEL_PBT_IN|RIG_LEVEL_PBT_OUT|RIG_LEVEL_RFPOWER|RIG_LEVEL_MICGAIN|RIG_LEVEL_COMP|RIG_LEVEL_BALANCE|RIG_LEVEL_SWR|RIG_LEVEL_ALC|RIG_LEVEL_VOXGAIN|RIG_LEVEL_ANTIVOX)
RIG_LEVEL_READONLY_LIST = (RIG_LEVEL_SQLSTAT|RIG_LEVEL_SWR|RIG_LEVEL_ALC|RIG_LEVEL_STRENGTH|RIG_LEVEL_RAWSTR)
def RIG_LEVEL_IS_FLOAT(l): return ((l)&RIG_LEVEL_FLOAT_LIST)
def RIG_LEVEL_SET(l): return ((l)&~RIG_LEVEL_READONLY_LIST)

RIG_PARM_NONE =         0          # -- No Parm
RIG_PARM_ANN =          (1 << 0)   # ANN -- "Announce" level, see ann_t
RIG_PARM_APO =          (1 << 1)   # APO -- Auto power off, int in minute
RIG_PARM_BACKLIGHT =    (1 << 2)   # BACKLIGHT -- LCD light, float [0.0 ... 1.0]
RIG_PARM_BEEP =         (1 << 4)   # BEEP -- Beep on keypressed, int (0,1)
RIG_PARM_TIME =         (1 << 5)   # TIME -- hh:mm:ss, int in seconds from 00:00:00
RIG_PARM_BAT =          (1 << 6)   # BAT -- battery level, float [0.0 ... 1.0]
RIG_PARM_KEYLIGHT =     (1 << 7)   # KEYLIGHT -- Button backlight, on/off

RIG_PARM_FLOAT_LIST = (RIG_PARM_BACKLIGHT|RIG_PARM_BAT)
RIG_PARM_READONLY_LIST = (RIG_PARM_BAT)
def RIG_PARM_IS_FLOAT(l): return ((l)&RIG_PARM_FLOAT_LIST)
def RIG_PARM_SET(l): return ((l)&~RIG_PARM_READONLY_LIST)

RIG_ITU_REGION1 = 1
RIG_ITU_REGION2 = 2
RIG_ITU_REGION3 = 3
