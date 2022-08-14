import os
from GnssTime import GnssTime

class UbloxLogFile():
    ftype = 'general'
    delim = '\t'
    _f = None
    _mjd = 0
    _fname = None
    _template = None

    def __init__(self, ftype, columns, dir='./', delim='\t') -> None:
        self.ftype = ftype
        self.dir = dir
        self.columns = columns
        self.delim = delim
        self._template = self.delim.join(['{' + str(i) + '}' for i in range(len(self.columns))])

    def writeheader(self) -> None:
        if not self._f:
            return
        hdr = self.delim.join(self.columns)
        self._f.write(hdr+'\n')

    @property
    def filename(self) -> str:
        return self._fname

    @property
    def mjd(self) -> int:
        return self._mjd

    @mjd.setter
    def mjd(self, mjd: int) -> None:
        if self._mjd == mjd:
            return

        if self._f:
            self._f.close()
        self._fname = os.path.join(self.dir, self.ftype + "-" + str(mjd) + ".txt")
        self._mjd = mjd
        if not os.path.exists(self._fname):
            self._f = open(self._fname, 'a')
            self.writeheader()
        else:
            self._f = open(self._fname, 'a')

    def logdata(self, data: list, mjd=None) -> None:
        if mjd:
            self.mjd = int(mjd)
        if not self._f:
            return
        self._f.write((self._template + '\n').format(*data))
        #self._f.flush()

    def logcomment(self, message) -> None:
        if not self._f:
            return
        self._f.write(('# {0} \n').format(message))
        #self._f.flush()

    def close(self) -> None:
        if self._f:
            self._f.close()
            self._fname = None

class UbloxMessageLogger():
    ubr = None
    sport = None
    gnssPrefixMap = {0: 'G', 1: 'S', 2: 'E', 3: 'B', 5: 'Y', 5: 'J', 6: 'R'}
    utcStdMap = {0: 'UTC', 1: 'UTC(CRL)', 2: 'UTC(NIST)', 3: 'UTC(USNO)', 4: 'UTC(BIPM)', 5: 'UTC(EU)', 6: 'UTC(SU)', 15: 'UTC()'}
    
    sigMap = {0: 'G1C', 3: 'G2L', 4: 'G2S', 20: 'E1C', 21: 'E1B', 25: 'E7I', 26: 'E7Q', 
             30: 'B1D', 31: 'B1X', 32: 'B5D', 33: 'B7D',
             50: 'J1C', 54: 'J2S', 55: 'J2L',
             60: 'R1C', 62: 'R2C'}

    columns = {
             'timepulse': ['LCL', 'TS', 'MJD', 'QERR', 'TIMEBASE'],
#             'timepulse': ['LCL', 'TS', 'MJD', 'QERR', 'TIMEBASE', 'CLKBIAS', 'CLKDRIFT', 'TACC', 'FACC'],
             'pseudorange': ['LCL', 'TS', 'MJD', 'SAT', 'SIG', 'PSEUDORANGE', 'CARRIERPHASE', 'DOPPLER', 'CNO', 
                                'PRSTD', 'CPSTD', 'DOSTD', 'LOCKTIME', 'PRVALID', 'CPVALID', 'HALFCYC', 'SUBHALFCYC'],
             'navsat': ['LCL', 'TS', 'MJD', 'SAT', 'ELEV', 'AZIM', 'CNO', 'PRRES', 'QUALITYIND', 
                                'SVUSED', 'HEALTH', 'DIFFCORR', 'SMOOTHED', 'ORBITSOURCE', 'EPHAVAIL', 'ALMAVAIL', 'ANOAVAIL', 'AOPAVAIL',
                                'SBASCORRUSED', 'RTCMCORRUSED', 'SLASCORRUSED', 'SPARTNCORRUSED', 'PRCORRUSED', 'CRCORRUSED', 'DOCORRUSED'],
              'clock': ['LCL', 'TS', 'MJD', 'CLKBIAS', 'CLKDRIFT', 'TACC', 'FACC', 'GPSACC', 'GALACC', 'BDSACC', 'GLOACC', 'UTCACC'],
              'surveyin': ['LCL', 'TS', 'MJD', 'DUR', 'MEANX', 'MEANY', 'MEANZ', 'MEANV', 'OBS', 'VALID', 'ACTIVE', 'RESERVED1']
             }

    survey_done_written = False

    def __init__(self, outputdir='./'):
        self.files = {}
        for ftype in self.columns:
            self.files[ftype] = UbloxLogFile(ftype, self.columns[ftype], dir=outputdir)
            
        self._nav_clock_missing = 0
        self._msg_nav_clock = None
        self._msg_tim_tp = None
        self._last_message = {}

    def exit(self):
        for f in self.files:
            f.close()
        exit(1)

    @staticmethod
    def is_ubx_message(ubx_msg):
        return hasattr(ubx_msg, 'identity')

    def log_nav_sat(self, args):
        msg = args[0]
        for a in msg['sats']:
            self.files['navsat'].logdata([
                msg['lts'], msg['ts'], msg['mjd'], a['sat'], a['elev'], a['azim'], a['cno'], 
                a['prRes'], a['qualityInd'], a['svUsed'], a['health'], a['diffCorr'],
                a['smoothed'], a['orbitSource'], a['ephAvail'], a['almAvail'], a['anoAvail'], a['aopAvail'], 
                a['sbasCorrUsed'], a['rtcmCorrUsed'], a['slasCorrUsed'], a['spartnCorrUsed'], a['prCorrUsed'], a['prCorrUsed'], a['doCorrUsed']
                ], mjd=msg['mjd']
            )

    def log_nav_clock(self, args):
        msg = args[0]
        self.files['clock'].logdata(msg.values(), mjd=msg['mjd'])

    def log_timepulse(self, args):
        msg = args[0]
        self.files['timepulse'].logdata([
            msg['lts'], msg['ts'], msg['mjd'], msg['qerr'], msg['timebase']
            ], mjd=msg['mjd']
        )

    def log_rawx(self, args):
        msg = args[0]
        for a in msg['meas']:
            self.files['pseudorange'].logdata([
                msg['lts'], msg['ts'], msg['mjd'], a['prn'], a['sig'], a['prMes'], a['cpMes'], a['doMes'], a['cno'],
                    a['prStd'], a['cpStd'], a['doStd'], a['locktime'], a['prValid'], a['cpValid'], a['halfCyc'], a['subHalfCyc']
                ], mjd=msg['mjd']
            )

    def log_survey_in(self, args):
        if self.survey_done_written:
            # after survey there is no change
            return

        msg = args[0]
        print(msg)
        print("Spatial deviation: {0:.3f} m".format((msg['meanV']**0.5)/1000.0))

        self.files['surveyin'].logdata([
            msg['lts'], msg['ts'], msg['mjd'], msg['dur'], msg['meanX'], msg['meanY'], msg['meanZ'], msg['meanV'], 
                msg['obs'], msg['valid'], msg['active'], msg['reserved1']
            ], mjd=msg['mjd']
        )

    def log_survey_done(self, args):
        if self.survey_done_written:
            return

        msg_pvt = args[0]
        self.files['surveyin'].logcomment(msg_pvt)
        self.survey_done_written = True
