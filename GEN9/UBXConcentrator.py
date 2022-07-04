from enum import Enum, auto
from pyubx2 import ubxhelpers
from GnssTime import GnssTime
from TimedUBXMessage import TimedUBXMessage

class UbxContentratorEventType(Enum):
    NAVCLOCK_EVENT = auto()
    TIMEPULSE_EVENT = auto()
    NAVSAT_EVENT = auto()
    RAWX_EVENT = auto()
    SURVEYIN_EVENT = auto()
    SURVEY_DONE = auto()

class UBXConcentrator():
    gnssPrefixMap = {0: 'G', 1: 'S', 2: 'E', 3: 'B', 5: 'Y', 5: 'J', 6: 'R'}
    utcStdMap = {0: 'UTC', 1: 'UTC(CRL)', 2: 'UTC(NIST)', 3: 'UTC(USNO)', 4: 'UTC(BIPM)', 5: 'UTC(EU)', 6: 'UTC(SU)', 15: 'UTC()'}
    
    sigMap = {0: 'G1C', 3: 'G2L', 4: 'G2S', 20: 'E1C', 21: 'E1B', 25: 'E7I', 26: 'E7Q', 
             30: 'B1D', 31: 'B1X', 32: 'B5D', 33: 'B7D',
             50: 'J1C', 54: 'J2S', 55: 'J2L',
             60: 'R1C', 62: 'R2C'}

    def __init__(self):
        self._last_message = {}
        self._listeners = {}
        for event_type in UbxContentratorEventType:
            self._listeners[event_type] = []

    def _timebase(self, timebase, timeRefGnss, utcStandard):
        if timebase == 0:
            return ubxhelpers.gnss2str(timeRefGnss)
        if timebase == 1:
            return self.utcStdmap[utcStandard]
        return ''

    def receive(self, ubx_msg):
        tubx_msg = TimedUBXMessage(ubx_msg)
        if not (tubx_msg.identity in self._last_message):
            self._last_message[tubx_msg.identity] = {}
        store = {'received': GnssTime.now(),
                    'ts': tubx_msg.timestamp,
                    'msg': tubx_msg}
        self._last_message[tubx_msg.identity] = store
        self._nav_clock(tubx_msg)
        self._nav_sat(tubx_msg)
        self._tim_tp(tubx_msg)
        self._rmx_rawx(tubx_msg)
        self._tim_svin(tubx_msg)

    def register_listener(self, event_type, function):
        self._listeners[event_type].append(function)

    def _notify(self, event_type, *args):
        for f in self._listeners[event_type]:
            # print("notifying listeners")
            f(args)

    def _nav_clock(self, tubx_msg):
        if tubx_msg.identity != 'NAV-CLOCK':
            return None
        # NAV-CLOCK is the last message of the NAV-TIMExxx batch
        tacc = []
        for scale in ['GPS', 'GAL', 'BDS', 'GLO', 'UTC']:
            tacc.append(None)
            # message is enabled and has beed received
            if ('NAV-TIME'+scale in self._last_message) and (tubx_msg.timestamp) and (self._last_message['NAV-TIME'+scale]['ts']):
                # epochs of the messages are the same
                if abs(self._last_message['NAV-TIME'+scale]['ts'] - tubx_msg.timestamp)<1.0e-2:
                    tacc[-1] = self._last_message['NAV-TIME'+scale]['msg'].tAcc
        lts = GnssTime.now()
        msg = {'lts': lts, 'ts': tubx_msg.timestamp, 'mjd': tubx_msg.mjd, 
                'clkb': tubx_msg.clkB, 'clkd': tubx_msg.clkD, 'tacc': tubx_msg.tAcc, 'facc': tubx_msg.fAcc, 
                'gpsacc': tacc[0], 'galacc': tacc[1], 'bdsacc': tacc[2], 'gloacc': tacc[3], 'utcacc': tacc[4]}
        self._notify(UbxContentratorEventType.NAVCLOCK_EVENT, msg)

    def _nav_sat(self, tubx_msg):
        if tubx_msg.identity != 'NAV-SAT':
            return
        lts = GnssTime.now()
        msg = {'lts': lts, 'ts': tubx_msg.timestamp, 'mjd': tubx_msg.mjd, 'sats': []}
        for i in range(1, tubx_msg.numSvs+1):
            si = "{0:02}".format(i)
            sat = {}
            for att in ['gnssId', 'svId', 'elev', 'azim', 'cno', 'prRes', 'qualityInd', 'svUsed', 'health', 'diffCorr', 
                    'smoothed', 'orbitSource', 'ephAvail', 'almAvail', 'anoAvail', 'aopAvail',
                    'sbasCorrUsed', 'rtcmCorrUsed', 'slasCorrUsed', 'spartnCorrUsed', 'prCorrUsed', 'crCorrUsed', 'doCorrUsed']:
                sat[att] = tubx_msg.prop(att, si)
            sat['sat'] = self.gnssPrefixMap[sat['gnssId']] + "{0:02}".format(sat['svId'])
            msg['sats'].append(sat)
        self._notify(UbxContentratorEventType.NAVSAT_EVENT, msg)

    def _tim_tp(self, tubx_msg):
        if (tubx_msg.identity not in ('TIM-TP')):
            return
        lts = GnssTime.now()
        tb = self._timebase(tubx_msg.timeBase, tubx_msg.timeRefGnss, tubx_msg.utcStandard)
        msg = {'lts': lts, 'ts': tubx_msg.timestamp, 'mjd': tubx_msg.mjd, 'qerr': tubx_msg.qErr,
                'timebase': tb
              }
        self._notify(UbxContentratorEventType.TIMEPULSE_EVENT, msg)

        # if (self._msg_tim_tp and self._msg_nav_clock):
        #     ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
        #     mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
        #     tow = GnssTime.tow_fromts(ts)            
        #     if abs((self._msg_nav_clock.iTOW/1000.0)-tow) <= 1.0:
        #         tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
        #         output = self.separator.join(['{' + str(i) + '}' for i in range(8)])
        #         self.file['timepulse'].write((output + "\n").format(
        #             lts, ts, mjd, self._msg_tim_tp.qErr, tb,
        #             self._msg_nav_clock.clkB, self._msg_nav_clock.clkD, self._msg_nav_clock.tAcc, self._msg_nav_clock.fAcc))
        #         self._msg_tim_tp = None
        # elif (msg.identity == 'TIM-TP' and self._nav_clock_missing > 3):
        #     ts = GnssTime.timestamp(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
        #     mjd = GnssTime.mjd2(self._msg_tim_tp.week, self._msg_tim_tp.towMS, self._msg_tim_tp.towSubMS)
        #     tb = self._timebase(self._msg_tim_tp.timeBase, self._msg_tim_tp.timeRefGnss, self._msg_tim_tp.utcStandard)                
        #     output = self.separator.join(['{' + str(i) + '}' for i in range(4)])
        #     self.file['timepulse'].write((output + "\n").format(lts, ts, mjd, self._msg_tim_tp.qErr, tb))
        #     self._msg_tim_tp = None

    def _rmx_rawx(self, tubx_msg):
        if (tubx_msg.identity != 'RXM-RAWX'):
                return
        lts = GnssTime.now()
        msg = {'lts': lts, 'ts': tubx_msg.timestamp, 'mjd': tubx_msg.mjd, 'meas': []}
        for i in range(1, tubx_msg.numMeas+1):
            si = "{0:02}".format(i)
            meas = {}
            for att in ['gnssId', 'svId', 'prMes', 'cpMes', 'doMes', 'cno', 'prStd', 'cpStd', 'doStd', 'locktime', 
                    'prValid', 'cpValid', 'halfCyc', 'subHalfCyc', 'reserved2']:
                meas[att] = tubx_msg.prop(att, si)
            meas['prn'] = self.gnssPrefixMap[meas['gnssId']] + "{0:02}".format(meas['svId'])
            meas['sig'] = self.sigMap[meas["gnssId"]*10+meas["reserved2"]]
            msg['meas'].append(meas)
        self._notify(UbxContentratorEventType.RAWX_EVENT, msg)

    def _tim_svin(self, tubx_msg):
        if (tubx_msg.identity != 'TIM-SVIN'):
                return
        lts = GnssTime.now()
        msg = {'lts': lts, 'ts': tubx_msg.timestamp, 'mjd': tubx_msg.mjd}

        for att in ['dur', 'meanX', 'meanY', 'meanZ', 'meanV', 'obs', 'valid', 'active', 'reserved1']:
            msg[att] = getattr(tubx_msg, att)
            
        self._notify(UbxContentratorEventType.SURVEYIN_EVENT, msg)
        
        if ('NAV-PVT' in self._last_message):
            if (msg['valid'] == 1) and ((self._last_message['NAV-PVT']['msg']).fixType == 5):
                self._notify(UbxContentratorEventType.SURVEY_DONE, self._last_message['NAV-PVT']['msg'])
                

