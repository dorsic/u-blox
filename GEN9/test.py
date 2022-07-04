from curses import baudrate
from serial import Serial
from pyubx2 import UBXReader

stream = Serial('/dev/ttyAMA0', baudrate=115200, timeout=3)
ubr = UBXReader(stream)
while True:
    try:
        (raw_data, parsed_data) = ubr.read()
        print(parsed_data)
    except KeyboardInterrupt:
        exit(1)
