from datetime import datetime, timezone, timedelta, tzinfo
from sqlite3 import Timestamp
import numpy as np

class GnssTime(object):
    START = datetime(2021, 1, 3, 0, 0, 0, 0, tzinfo=timezone.utc)
    gps_leapsecs = 18

    @staticmethod
    def week_ts(weekNumber):
        # 2139 = 2021-01-03 00:00:00 = START
        if weekNumber and not np.isnan(weekNumber):
            return (GnssTime.START + timedelta(7*(weekNumber-2139))).timestamp()
    
    # this is loosing precision to about 10 ns !!
    @staticmethod
    def timestamp(wn, towMs, towSubMs, leapsecs=18):
        return GnssTime.week_ts(wn) + towMs*1.0e-3 + towSubMs*1.0e-9 - leapsecs

    @staticmethod
    def timestamp2(year, dayofyear, hour, minute, second):
        return (datetime(year, 1, 1, hour, minute, second, 0, tzinfo=timezone.utc) + timedelta(days=dayofyear-1)).timestamp()

    @staticmethod
    def timestamp3(year_dayofear_hour_minute_string):
        return GnssTime.timestamp2(int(year_dayofear_hour_minute_string[:4]), int(year_dayofear_hour_minute_string[4:7]), 
                    int(year_dayofear_hour_minute_string[7:9]), int(year_dayofear_hour_minute_string[9:11]), 0)

    @staticmethod
    def timestamp4(year, month, day, hour, minute, second, millis):
        return datetime(year, month, day, hour, minute, second, millis, tzinfo=timezone.utc).timestamp()
        
    @staticmethod
    def timestamp5(wn, tow, leapsecs=18):
        return GnssTime.week_ts(wn) + tow - leapsecs

    @staticmethod
    def tow(towMs, towSubMs, offset=0.0):
        return towMs*1.0e-3 + towSubMs*1.0e-9 + offset

    @staticmethod
    def tow_components(utctimestamp, leapsecs=18):
        wn = GnssTime.week_fromts(utctimestamp, leapsecs)
        tow = GnssTime.tow_fromts(utctimestamp, leapsecs)
        towMs = np.int(tow * 1.0e3)
        towSubMs = ((tow-np.int(tow))*1.0e3 - np.int((tow-np.int(tow))*1.0e3)) * 1.0e6
        return (wn, towMs, towSubMs)
    
    @staticmethod
    def tow_fromts(utctimestamp, leapsecs=18):
        startweek_ts = GnssTime.week_ts(GnssTime.week_fromts(utctimestamp, leapsecs))
        return utctimestamp + leapsecs - startweek_ts
    
    @staticmethod
    def week_fromts(utctimestamp, leapsecs=18):
        return 2139 + np.int((datetime.fromtimestamp(utctimestamp+leapsecs, tz=timezone.utc)-GnssTime.START).days/7)

    @staticmethod
    def mjd(utctimestamp):
        # 59217.0 = 2021-01-03 00:00:00 = START
        if utctimestamp:
            td = datetime.fromtimestamp(utctimestamp, tz=timezone.utc) - GnssTime.START
            return 59217.0 + td.days + (td.seconds+td.microseconds*1.0e-6)/86400.0

    @staticmethod
    def mjd2(wn, towMs, towSubMs, leapsecs=18):
        if wn and not np.isnan(wn):
            return GnssTime.mjd(GnssTime.week_ts(wn)) + (towMs-leapsecs*1.0e3)*1.0e-3/86400.0 + towSubMs*1.0e-9/86400.0

    @staticmethod
    def now():
        return datetime.now(tz=timezone.utc).timestamp()

    @staticmethod
    def now_tsmjd():
        ts = GnssTime.now()
        return ts, GnssTime.mjd(ts)