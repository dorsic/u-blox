import os
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb, ubxhelpers
from datetime import datetime
from GnssTime import GnssTime

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
    survey_done_written = False

    def __init__(self, serialport='/dev/ttyS0', baudrate=115200, timeout=3, fn_timepulse=None, fn_pseudorange=None, fn_navsat=None, fn_clock=None, fn_svin=None):
        self.sport = Serial(serialport, baudrate=baudrate, timeout=timeout)
        self.ubr = UBXReader(self.sport)

        self.file = {'timepulse': fn_timepulse, 'pseudorange': fn_pseudorange, 'navsat': fn_navsat, 'clock': fn_clock, 'svin': fn_svin }
        self.file_mjd = int(GnssTime.now_tsmjd()[1])
        for f in self.file:
            if self.file[f]:
                self.file[f] = self.file[f][:-4] + '-' + str(self.file_mjd) + self.file[f][-4:]
                if not os.path.exists(self.file[f]):
                    self._writeheader(f, self.file[f])
                self.file[f] = open(self.file[f], 'a')
            
        self._nav_clock_missing = 0
        self._msg_nav_clock = None
        self._msg_tim_tp = None
        self._last_message = {}

    def exit(self):
        for f in self.file:
            if self.file[f]:
                self.file[f].close()
        exit(1)

    def _writeheader(self, type, filename):
        hdr = ''
        if type == 'timepulse':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'QERR', 'TIMEBASE', 'CLKBIAS', 'CLKDRIFT', 'TACC', 'FACC'])
        elif type == 'pseudorange':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'SAT', 'SIG', 'PSEUDORANGE', 'CARRIERPHASE', 'DOPPLER', 'CNO', 
                                'PRSTD', 'CPSTD', 'DOSTD', 'LOCKTIME', 'PRVALID', 'CPVALID', 'HALFCYC', 'SUBHALFCYC'])
        elif type == 'navsat':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'SAT', 'ELEV', 'AZIM', 'CNO', 'PRRES', 'QUALITYIND', 
                                'SVUSED', 'HEALTH', 'DIFFCORR', 'SMOOTHED', 'ORBITSOURCE', 'EPHAVAIL', 'ALMAVAIL', 'ANOAVAIL', 'AOPAVAIL',
                                'SBASCORRUSED', 'RTCMCORRUSED', 'SLASCORRUSED', 'SPARTNCORRUSED', 'PRCORRUSED', 'CRCORRUSED', 'DOCORRUSED'])
        elif type == 'clock':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'CLKBIAS', 'CLKDRIFT', 'TACC', 'FACC', 'GPSACC', 'GALACC', 'BDSACC', 'GLOACC', 'UTCACC'])
        elif type == 'svin':
            hdr = self.separator.join(['LCL', 'TS', 'MJD', 'DUR', 'MEANX', 'MEANY', 'MEANZ', 'MEANV', 'OBS', 'VALID', 'ACTIVE', 'RESERVED1'])
 
        with open(filename, 'w') as f:
            f.write(hdr+'\n')

    def _swap_mjd_files(self, mjd):
        self.file_mjd = mjd
        with open('extralogfile.txt', 'a') as flog:
            flog.write("looping files...\n")
            flog.flush()                    
            for f in self.file:
                if self.file[f]:
                    self.file[f].close()
                    flog.write("file closed. ")
                    flog.flush()
                    fname = f.split("-")[0] + '-' + str(mjd) + ".txt"
