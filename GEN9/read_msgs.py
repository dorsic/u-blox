import os
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb, ubxhelpers
from datetime import datetime
from GnssTime import GnssTime
from GnssMqtt import GnssMqtt
from TimedUBXMessage import TimedUBXMessage
from UBXProcessor import UBXProcessor, UbxProcessorEventType
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

ubxp = UBXProcessor()
ubxp.register_listener(UbxProcessorEventType.NAVCLOCK_EVENT, ubxl.log_nav_clock)
ubxp.register_listener(UbxProcessorEventType.NAVSAT_EVENT, ubxl.log_nav_sat)
ubxp.register_listener(UbxProcessorEventType.TIMEPULSE_EVENT, ubxl.log_timepulse)
ubxp.register_listener(UbxProcessorEventType.RAWX_EVENT, ubxl.log_rawx)
ubxp.register_listener(UbxProcessorEventType.SURVEYIN_EVENT, ubxl.log_survey_in)
ubxp.register_listener(UbxProcessorEventType.SURVEY_DONE, ubxl.log_survey_done)

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
        ubxp.receive(ubx_msg)
        # if msg.identity in (''):
        #     print(msg.identity, msg.timestamp)
        #mqtt.publish(ubx_msg)
    except KeyboardInterrupt:
        ubxl.exit()
    except:
        pass
