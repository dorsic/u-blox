from turtle import right
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import NamedTuple
from GnssTime import GnssTime
from GnssCoorProject import GnssCoorProject

class GnssOrbit(object):

    def _numHeaderRows(self, sp3_filename):
        with open(sp3_filename, 'r') as f:
            res = 0
            for line in f:
                if (line.strip().startswith('*')):
                    return res
                res += 1

    def _parseTime(self, epochLine):
        if not epochLine.startswith('*'):
            return None
        
        d = ' '.join(epochLine.split())   # replace multiple whitespaces with one
        d = d.split(' ')
        ms = d[6].split('.') 
        #return datetime(int(d[1]), int(d[2]), int(d[3]), int(d[4]), int(d[5]), int(ms[0]), int(ms[1][:6]))
        return GnssTime.timestamp4(int(d[1]), int(d[2]), int(d[3]), int(d[4]), int(d[5]), int(ms[0]), int(ms[1][:6]))       

    def _parsePosition(self, dataLine):
        if not dataLine.startswith('P'):
            return None

        d = ' '.join(dataLine.split())   # replace multiple whitespaces with one
        d = d[1:].split(' ')             # ignore the first character marking the position line type

        return d[0], float(d[1])*1000.0, float(d[2])*1000.0, float(d[3])*1000.0, \
            float(d[4])*1000.0 if not d[4].startswith('999999') else None

    def _list_files(self, folder):
        if not folder:
            return None
        return [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith('sp3')]    

    def _read_sp3(self, sp3_filename, fromts=None, tots=None):
        data = []
        epoch = None
        file_ts = GnssTime.timestamp3(os.path.basename(sp3_filename).split('_')[1])
        skipheader = self._numHeaderRows(sp3_filename)
        cnt = 0
        with open(sp3_filename, 'r') as f:
            res = 0         
            for line in f:
                if cnt < skipheader:
                    cnt += 1
                    continue
                ln = line.strip()
                epoch = self._parseTime(ln) if self._parseTime(ln) else epoch
                if fromts and epoch < fromts:
                    continue
                if tots and epoch >= tots:
                    break
                type = 'O' if epoch < file_ts else 'P' if epoch >= file_ts else 'U'
                position = self._parsePosition(ln)
                if position:
                    #position.append(type)
                    data.append((epoch, *position, type))

        d = np.array(data, dtype=[('TS', 'float64'), ('SAT', 'object'), ('X', 'float64'), 
                ('Y', 'float64'), ('Z', 'float64'), ('DT', 'float64'), ('TYPE', 'object')])
        df = pd.DataFrame.from_records(d, columns=['TS', 'SAT', 'X', 'Y', 'Z', 'DT', 'TYPE'], index=['SAT'])
        return df

    def _makewindow(self, halfsize, center, n):
        mi = center - halfsize
        mx = center + halfsize
        if mi < 0:
            mx += -mi
            mi = 0
        if mx >= n:
            mi -= mx-n
            mx = n
        mi = 0 if mi < 0 else mi
        mx = n if mx >= n else mx
        return mi, mx

    def __init__(self, sp3_folder=None, sp3_files=None):
        self.df = pd.DataFrame()
        files = sp3_files if sp3_files else self._list_files(sp3_folder)
        ordered = [(os.path.basename(sp3f).split('_')[1], sp3f) for sp3f in files]
        ordered.sort(key=lambda x: x[0])
        ordered = [sp3f[1] for sp3f in ordered]
        fromts, nextts = None, None
        dfs = []
        for i in range(len(ordered)):
            sp3f = ordered[i]
            nextfts = GnssTime.timestamp3(ordered[i+1].split('_')[1]) if i < len(ordered)-1 else None
            # the file contains 1 day of observations and 1 day of predictions
            # stop loading the predictions if next file available
            fromts = nextts
            nextts = nextfts - 86400 if nextfts else None       # ToDo: handle the possible leapseconds
            print("Loading ", sp3f, nextfts)
            df = self._read_sp3(sp3f, fromts , nextts)
            dfs.append(df)
        self.df = pd.concat(dfs)

    def dump(self, filename):
        ddf = self.df
        ddf['MJD'] = ddf.apply(lambda x: GnssTime.mjd(x.TS), axis=1)
        ddf.to_csv(filename, columns=['TS', 'MJD', 'X', 'Y', 'Z', 'DT', 'TYPE'])

    def ecef_pos(self, sat, timestamp):
        fit_window = 3
        polydeg = 2
        # make sub datafrake for given satellite
        dfsat = self.df.loc[sat].reset_index()
        # index of the last observation less than timestamp
        maxlessidx = dfsat[dfsat.TS <= timestamp].TS.idxmax()
        # if observation time same as timestamp return the observation
        if (dfsat.iloc[maxlessidx].TS == timestamp):
            return dfsat.iloc[maxlessidx].loc[['X', 'Y', 'Z', 'DT']]

        # create window for interpolation values
        mi, mx = self._makewindow(fit_window, maxlessidx, len(dfsat))

        # check if enough values for interpolation, else decrease the degree
        polydeg = (mx-mi) if (mx-mi) < polydeg+1 else polydeg
        # try to interpolate the value
        x = [tt for tt in list(dfsat.iloc[mi:mx].TS)]
        y = dfsat[['X', 'Y', 'Z', 'DT']][mi:mx].values.tolist()

        f = np.polyfit(x, y, deg=polydeg, full=False)
        pos = np.sum([f[i] * np.power(timestamp, polydeg-i) for i in range(polydeg+1)], axis=0)
        return pos

    def data_range(self, include_prediction=False):
        if include_prediction:
            return self.df.TS.min(), self.df.TS.max()
        else:
            return self.df[self.df.TYPE == 'O'].TS.min(), \
                self.df[self.df.TYPE == 'O'].TS.max() 



if __name__ == "__main__":
    sp3_folder = '/Users/dorsic/Downloads/PPPdata/SP3'
    sats = GnssOrbit(sp3_folder=sp3_folder)
    tsr = sats.data_range(include_prediction=False)
    print(tsr[0], tsr[1])
    print(GnssTime.mjd(tsr[0]), GnssTime.mjd(tsr[1]))
    tsr = sats.data_range(include_prediction=True)
    print(tsr[0], tsr[1])
    print(GnssTime.mjd(tsr[0]), GnssTime.mjd(tsr[1]))

    sats.df.to_csv('/Users/dorsic/Downloads/PPPdata/SP3/GnssOrbit_df.csv')
    

    #E01,1649467800.0,-5227831.58,-22537185.569000002,-18472934.517,-612735.8010000001,O
    #E01,1649468100.0,-4830808.892,-22135315.975,-19057605.816999998,-612738.001,O


