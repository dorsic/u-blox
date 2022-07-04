import numpy as np
import pandas as pd

class GnssIono(object):

    IONO_ALT = 350000   # 350 km
    C = 299792458.0   # speed of light m/s

    L1, L2, L5 = 1575.42e6, 1227.60e6, 1176.45e6
    E1, E5a, E5b = 1575.42e6, 1176.45e6, 1207.14e6
    B1, B5, B7 = 1575.42e6, 1176.45e6, 1207.14e6
    SIG_FREQS={'G1C': L1, 'G2L': L2, 'G2S': L2, 'E1C': E1, 'E7Q': E5b, 'B1D': L1, 'B1X': L1, 'B5D': B7, 'B7D': B7,
                'R1C': L1,  'R2C': L2}

    def __init__(self, altitude=IONO_ALT):
        self.ionoalt = altitude

    @staticmethod
    def ionocorrectionP3(freqs, pseudoranges, internal_delays):
        return freqs[0]**2 / (freqs[0]**2 - freqs[1]**2) * (pseudoranges[0]/GnssIono.C-internal_delays[0]) - \
                freqs[1]**2 / (freqs[0]**2 - freqs[1]**2) * (pseudoranges[1]/GnssIono.C-internal_delays[1])

    @staticmethod
    def ionocorrection(freqs, pseudoranges, internal_delays, sig_level):
        return pseudoranges[sig_level-1]/GnssIono.C - GnssIono.ionocorrectionP3(freqs, pseudoranges, internal_delays)

    @staticmethod
    def userclockbias(sat_pseudorange, user_ecef, sat_ecef, satclock_bias, correction):
        return (sat_pseudorange-np.linalg.norm(user_ecef-sat_ecef))/GnssIono.C + satclock_bias - correction


