from serial import Serial
import pyubx2

class Ublox_TIM(object):
    def __init__(self, serialPort='/dev/ttyAMA0', baudRate=115200):
        stream =  Serial(serialPort, baudRate, timeout=3)
        self.reader = pyubx2.UBXReader(stream)

    def ubx_stream(self):
        while True:
            try:
                (raw, parsed) = self.reader.read()
                yield(parsed)
            except KeyboardInterrupt:
                print('interrupted')
                return
            except:
                print("Unknown error")

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
        return ubxmessage.identity == 'TIM-TM2'

    def __init__(self, ubxmessage):
        if TIMTM2.isMessageOf(ubxmessage):
            self.msg = ubxmessage
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
            return self.wnR
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