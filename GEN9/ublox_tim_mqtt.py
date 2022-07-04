import serial
import ublox_gps
from timtp2 import TimTm2
import paho.mqtt.client as mqtt
import mqtt_connect

main_topic = 'rarach/timelab/ublox'

class Ublox_TIM(object):

    TOPIC_TIMTM = main_topic + '/timtm'

    def __init__(self, serialPort='/dev/ttyAMA0', baudRate=115200):
        port = serial.Serial(serialPort, baudRate, timeout=3)
        self.gps = ublox_gps.UbloxGps(port)

        self.client = mqtt.Client(client_id="", clean_session=True, userdata="rpi3_ublox", protocol=mqtt.MQTTv311, transport="tcp")
        self.client.on_message=self.on_message
        print("connecting to broker")
        self.connected = mqtt_connect.connect(self.client)
        if not self.connected:
            print("Unable to connect to MQTT broker server. Quiting.")
            return None

        self.client.loop_start()

        print("Publishing topic", self.TOPIC_TIMTM)

    def execute(self):
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.MON_CLS, 
                                        ublox_gps.sparkfun_predefines.TIM_CLS,
                                        ublox_gps.sparkfun_predefines.NAV_CLS,
                                        ublox_gps.sparkfun_predefines.CFG_CLS])
        while True:
            try:
                msg = parse_tool.receive_from(self.gps.hard_port)
                if TimTm2.isMessageOf(msg):
                    try:
                        if self.client and self.connected:
                            timtm = TimTm2(ubx_msg=msg)
                            j = timtm.json
                            self.client.publish(self.TOPIC_TIMTM, timtm.json, qos=0)
                            print("Published ", str(j))
                    except:
                        print("Unable to publish MQTT events.")
            except KeyboardInterrupt:
                print('interrupted')
                self.client.loop_stop()
                return
            except:
                pass

    def on_message(self, client, userdata, message):
        pass

def main():
    u = Ublox_TIM(serialPort='/dev/ttyS0')
    u.execute()
        
if __name__ == '__main__':
    main()