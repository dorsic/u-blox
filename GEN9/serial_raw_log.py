import serial
import uuid

logfile = '/home/pi/ublox/ublox-' + str(uuid.uuid4()) + '.mix'

serial = serial.Serial(port='/dev/ttyS0', baudrate=115200)
with open(logfile, 'ab') as fout:
    while True:
        try:
            d = serial.read_all()
            fout.write(d)
        except:
            pass
