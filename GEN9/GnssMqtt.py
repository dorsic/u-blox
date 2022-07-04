import json
import paho.mqtt.client as mqtt
import mqtt_connect
from GnssTime import GnssTime


class GnssMqtt(object):
    main_topic = 'rarach/timelab/gnss'
    PTOPIC_TIMTP = main_topic + '/timtp'
    PTOPIC_NAVSAT = main_topic + '/navsat'
    PTOPIC_CONNECT = main_topic + '/connected'
    gnssPrefixMap = {0: 'G', 1: 'S', 2: 'E', 3: 'B', 5: 'Y', 5: 'J', 6: 'R'}

    def __init__(self, name='zedf9t'):
        self.client = mqtt.Client(client_id="", clean_session=True, userdata="xpi0_zedf9t", protocol=mqtt.MQTTv311, transport="tcp")
        self.client.on_message=self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.name = name
        print("connecting to broker")
        self.connected = mqtt_connect.connect(self.client)
        if not self.connected:
            print("Unable to connect to MQTT broker server. Quiting.")
            return None

        self.client.loop_start()

        print("Publishing topics \n")
        print(self.PTOPIC_TIMTP + "")
        print(self.PTOPIC_NAVSAT + "")

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            print("Connected to MQTT broker.")
            # print("Subscribing to topics\n")
            # print(STOPIC_SET)
            # (result, mid) = self.client.subscribe(STOPIC_SET + "/#", qos=2)
            # if (result != 0):
            #     print("Error subscribing to topics.")
            #     return
            self._publish(self.PTOPIC_CONNECT, {"value": "CONNECTED"})
        else:
            print("Failed to connect to MQTT broker. Return Code " + str(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed to " + "" + " messages sucessfull. Mid is " + str(mid) + ", granted QOS is " + str(granted_qos))

    def on_message(self, client, userdata, message):
        try:
            payload = message.payload.decode("utf-8")
            print("message received  ", payload,\
                "topic",message.topic,"retained ",message.retain)
            if message.retain==1:
                print("This is a retained message")
            self.log(message.topic, payload)
            js = json.loads(payload)
            self.decode_command(message.topic, js)
            self.client.loop()
        except:
            print("Exception in mqtt on_message")

    def _decode_command(self, topic, message):
        #if topic.startswith(STOPIC_SET) and "required_temperature" in topic:
            #value = message["value"]
        print("Topic {0} not implemented".format(topic))

    def _publish(self, topic, msg, qos=0, retain=False):
        try:
            if self.client and self.connected:
                self.client.publish(topic, json.dumps(msg), qos=qos, retain=retain)
                #print("Published " + topic + " " + str(msg))
                print("Published " + topic)
        except:
            print("Unable to publish MQTT events.")
            if not self.connected:
                self.connected = mqtt_connect.connect(self.client)
                print("Client reconnected")

    def _prepare_TimTp(self, ubx_msg):
        ts = GnssTime.timestamp(ubx_msg.week, ubx_msg.towMS, ubx_msg.towSubMS)
        mjd = GnssTime.mjd2(ubx_msg.week, ubx_msg.towMS, ubx_msg.towSubMS)
        return [("/".join([self.PTOPIC_TIMTP, self.name]), {'@timestamp': ts, 'mjd': mjd, 'qerr': ubx_msg.qErr}, 0, False)]

    def _prepare_NavSat(self, ubx_msg):
        lts = GnssTime.now()
        week = GnssTime.week_fromts(lts)
        mjd = GnssTime.mjd2(week, ubx_msg.iTOW/1000.0, 0) # - leapseconds???
        ts = GnssTime.timestamp(week, ubx_msg.iTOW, 0)
        msgs = []
        svsUsed = 0
        for i in range(1, ubx_msg.numSvs+1):
            si = "{0:02}".format(i)
            sv = self.gnssPrefixMap[getattr(ubx_msg, "gnssId_"+si)] + "{0:02}".format(getattr(ubx_msg, "svId_"+si))
            elev = int(getattr(ubx_msg, "elev_"+si))
            azim = int(getattr(ubx_msg, "azim_"+si))
            cno = int(getattr(ubx_msg, "cno_"+si))
            qualityInd = int(getattr(ubx_msg, "qualityInd_"+si))
            svUsed = int(getattr(ubx_msg, "svUsed_"+si))
            if svUsed:
                svsUsed += 1
                msgs.append(
                    ("/".join([self.PTOPIC_NAVSAT, self.name, 'sv']), {'@timestamp': ts, 'sv': sv, 'elev': elev, 'azim': azim, 'cno': cno, 'qualityInd': qualityInd, 'svUsed': svUsed}, 0, False)
                )

        msgs.append(("/".join([self.PTOPIC_NAVSAT, self.name]), {'@timestamp': ts, 'mjd': mjd, 'numSvs': ubx_msg.numSvs, 'numSvsUsed': svsUsed}, 0, False))
        return msgs

    def _prepare_ubxmessage(self, ubx_msg):
        if ubx_msg.identity == "TIM-TP":
            return self._prepare_TimTp(ubx_msg)
        elif ubx_msg.identity == "NAV-SAT":
            return self._prepare_NavSat(ubx_msg)
        return []

    def publish(self, ubx_msg):
        msgs = self._prepare_ubxmessage(ubx_msg)
        for topic, msg, qos, retain in msgs:
            self._publish(topic, msg, qos, retain)