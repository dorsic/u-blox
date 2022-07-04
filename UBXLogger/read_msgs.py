from curses import baudrate
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb, ubxhelpers
from datetime import datetime
from GnssTime import GnssTime
import os

configs = ['TP1.ubx_conf', 'OUT_MSG.ubx_conf']
f_timepulse = 'timepulse.txt'
f_rawx = 'rawx.txt'

class UBXLogger():
    ubr = None
    sport = None
    gnssPrefixMap = {0: 'G', 1: 'S', 2: 'E', 3: 'B', 5: 'Y', 5: 'J', 6: 'R'}
    utcStdMap = {0: 'UTC', 1: 'UTC(CRL)', 2: 'UTC(NIST)', 3: 'UTC(USNO)', 4: 'UTC(BIPM)', 5: 'UTC(EU)', 6: 'UTC(SU)', 15: 'UTC()'}
    sigMap = {0: 'G1C', 3: 'G2L', 4: 'G2S', 20: 'E1C', 21: 'E1B', 25: 'E7I', 26: 'E7Q', 
             30: 'B1D', 31: 'B1X', 32: 'B5D', 33: 'B7D',
             50: 'J1C', 54: 'J2S', 55: 'J2L',
             60: 'R1C', 62: 'R2C'}
    separator = '\t'

    def __init__(self, serialport='/dev/ttyS0', baudrate=115200, timeout=3, fn_timepulse=None, fn_pseudorange=None, fn_navsat=None):
        self.sport = Serial(serialport, baudrate=baudrate, timeout=timeout)
        self.ubr = UBXReader(self.sport)
        if fn_timepulse and not os.path.exists(fn_timepulse):
            self._writeheader('TIMEPULSE', fn_timepulse)
        if fn_pseudorange and not os.path.exists(fn_pseudorange):
            self._writeheader('PSEUDORANGE', fn_pseudorange)
        if fn_navsat and not os.path.exists(fn_navsat):
            self._writeheader('NAVSAT', fn_navsat)
        self.f_timepulse = open(fn_timepulse, 'a') if fn_timepulse else None
        self.f_pseudorange = open(fn_pseudorange, 'a') if fn_pseudorange else None
        self.f_navsat = open(fn_navsat, 'a') if fn_navsat else None
        self._nav_clock_missing = 0
        self._msg_nav_clock = None
        self._msg_tim_tp = None

    def exit(self):
        if self.f_timepulse:
             self.f_timepulse.close()
        if self.f_pseudorange:
            self.f_pseudorange.close()
        if self.f_navsat:
            self.f_navsat.close()
        exit(1)

    def _writeheader(self, type, filename):
        hdr = ''
        if type == 'TIMEPULSE':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'QERR', 'TIMEBASE', 'CLKBIAS', 'CLKDRIFT', 'TACC', 'FACC'])
        elif type == 'PSEUDORANGE':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'SAT', 'SIG', 'PSEUDORANGE', 'CARRIERPHASE', 'DOPPLER', 'CNO', 
                                'PRSTD', 'CPSTD', 'DOSTD', 'LOCKTIME', 'PRVALID', 'CPVALID', 'HALFCYC', 'SUBHALFCYC'])
        elif type == 'NAVSAT':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'SAT', 'ELEV', 'AZIM', 'CNO', 'PRRES', 'QUALITYIND', 
                                'SVUSED', 'HEALTH', 'DIFFCORR', 'SMOOTHED', 'ORBITSOURCE', 'EPHAVAIL', 'ALMAVAIL', 'ANOAVAIL', 'AOPAVAIL',
                                'SBASCORRUSED', 'RTCMCORRUSED', 'SLASCORRUSED', 'SPARTNCORRUSED', 'PRCORRUSED', 'CRCORRUSED', 'DOCORRUSED'])
        with open(filename, 'w') as f:
            f.write(hdr+'\n')

    # config file format from u-Center Generation 9 Advanced Configuration tool
    def apply_valset(self, layer, cmd, value, timeout=3):
        msg = UBXMessage.config_set(layer, ubxtypes_configdb.TXN_NONE, [(cmd, value)])
        self.sport.write(msg.serialize())
        st = datetime.now()
        while True:
            try:
                (raw_data, parsed_data) = self.ubr.read()
                if (parsed_data.identity == 'ACK-ACK'):
                    return True
                if (parsed_data.identity == 'ACK-NAK'):
                    return False
                if ((datetime.now()-st).seconds > timeout):
                    return False
            except KeyboardInterrupt:
                self.exit()   

    def apply_valdel(self, layer, cmd, timeout=3):
        msg = UBXMessage.config_del(layer, ubxtypes_configdb.TXN_NONE, [cmd])
        self.sport.write(msg.serialize())
        st = datetime.now()
        while True:
            try:
                (raw_data, parsed_data) = self.ubr.read()
                if (parsed_data.identity == 'ACK-ACK'):
                    return True
                if (parsed_data.identity == 'ACK-NAK'):
                    return False
                if ((datetime.now()-st).seconds > timeout):
                    return False
            except KeyboardInterrupt:
                self.exit()   

    def apply_configfile(self, config_filename):
        delcmd = {'RAM': [], 'BBR': [], 'Flash': []}
        setcmd = {'RAM': [], 'BBR': [], 'Flash': []}
        deleting = False
        with open(config_filename, 'r') as cf:
            for line in cf:
                try:
                    ln = line.strip()
                    if not ln:
                        continue
                    if ln.startswith('#'):
                        continue
                    if ln.startswith('[del]'):
                        deleting = True
                        continue
                    if ln.startswith('[set]'):
                        deleting = False
                        continue
                    cmd = ln.split('#')[0]
                    cmd = ' '.join(cmd.split()).split(' ')
                    cmd_id = cmd[1].replace('-', '_')
                    if not deleting:
                        cmd_val = int(cmd[2], 16)
                    if cmd[0] not in setcmd.keys():
                        print("wARNING> Ignoring config message ", cmd)
                    if deleting:
                        delcmd[cmd[0]].append(cmd_id)
                    else:
                        setcmd[cmd[0]].append((cmd_id, cmd_val))
                except:
                    print('ERROR in config file at line "', ln, '"')
                    exit(1)

        for layer, layer_id in [('Flash', ubxtypes_configdb.SET_LAYER_FLASH), ('BBR', ubxtypes_configdb.SET_LAYER_BBR), ('RAM', ubxtypes_configdb.SET_LAYER_RAM)]:
            for cmd in delcmd[layer]:
                if not self.apply_valdel(layer_id, cmd):
                    print("WARNING: Unable to del ", cmd, " in ", layer)
            for cmd in setcmd[layer]:
                if not self.apply_valset(layer_id, cmd[0], cmd[1]):
                    print("WARNING: Unable to set value ", cmd, " in ", layer)

    def _timebase(self, timebase, timeRefGnss, utcStandard):
        if timebase == 0:
            return ubxhelpers.gnss2str(timeRefGnss)
        if timebase == 1:
            return self.utcStdmap[utcStandard]
        return ''

    def log_tim_tp_nav_clock(self, msg):
        if (msg.identity not in ('TIM-TP', 'NAV-CLOCK')) or (not self.f_timepulse):
            return
        
        if (msg.identity == 'TIM-TP'):
            self._msg_tim_tp = msg
            self._nav_clock_missing += 1
        if (msg.identity == 'NAV-CLOCK'):
            self._msg_nav_clock = msg
            self._nav_clock_missing = 0

        lts = GnssTime.now()
        if (self._msg_tim_tp and self._msg_nav_clock):
            ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
            mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
            tow = GnssTime.tow_fromts(ts)            
            if abs((self._msg_nav_clock.iTOW/1000.0)-tow) <= 1.0:
                tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
                output = self.separator.join(['{' + str(i) + '}' for i in range(8)])
                self.f_timepulse.write((output + "\n").format(
                    lts, ts, mjd, self._msg_tim_tp.qErr, tb,
                    self._msg_nav_clock.clkB, self._msg_nav_clock.clkD, self._msg_nav_clock.tAcc, self._msg_nav_clock.fAcc))
                self._msg_tim_tp = None
        elif (msg.identity == 'TIM-TP' and self._nav_clock_missing > 3):
            ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
            mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
            tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
            output = self.separator.join(['{' + str(i) + '}' for i in range(4)])
            self.f_timepulse.write((output + "\n").format(lts, ts, mjd, self._msg_tim_tp.qErr, tb))
            self._msg_tim_tp = None

    def log_rxm_rawx(self, msg):
        if (msg.identity != 'RXM-RAWX') or (not self.f_pseudorange):
            return
        ts = GnssTime.timestamp(msg.week, msg.rcvTow*1000.0, 0) - msg.leapS
        mjd = GnssTime.mjd2(msg.week, msg.rcvTow*1000.0, 0) - msg.leapS/86400.0
        # msg.leapS, msg.leapSec
        lts = GnssTime.now()
        for i in range(1, msg.numMeas+1):
            si = "{0:02}".format(i)
            sig = self.sigMap[getattr(msg, "gnssId_"+si)*10+getattr(msg, "reserved2_"+si)]
            output = self.separator.join(['{' + str(i) + '}' for i in range(17)])
            output = output.replace(self.separator + '{4}', '{4:02}')
            self.f_pseudorange.write((output + '\n').format(    
                lts, ts, mjd, self.gnssPrefixMap[getattr(msg, "gnssId_"+si)], getattr(msg, "svId_"+si), sig,
                getattr(msg, "prMes_"+si), getattr(msg, "cpMes_"+si), getattr(msg, "doMes_"+si), getattr(msg, "cno_"+si),
                getattr(msg, "prStd_"+si), getattr(msg, "cpStd_"+si), getattr(msg, "doStd_"+si), getattr(msg, "locktime_"+si),
                getattr(msg, "prValid_"+si), getattr(msg, "cpValid_"+si), getattr(msg, "halfCyc_"+si), getattr(msg, "subHalfCyc_"+si)               
            ))

    def log_nav_sat(self, msg):
        if (msg.identity != 'NAV-SAT') or (not self.f_navsat):
            return
        lts = GnssTime.now()
        week = GnssTime.week_fromts(lts)
        ts = GnssTime.timestamp(week, msg.iTOW*1000.0, 0)   # - leapseconds???
        mjd = GnssTime.mjd2(week, msg.iTOW*1000.0, 0) # - leapseconds???    
        for i in range(1, msg.numSvs+1):
            si = "{0:02}".format(i)
            output = self.separator.join(['{' + str(i) + '}' for i in range(25)])
            output = output.replace(self.separator + '{4}', '{4:02}')
            self.f_navsat.write((output + '\n').format(    
                lts, ts, mjd, self.gnssPrefixMap[getattr(msg, "gnssId_"+si)], getattr(msg, "svId_"+si),
                getattr(msg, "elev_"+si), getattr(msg, "azim_"+si), getattr(msg, "cno_"+si), getattr(msg, "prRes_"+si), getattr(msg, "qualityInd_"+si),
                getattr(msg, "svUsed_"+si), getattr(msg, "health_"+si), getattr(msg, "diffCorr_"+si), getattr(msg, "smoothed_"+si), getattr(msg, "orbitSource_"+si),
                getattr(msg, "ephAvail_"+si), getattr(msg, "almAvail_"+si), getattr(msg, "anoAvail_"+si), getattr(msg, "aopAvail_"+si), 
                getattr(msg, "sbasCorrUsed_"+si), getattr(msg, "rtcmCorrUsed_"+si), getattr(msg, "slasCorrUsed_"+si), getattr(msg, "spartnCorrUsed_"+si),
                getattr(msg, "prCorrUsed_"+si), getattr(msg, "crCorrUsed_"+si), getattr(msg, "doCorrUsed_"+si)
            ))


ubxl = UBXLogger(fn_timepulse='timepulse.txt', fn_pseudorange="pseudorange.txt", fn_navsat='navsat.txt')

for cfg in configs:
    ubxl.apply_configfile(cfg)

while True:
    try:
        (raw_data, parsed_data) = ubxl.ubr.read()
        msg = parsed_data
        print(msg.identity)
        ubxl.log_tim_tp_nav_clock(msg)
        ubxl.log_rxm_rawx(msg)
        ubxl.log_nav_sat(msg)
        if msg.identity in ('NAV-SAT'):
            print(msg)
#       #print(parsed_data)
    except KeyboardInterrupt:
        ubxl.exit()
