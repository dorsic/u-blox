from RTCM3 import *

data = [0xD3, 0x00, 0x13, 0x3E, 0xD7, 0xD3, 0x02, 0x02, 0x98, 0x0E, 0xDE, 0xEF, 0x34, 0xB4, 0xBD, 0x62, 0xAC, 0x09, 0x41, 0x98, 0x6F, 0x33, 0x36, 0x0B, 0x98]
p = RTCM3.RTCM3(5)

with open('/Users/dorsic/Downloads/RTCM3.bin', 'rb') as f:
    data = f.read(1000000)

p.add_data(bytearray(data))
p.process_data(dump_decoded=True)
p.dump(dump_undecoded=True,dump_status=True,dump_decoded=True,dump_timestamp=True)
