from datetime import datetime, timezone, timedelta, tzinfo
from sqlite3 import Timestamp
import numpy as np

class GnssTime(object):
    START = datetime(2021, 1, 3, 0, 0, 0, 0, tzinfo=timezone.utc)

    @staticmethod
    def week_ts(weekNumber):
        # 2139 = 2021-01-03 00:00:00 = START
        if weekNumber and not np.isnan(weekNumber):
            return (GnssTime.START + timedelta(7*(weekNumber-2139))).timestamp()
    
    # this is loosing precision to about 10 ns !!
    @staticmethod
    def timestamp(wn, towMs, towSubMs):
        return GnssTime.week_ts(wn) + towMs/1e3 + towSubMs/1e9

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
    def tow(towMs, towSubMs, offset=0):
        return towMs/1e3 + towSubMs/1e9 - offset

    @staticmethod
    def tow_components(utctimestamp):
        wn = GnssTime.week_fromts(utctimestamp)
        tow = GnssTime.tow_fromts(utctimestamp)
        towMs = np.int(tow * 1000)
        towSubMs = ((tow-np.int(tow))*1000 - np.int((tow-np.int(tow))*1000)) * 1e6
        return (wn, towMs, towSubMs)
    
    @staticmethod
    def tow_fromts(utctimestamp):
        startweek_ts = GnssTime.week_ts(GnssTime.week_fromts(utctimestamp))
        return utctimestamp - startweek_ts
    
    @staticmethod
    def week_fromts(utctimestamp):
        return 2139 + np.int((datetime.fromtimestamp(utctimestamp, tz=timezone.utc)-GnssTime.START).days/7)

    @staticmethod
    def mjd(utctimestamp):
        # 59217.0 = 2021-01-03 00:00:00 = START
        if utctimestamp:
            td = datetime.fromtimestamp(utctimestamp, tz=timezone.utc) - GnssTime.START
            return 59217.0 + td.days + (td.seconds+td.microseconds/1e6)/86400

    @staticmethod
    def mjd2(wn, towMs, towSubMs):
        if wn and not np.isnan(wn):
            return GnssTime.mjd(GnssTime.week_ts(wn)) + towMs/1e3/86400 + towSubMs/1e9/86400

    @staticmethod
    def now():
        return datetime.now(tz=timezone.utc).timestamp()

    @staticmethod
    def now_tsmjd():
        ts = GnssTime.now()
        return ts, GnssTime.mjd(ts)