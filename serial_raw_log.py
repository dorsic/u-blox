import serial

logfile = '/home/pi/ublox/serial_raw_log.mix'

serial = serial.Serial(port='/dev/ttyAMA0', baudrate=115200)
with open(logfile, 'ab') as fout:
    while True:
        try:
            d = serial.read_all()
            fout.write(d)
        except:
            pass
