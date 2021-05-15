import numpy as np
import RPi.GPIO as GPIO
import debugpy
from ublox_tim import Ublox_TIM, TIMTM2
from mcp4921 import Mcp4921
from collections import deque

# Allow other computers to attach to debugpy at this IP address and port.
#debugpy.listen(('192.168.1.73', 5678))

# Pause the program until a remote debugger is attached
#debugpy.wait_for_client()

voltage_log = 'vctcxo_dac.log'
gnss_log = 'vctcxo_gnss.ubx'

class VctcxoCtrl(object):
    def __init__(self, ubx, dac, extint=1, vlogfile=voltage_log, glogfile=gnss_log, voltage=2048):
        print("Configuring UBX Messages")
        #ubx.configure()
        self.ubx = ubx
        self.dac = dac
        self.minVoltage = 0
        self.maxVoltage = 4096
        self._voltage = voltage
        self.vlogfile = vlogfile
        self.glogfile = glogfile
        self.extint = extint
        self.step = 100
        self.tmarks = []
        self.drifts = []
        self.pi = 0
        self.window = 10
        self.expected_change = 1
        self.stdevs = deque(([0] * int(self.window/2)) + ([1000] * int(self.window/2)))
        self.waitingforchange = False

    def execute(self):
        print("Listening for UBX Messages")
        with open(self.glogfile, "a") as fout:
            for msg in self.ubx.ubx_stream():
                fout.write(str(msg))
                fout.write("\n")
                if (TIMTM2.isMessageOf(msg)):
                    tm2 = TIMTM2(msg)
                    if tm2.extint == self.extint:
                        self.do_control(tm2)

    def set_step(self, drift):
        if abs(drift) > 1000:
            self.step = 100
        elif abs(drift) > 100:
            self.step = 10
        else:
            self.step = 1
        # get the correct direction of the correction
        self.step = self.step if drift >=0 else -self.step
        # solve for corner cases
        self.step = 1 if abs(self.step) < 1 else self.step

    def tmdrift(self, timemark1, timemark2):
        dt = round(timemark2-timemark1)
        return ((timemark2-timemark1)-dt)/dt if dt != 0 else 0

    def new_timemark(self, value):
        drift = self.tmdrift(self.tmarks[-1], value) * 1e9 if len(self.tmarks) > 0 else 0
        self.drifts.append(drift)
        self.tmarks.append(value)
        self.stdevs.rotate(-1)
        self.stdevs[-1] = np.std(self.drifts[-len(self.stdevs):])

    def is_in_interval(self, value, mean, sigma, k=1):
        return (mean-k*sigma < value) and (value < mean+k*sigma)

    def do_control(self, tm2_msg):
        self.new_timemark(tm2_msg.raiseTow)
        snc = self.is_sync(tm2_msg.accEst)
        if (not snc and self.is_stable(tm2_msg.accEst)):
            dmean = np.mean(self.drifts[-self.window:])
            step = int(dmean // 8)
            if abs(dmean) < 50:
                    step = int(np.sign(dmean)) * 1
            self.stdevs = deque(([0] * int(self.window/2)) + ([1000] * int(self.window/2)))
            self.voltage = self.voltage + step
            #print("{0:.9f} voltage set to {1}.".format(tm2_msg.raiseTow, self.voltage))
        print("{0}\tDAC\t{1}\tTM\t{2:.9f}\tdrift\t{3:.1f}\tstdev\t{4:.1f}\taccEst\t{5}".format(
                snc, self.voltage, tm2_msg.raiseTow, self.drifts[-1], self.stdevs[-1], tm2_msg.accEst))


    def is_change(self, expected_change):
        # analyzes the self.stdevs array and searches for low-high-low pattern
        k = 1/3
        state = 0
        for i in range(len(self.stdevs)):
            if (state == 0) and i > 0 and self.stdevs[i] > k * expected_change:
                state = 1
            elif (state == 1) and self.stdevs[i] < k * expected_change:
                state = 2
            elif (state == 2) and self.stdevs[i] > k * expected_change:
                return False
        return state == 2

    def is_sync(self, accEst):
        a = np.array(self.drifts[-self.window:])
        pos = np.count_nonzero(a >= 0)
        neg = np.count_nonzero(a < 0)
        (np.abs(a)<accEst).all()
        return abs(pos-neg) <= 4 and (np.abs(a)<accEst).all()

    def is_stable(self, accEst, k=1/2):
        a = np.array(self.stdevs)
        return (a < k*accEst).all()

    def test_control(self, tm2_msg):
        shift = 0
        voltages = [3000, 2998, 3000, 2998, 3000, 2998, 3000, 2900]

        self.new_timemark(tm2_msg.raiseTow)
        if (self.waitingforchange == False and self.is_stable(tm2_msg.accEst)):
            self.voltage = voltages[self.pi+shift]
            print("{0:.9f} voltage set to {1}.".format(tm2_msg.raiseTow, voltages[self.pi+shift]))
            self.pi += 1
            for i in range (self.window-1):
                self.stdevs[i] = 0
            self.waitingforchange = True
        elif (self.is_change(2*8)):
            self.waitingforchange = False
        else:
            print("{0}\tTM\t{1:.9f}\tdrift\t{2:.1f}\tstdev\t{3:.1f}\taccEst\t{4}".format(
                self.pi, tm2_msg.raiseTow, self.drifts[-1], self.stdevs[-1], tm2_msg.accEst))

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        v = value if value < self.maxVoltage else self.maxVoltage
        v = v if value > self.minVoltage else self.minVoltage
        if (v == self.maxVoltage or v == self.minVoltage):
            self.step *= -1

        if v != self._voltage:
            self._voltage = v
            self.dac.setVoltage(self._voltage)
            with open(self.vlogfile, "a") as fout:
                fout.write('{0:.9f}\t{1}\n'.format(self.tmarks[-1], self._voltage))

def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    ubx = Ublox_TIM()
    dac = Mcp4921(spibus=0, spidevice=1, cs=24, ldac=22, buffered=False)
    xo = VctcxoCtrl(ubx, dac, voltage=2400)
    xo.execute()
        
if __name__ == '__main__':
    main()