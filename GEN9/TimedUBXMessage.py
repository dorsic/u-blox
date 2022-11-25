from pyubx2 import UBXMessage
from GnssTime import GnssTime

class TimedUBXMessage(UBXMessage):

    def __init__(self, ubx_msg):
        super().__init__(ubx_msg.msg_cls, ubx_msg.msg_id, ubx_msg.msgmode, payload=ubx_msg.payload)

    def _parseTime(self):
        # take week from message if available, if not take from constructor, else take actual
        week = self.week if (hasattr(self, 'week')) else GnssTime.week_fromts(GnssTime.now())
        towms = self.tow*1.0e3 if (hasattr(self, 'tow')) else 0.0
        towms = self.iTOW if (hasattr(self, 'iTOW')) else towms
        towms = self.towMS if (hasattr(self, 'towMS')) else towms
        ftow = self.fTOW if (hasattr(self, 'fTOW')) else 0.0
        ftow = self.towSubMS if (hasattr(self, 'towSubMS')) else ftow

    @property
    def timestamp(self):
        try:
            now = GnssTime.now()
            week = GnssTime.week_fromts(now)
            week = self.week if (hasattr(self, 'week') and self.identity != 'NAV-TIMEBDS') else week
            towms = self.tow*1.0e3 if (hasattr(self, 'tow')) else -1.0
            towms = self.iTOW if (hasattr(self, 'iTOW')) else towms
            towms = self.towMS if (hasattr(self, 'towMS')) else towms
            towms = self.rcvTow*1.0e3 if (hasattr(self, 'rcvTow')) else towms            
            if towms == -1.0:
                return now      # not enought information
            ftow = self.fTOW if (hasattr(self, 'fTOW')) else 0.0
            ftow = self.towSubMS if (hasattr(self, 'towSubMS')) else ftow
            return GnssTime.timestamp(week, towms, ftow)
        except:
            return None

    @property
    def mjd(self):
        now_mjd = GnssTime.now_tsmjd()
        week = GnssTime.week_fromts(now_mjd[0])
        week = self.week if (hasattr(self, 'week') and self.identity != 'NAV-TIMEBDS') else week
        towms = self.tow*1.0e3 if (hasattr(self, 'tow')) else -1.0
        towms = self.iTOW if (hasattr(self, 'iTOW')) else towms
        towms = self.towMS if (hasattr(self, 'towMS')) else towms
        if towms == -1.0:
            return now_mjd[1]    # not enought information
        ftow = self.fTOW if (hasattr(self, 'fTOW')) else 0.0
        ftow = self.towSubMS if (hasattr(self, 'towSubMS')) else ftow
        return GnssTime.mjd2(week, towms, ftow)

    def prop(self, basename, n):
        if (hasattr(self, basename+'_'+str(n))):
            return getattr(self, basename+'_'+str(n))
        return None