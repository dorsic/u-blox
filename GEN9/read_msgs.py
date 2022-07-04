import os
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb, ubxhelpers
from datetime import datetime
from GnssTime import GnssTime
from GnssMqtt import GnssMqtt
from TimedUBXMessage import TimedUBXMessage
from UBXConcentrator import UBXConcentrator, UbxContentratorEventType
from UBXLogger import UBXLogger

logdir = os.path.dirname(__file__) + '/data'
confdir = os.path.dirname(__file__) + '/conf'
configs = [os.path.join(confdir, 'TP1.conf'), 
           os.path.join(confdir, 'OUT_MSG.conf'),
           os.path.join(confdir, 'SURVEY.conf'),
          # os.path.join(confdir, 'BALK_STRED.conf'),
          # os.path.join(confdir, 'zla_poloha.conf')
          ]
f_timepulse = 'timepulse.txt'
f_rawx = 'rawx.txt'

ubxl = UBXLogger(serialport='/dev/ttyS0', fn_timepulse=os.path.join(logdir, 'timepulse.txt'), fn_pseudorange=os.path.join(logdir, "pseudorange.txt"), 
                    fn_navsat=os.path.join(logdir, 'navsat.txt'), fn_clock=os.path.join(logdir, 'clock.txt'), fn_svin=os.path.join(logdir, 'survey.txt'))

ubxc = UBXConcentrator()
ubxc.register_listener(UbxContentratorEventType.NAVCLOCK_EVENT, ubxl.log_nav_clock)
ubxc.register_listener(UbxContentratorEventType.NAVSAT_EVENT, ubxl.log_nav_sat)
ubxc.register_listener(UbxContentratorEventType.TIMEPULSE_EVENT, ubxl.log_timepulse)
ubxc.register_listener(UbxContentratorEventType.RAWX_EVENT, ubxl.log_rawx)
ubxc.register_listener(UbxContentratorEventType.SURVEYIN_EVENT, ubxl.log_survey_in)
ubxc.register_listener(UbxContentratorEventType.SURVEY_DONE, ubxl.log_survey_done)

#mqtt = GnssMqtt()

for cfg in configs:
    print("Processing config ", cfg)
    ubxl.apply_configfile(cfg)

while True:
    try:
        (raw_data, ubx_msg) = ubxl.ubr.read()
        if not hasattr(ubx_msg, 'identity'):
            continue
        print(ubx_msg.identity)
        ubxc.receive(ubx_msg)
        # if msg.identity in (''):
        #     print(msg.identity, msg.timestamp)
        #mqtt.publish(ubx_msg)
    except KeyboardInterrupt:
        ubxl.exit()
    except:
        pass
