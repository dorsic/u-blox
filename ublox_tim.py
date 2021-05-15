import serial
import ublox_gps

class Ublox_TIM(object):
    def __init__(self, serialPort='/dev/ttyAMA0', baudRate=115200):
        port = serial.Serial(serialPort, baudRate, timeout=3)
        self.gps = ublox_gps.UbloxGps(port)

    def ubx_stream(self):
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.MON_CLS, 
                                        ublox_gps.sparkfun_predefines.TIM_CLS,
                                        ublox_gps.sparkfun_predefines.NAV_CLS,
                                        ublox_gps.sparkfun_predefines.CFG_CLS])        
        while True:
            try:
                msg = parse_tool.receive_from(self.gps.hard_port)
                yield(msg)
            except KeyboardInterrupt:
                print('interrupted')
                return
            except:
                pass

    def configure(self):
        pass

class GPSTimeConv(object):

    @staticmethod
    def week_ts(weekNumber):
        # 2139 = 2021-01-03 00:00:00
        return (datetime.datetime(2021, 1, 3) + datetime.timedelta(7*(weekNumber-2139))).timestamp()

    # this is loosing precision to about 10 ns !!
    @staticmethod
    def timestamp(wn, towMs, towSubMs):
        return GPSTimeConv.week_ts(wn) + towMs/1e3 + towSubMs/1e9

    @staticmethod
    def tow(towMs, towSubMs, offset=0):
        return towMs/1e3 + towSubMs/1e9 - offset

class TIMTM2(object):
    @classmethod
    def isMessageOf(cls, ubxmessage):
        return (ubxmessage[0] + '-' + ubxmessage[1]) == 'TIM-TM2'

    def __init__(self, ubxmessage):
        if TIMTM2.isMessageOf(ubxmessage):
            self.msg = ubxmessage[2]
        else:
            self.msg = None

    @property
    def extint(self):
        try:
            return self.msg.ch
        except:
            return None

    # this is loosing precision to about 10 ns !!
    @property
    def raiseTm(self):
        try:
            return GPSTimeConv.timestamp(self.msg.wnR, self.msg.towMsR, self.msg.towSubMsR)
        except:
            return None

    @property
    def raiseWn(self):
        try:
            return self.msg.wnR
        except:
            return None

    @property
    def raiseTow(self):
        try:
            return GPSTimeConv.tow(self.msg.towMsR, self.msg.towSubMsR, 0)
        except:
            return None

    @property
    def accEst(self):
        try:
            return self.msg.accEst
        except:
            return None