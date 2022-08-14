import os
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb, ubxhelpers
from datetime import datetime
from GnssTime import GnssTime
from GnssMqtt import GnssMqtt
from TimedUBXMessage import TimedUBXMessage
from UbloxProcessor import UbloxProcessor, UbloxProcessorEventType
from UbloxMessageLogger import UbloxMessageLogger 
from UbloxReader import UbloxReader

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

ureader = UbloxReader(serialport='/dev/ttyS0', baudrate=115200, configdir=confdir)
ulogger = UbloxMessageLogger(outputdir=logdir)
uprocessor = UbloxProcessor()

uprocessor.register_listener(UbloxProcessorEventType.NAVCLOCK_EVENT, ulogger.log_nav_clock)
uprocessor.register_listener(UbloxProcessorEventType.NAVSAT_EVENT, ulogger.log_nav_sat)
uprocessor.register_listener(UbloxProcessorEventType.TIMEPULSE_EVENT, ulogger.log_timepulse)
uprocessor.register_listener(UbloxProcessorEventType.RAWX_EVENT, ulogger.log_rawx)
uprocessor.register_listener(UbloxProcessorEventType.SURVEYIN_EVENT, ulogger.log_survey_in)
uprocessor.register_listener(UbloxProcessorEventType.SURVEY_DONE, ulogger.log_survey_done)

#mqtt = GnssMqtt()

for cfg in configs:
    print("Processing config ", cfg)
    ureader.apply_configfile(cfg)

while True:
    try:
        (raw_data, ubx_msg) = ureader.ubr.read()
        if not ureader.is_ubx_message(ubx_msg):
            continue
        print(ubx_msg.identity)
        uprocessor.receive(ubx_msg)
        # if msg.identity in (''):
        #     print(msg.identity, msg.timestamp)
        #mqtt.publish(ubx_msg)
    except KeyboardInterrupt:
        ureader.exit()
    except:
        pass
