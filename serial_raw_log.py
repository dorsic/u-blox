import serial

logfile = '/home/pi/ublox/serial_raw_log.mix'
logfile = 'serial_raw_log.mix'
port = '/dev/ttyAMA0'
port = '/dev/cu.usbserial-14410'

serial = serial.Serial(port=port, baudrate=115200)
with open(logfile, 'ab') as fout:
    while True:
        try:
            d = serial.read_all()
            fout.write(d)
        except:
            pass
