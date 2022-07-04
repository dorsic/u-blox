import datetime
import numpy as np

class GPSTimeConv(object):
    START = datetime.datetime(2021, 1, 3, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)

    @staticmethod
    def week_ts(weekNumber):
        # 2139 = 2021-01-03 00:00:00 = START
        if weekNumber and not np.isnan(weekNumber):
            return (GPSTimeConv.START + datetime.timedelta(7*(weekNumber-2139))).timestamp()
    
    # this is loosing precision to about 10 ns !!
    @staticmethod
    def timestamp(wn, towMs, towSubMs):
        return GPSTimeConv.week_ts(wn) + towMs/1e3 + towSubMs/1e9

    @staticmethod
    def tow(towMs, towSubMs, offset=0):
        return towMs/1e3 + towSubMs/1e9 - offset

    @staticmethod
    def tow_components(utctimestamp):
        wn = GPSTimeConv.week_fromts(uts.timestamp())
        tow = GPSTimeConv.tow_fromts(uts.timestamp())
        towMs = np.int(tow * 1000)
        towSubMs = ((tow-np.int(tow))*1000 - np.int((tow-np.int(tow))*1000)) * 1e6
        return (wn, towMs, towSubMs)
    
    @staticmethod
    def tow_fromts(utctimestamp):
        startweek_ts = GPSTimeConv.week_ts(GPSTimeConv.week_fromts(utctimestamp))
        return utctimestamp - startweek_ts
    
    @staticmethod
    def week_fromts(utctimestamp):
        return 2139 + np.int((datetime.datetime.fromtimestamp(utctimestamp, tz=datetime.timezone.utc)-GPSTimeConv.START).days/7)

    @staticmethod
    def mjd(utctimestamp):
        # 59217.0 = 2021-01-03 00:00:00 = START
        if utctimestamp:
            td = datetime.datetime.fromtimestamp(utctimestamp, tz=datetime.timezone.utc) - GPSTimeConv.START
            return 59217.0 + td.days + (td.seconds+td.microseconds/1e6)/86400

    @staticmethod
    def mjd2(wn, towMs, towSubMs):
        if wn and not np.isnan(wn):
            return GPSTimeConv.mjd(GPSTimeConv.week_ts(wn)) + towMs/1e3/86400 + towSubMs/1e9/86400