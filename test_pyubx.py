
from pyubx2 import UBXMessage, SET, UBX_MSGIDS
import pyubx2
import pyubx2.exceptions as ube

msg = UBXMessage("CFG", "CFG-TMODE2", SET, timeMode=0)
msg = UBXMessage("CFG", "CFG-TP5", SET, tpIdx=1, version=1, antCableDelay=20, rfGroupDelay=0, 
    freqPeriod=10, pulseLenRatio=20, freqPeriodLock=20, pulseLenRatioLock=50, userConfigDelay=0, flags=b'\x00\x00\x00\x08')
payload = b'\x01\x00\x00\x00\x14\x00\x00\x00\x0A\x00\x00\x00\x14\x00\x00\x00\x14\x00\x00\x00\x32\x00\x00\x00\x00\x00\x00\x00\x09\x00\x00\x00'
payloadGPS = b'\x00\x20\x20\x07\x00\x08\x10\x00\x01\x00\x01\x01\x01\x01\x03\x00\x00\x00\x01\x01\x02\x04\x08\x00\x00\x00\x01\x01\x03\x08\x10\x00\x00\x00\x01\x01\x04\x00\x08\x00\x00\x00\x01\x03\x05\x00\x03\x00\x00\x00\x01\x05\x06\x08\x0E\x00\x00\x00\x01\x01'
msg = UBXMessage("CFG", "CFG-TP5", SET, payload=payload)
msg = UBXMessage("CFG", "CFG-GNSS", SET, payload=payloadGPS)
#msg = UBXMessage("CFG", "CFG-RATE", SET, payload=b'\x64\x00\x01\x00\x00\x00')
#msg = UBXMessage("CFG", "CFG-MSG", SET, payload=b'\xf1\x00\x01\x01\x00\x01\x01\x00')


print(msg)
print("-----")
print(msg.payload)
print(msg.serialize())
