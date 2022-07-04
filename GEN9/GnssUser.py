
import io
from xml.etree.ElementInclude import include
from matplotlib.cbook import flatten
import numpy as np
import pandas as pd
from GnssIono import GnssIono
from GnssCoorProject import GnssCoorProject
from GnssTime import GnssTime

pseudorange_file = '/Users/dorsic/Downloads/PPPdata/Ublox/pseudorange.txt'
uecef = [4075055.230, 1253817.174, 4728069.307]   # user position ECEF

class GnssUser(object):

    def __init__(self, iono_dataframefile=None):
        self.df = None
        if iono_dataframefile:
            self.df = pd.read_csv(iono_dataframefile, index_col=['SAT', 'TS'])

    def read_prange_file(self, file_name):
        #dfm = pd.read_csv(meas, delimiter='\t') #, index_col=['SAT'])
        skipheader = True
        ts = 0
        rows = []
        cache = {}
        with open(file_name, 'r') as f:
            for line in f:
                if skipheader:
                    skipheader = False
                    continue
                ln = line.split('\t')
                if ln[1] != ts and cache:
                    for sat in cache:
                        # take only dualfreq measurements
                        if cache[sat][0] and cache[sat][1]:
                            rows.append( (float(ts), sat, cache[sat][0], cache[sat][1], cache[sat][2], cache[sat][3]) )            
                    ts = ln[1]
                    cache = {}
                sat, sig, prange, prvalid = ln[3], ln[4], float(ln[5]), int(ln[13])
                # take only valid pseudorange measuremnts
                if prvalid == 1:
                    lvl = 0 if sig in ['G1C', 'B1D', 'B1X', 'R1C', 'E1C'] else 1
                    if not sat in cache:
                        cache[sat] = [None, None, None, None]
                    cache[sat][lvl] = prange
                    cache[sat][lvl+2] = sig
        dfm = pd.DataFrame(rows, columns=['TS', 'SAT', 'PR1', 'PR2', 'SIG1', 'SIG2'])

        dfm['IO1'] = dfm.apply(lambda x: GnssIono.ionocorrection(
            [GnssIono.SIG_FREQS[x.SIG1], GnssIono.SIG_FREQS[x.SIG2]],
            [x.PR1, x.PR2], [0.0, 0.0], 1)*1.0e9, axis=1)
        dfm['IO2'] = dfm.apply(lambda x: GnssIono.ionocorrection(
            [GnssIono.SIG_FREQS[x.SIG1], GnssIono.SIG_FREQS[x.SIG2]],
            [x.PR1, x.PR2], [0.0, 0.0], 2)*1.0e9, axis=1)

        return dfm

    def nieco(self):
        pass

if __name__ == "__main__":
    sp3_folder = '/Users/dorsic/Downloads/PPPdata/SP3'
    sats = GnssCoor(sp3_folder=sp3_folder)

    # prs = GnssUser()
    # dfpr = prs.read_prange_file(pseudorange_file)
    # dfpr.to_csv(sp3_folder + '/pseudoranges_iono.csv')
    # mi, mx = int(dfpr.TS.min()), int(dfpr.TS.max())


    sat = 'E12'
    prs = GnssUser(sp3_folder + '/pseudoranges_iono.csv')
    dfpr = prs.df
    tss = dfpr.loc[sat].index

    data = []
    for ts in tss:
        io1 = dfpr.loc[sat].loc[ts].IO1
        io2 = dfpr.loc[sat].loc[ts].IO2
        if (io1):
            secef = sats.ecef_pos(sat, ts)[:3]
            elev = np.degrees(sats.sat_elevation(uecef, secef))
            iono_intersect = sats.querypoint_ataltitude(uecef, secef, GnssIono.IONO_ALT)
            ionoi_wgs = GnssCoor.gnss_eceftowgs(iono_intersect)
            data.append((ts, elev, ionoi_wgs[0], ionoi_wgs[1], ionoi_wgs[2], io1, io2))
            #print(ts, elev, ionoi_wgs[0], ionoi_wgs[1], ionoi_wgs[2], io1, io2)

    df = pd.DataFrame(data, columns=["TS", "ELEV", 'LON', 'LAT', 'ALT', 'IO1', 'IO2'])
    df.to_csv(sp3_folder + '/E12_iono.csv')