#                    self.file[f] = self.file[f][:-4] + '-' + str(mjd) + self.file[f][-4:]
                    flog.write(", set new filename")
                    flog.flush()
                    if not os.path.exists(fname):
                        self.file[f] = open(fname, 'a')
                        flog.write(", new file opened")
                        flog.flush()
                        ftype = None
                        for t in ['timepulse', 'pseudorange', 'navsat', 'clock' 'svin']:
                            if t in fname:
                                ftype = t
                                break
                        self._writeheader(ftype, self.file[f])
                        flog.write(", header written\n")
                        flog.flush()
                    else:
                        self.file[f] = open(fname, 'a')
                        flog.write(", new file opened\n")
                        flog.flush()

    @staticmethod
    def is_ubx_message(ubx_msg):
        return hasattr(ubx_msg, 'identity')

    # config file format from u-Center Generation 9 Advanced Configuration tool
    def apply_valset(self, layer, cmd, value, timeout=3):
        msg = UBXMessage.config_set(layer, ubxtypes_configdb.TXN_NONE, [(cmd, value)])
        self.sport.write(msg.serialize())
        st = datetime.now()
        while True:
            try:
                (raw_data, parsed_data) = self.ubr.read()
                if UBXLogger.is_ubx_message(parsed_data):                    
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
                if UBXLogger.is_ubx_message(parsed_data):
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

    # def log_tim_tp_nav_clock(self, msg):
    #     if (msg.identity not in ('TIM-TP', 'NAV-CLOCK')) or (not self.file['timepulse']):
    #         return
        
    #     if (msg.identity == 'TIM-TP'):
    #         self._msg_tim_tp = msg
    #         self._nav_clock_missing += 1
    #     if (msg.identity == 'NAV-CLOCK'):
    #         self._msg_nav_clock = msg
    #         self._nav_clock_missing = 0

    #     lts = GnssTime.now()
    #     if (self._msg_tim_tp and self._msg_nav_clock):
    #         ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
    #         mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
    #         tow = GnssTime.tow_fromts(ts)            
    #         if abs((self._msg_nav_clock.iTOW/1000.0)-tow) <= 1.0:
    #             tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
    #             output = self.separator.join(['{' + str(i) + '}' for i in range(8)])
    #             self.file['timepulse'].write((output + "\n").format(
    #                 lts, ts, mjd, self._msg_tim_tp.qErr, tb,
    #                 self._msg_nav_clock.clkB, self._msg_nav_clock.clkD, self._msg_nav_clock.tAcc, self._msg_nav_clock.fAcc))
    #             self._msg_tim_tp = None
    #     elif (msg.identity == 'TIM-TP' and self._nav_clock_missing > 3):
    #         ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
    #         mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
    #         tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
    #         output = self.separator.join(['{' + str(i) + '}' for i in range(4)])
    #         self.file['timepulse'].write((output + "\n").format(lts, ts, mjd, self._msg_tim_tp.qErr, tb))
    #         self._msg_tim_tp = None

    def log_nav_sat(self, args):
        try:
            if not self.file['navsat']:
                return
            msg = args[0]
            template = self.separator.join(['{' + str(i) + '}' for i in range(25)])
            for a in msg['sats']:
                self.file['navsat'].write((template + '\n').format(
                    msg['lts'], msg['ts'], msg['mjd'], a['sat'], a['elev'], a['azim'], a['cno'], 
                    a['prRes'], a['qualityInd'], a['svUsed'], a['health'], a['diffCorr'],
                    a['smoothed'], a['orbitSource'], a['ephAvail'], a['almAvail'], a['anoAvail'], a['aopAvail'], 
                    a['sbasCorrUsed'], a['rtcmCorrUsed'], a['slasCorrUsed'], a['spartnCorrUsed'], a['prCorrUsed'], a['prCorrUsed'], a['doCorrUsed']
            ))
            self.file['navsat'].flush()
        except:
            print("ERROR, log_nav_sat")
            pass

    def log_nav_clock(self, args):
        try:
            if not self.file['clock']:
                return
            msg = args[0]
            output = self.separator.join(['{' + str(i) + '}' for i in range(len(msg))])
            self.file['clock'].write((output + '\n').format( *msg.values() ))
        except:
            print("ERROR, log_nav_clock")
            pass

    def log_timepulse(self, args):
        if not self.file['timepulse']:
            return
        msg = args[0]
        if (self.file_mjd != int(msg['mjd'])):
            with open('extralogfile.txt', 'a') as f:
                f.write("swapping mjd files from ")
                f.flush()                    
                f.write(str(self.file_mjd))
                f.flush()
                f.write(" to " + str(int(msg['mjd'])) + "\n")
                f.flush()
                self._swap_mjd_files(int(msg['mjd']))
                f.write('Done.\n')

        template = self.separator.join(['{' + str(i) + '}' for i in range(5)])        
        self.file['timepulse'].write((template + '\n').format(
            msg['lts'], msg['ts'], msg['mjd'], msg['qerr'], msg['timebase']
        ))
        self.file['timepulse'].flush()
#    except:
#        print("ERROR, log_timepulse")
#        pass

    def log_rawx(self, args):
        try:
            if not self.file['pseudorange']:
                return
            msg = args[0]
            template = self.separator.join(['{' + str(i) + '}' for i in range(17)])        
            for a in msg['meas']:
                self.file['pseudorange'].write((template + '\n').format(
                    msg['lts'], msg['ts'], msg['mjd'], a['prn'], a['sig'], a['prMes'], a['cpMes'], a['doMes'], a['cno'],
                    a['prStd'], a['cpStd'], a['doStd'], a['locktime'], a['prValid'], a['cpValid'], a['halfCyc'], a['subHalfCyc']
                    )
                )
        except:
            print("ERROR, log_rawx")
            pass

    def log_survey_in(self, args):
        try:
            if self.survey_done_written:
                # after survey there is no change
                return

            msg = args[0]
            print(msg)
            print("Spatial deviation: {0:.3f} m".format((msg['meanV']**0.5)/1000.0))

            if not self.file['svin']:
                return
            template = self.separator.join(['{' + str(i) + '}' for i in range(12)])        
            self.file['svin'].write((template + '\n').format(
                msg['lts'], msg['ts'], msg['mjd'], msg['dur'], msg['meanX'], msg['meanY'], msg['meanZ'], msg['meanV'], 
                    msg['obs'], msg['valid'], msg['active'], msg['reserved1']
            ))
            self.file['svin'].flush()   # make the update immediately visible
        except:
            print("ERROR, log_survey_in")
            pass     

    def log_survey_done(self, args):
        if self.survey_done_written:
            return
        try:
            if not self.file['svin']:
                return

            msg_pvt = args[0]
            self.file['svin'].write(('# {0} \n').format(msg_pvt))
            self.file['svin'].flush()
            self.survey_done_written = True
        except:
            print("ERROR, log_survey_done")
            pass   
