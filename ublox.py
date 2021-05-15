import serial
import ublox_gps

import debugpy
# Allow other computers to attach to debugpy at this IP address and port.
#debugpy.listen(('192.168.1.72', 5678))

# Pause the program until a remote debugger is attached
#debugpy.wait_for_client()

sdev = '/dev/ttyAMA0'
baudrate = 115200

def get_gnss(gps):
    try:
        msg = gps.send_message(ublox_gps.sparkfun_predefines.MON_CLS, gps.mon_ms.get('GNSS'))
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.MON_CLS])
        msg = parse_tool.receive_from(gps.hard_port)
        return msg
    except (ValueError, IOError) as err:
        print(err)

def get_time(gps):
    try:
        msg = gps.send_message(ublox_gps.sparkfun_predefines.TIM_CLS, gps.time_ms.get('TM2'))
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.TIM_CLS])
        msg = parse_tool.receive_from(gps.hard_port)
        return msg
    except (ValueError, IOError) as err:
        print(err)

def get_tp(gps):
    try:
        msg = gps.send_message(ublox_gps.sparkfun_predefines.TIM_CLS, gps.time_ms.get('TP'))
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.TIM_CLS])
        msg = parse_tool.receive_from(gps.hard_port)
        return msg
    except (ValueError, IOError) as err:
        print(err)

def get_sbas(gps):
    try:
        msg = gps.send_message(ublox_gps.sparkfun_predefines.NAV_CLS, gps.nav_ms.get('SBAS'))
        parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.NAV_CLS])
        msg = parse_tool.receive_from(gps.hard_port)
        return msg
    except (ValueError, IOError) as err:
        print(err)

def nmea_stream(gps):
    while True:
        try:
            msg = gps.hard_port.readline().decode('utf-8')
            print(msg)
        except KeyboardInterrupt:
            print('interrupted!')
            return
        except:
            pass

def ubx_stream(gps):
    parse_tool = ublox_gps.core.Parser([ublox_gps.sparkfun_predefines.MON_CLS, 
                                        ublox_gps.sparkfun_predefines.TIM_CLS,
                                        ublox_gps.sparkfun_predefines.NAV_CLS,
                                        ublox_gps.sparkfun_predefines.CFG_CLS])
    while True:
        try:
            msg = parse_tool.receive_from(gps.hard_port)
            print(msg)
        except KeyboardInterrupt:
            print('interrupted')
            return
        except:
            pass
            #print("Unknown error")

def configure(gps):
    try:
        # UBX-NAV-TIMEGPS
        ubx_msg = ublox_gps.sparkfun_predefines.CFG_CLS[gps.cfg_ms.get('MSG')]
        ubx_msg.set_values({"msgClass": 0x01, "msgID": 0x20, "rate": 1})        
        msg = gps.send_message(ublox_gps.sparkfun_predefines.CFG_CLS, gps.cfg_ms.get('MSG'), ubx_msg.payload())
        print(msg)

        # UBX-TIM-TM2
        ubx_msg = ublox_gps.sparkfun_predefines.CFG_CLS[gps.cfg_ms.get('MSG')]
        ubx_msg.set_values({"msgClass": 0x0D, "msgID": 0x03, "rate": 1})
        msg = gps.send_message(ublox_gps.sparkfun_predefines.CFG_CLS, gps.cfg_ms.get('MSG'), ubx_msg.payload())
        print(msg)

        # UBX-TIM-TP
        ubx_msg = ublox_gps.sparkfun_predefines.CFG_CLS[gps.cfg_ms.get('MSG')]
        ubx_msg.set_values({"msgClass": 0x0D, "msgID": 0x01, "rate": 1})
        msg = gps.send_message(ublox_gps.sparkfun_predefines.CFG_CLS, gps.cfg_ms.get('MSG'), ubx_msg.payload())
        print(msg)


    except (ValueError, IOError) as err:
        print(err)


def main():
    port = serial.Serial(sdev, baudrate, timeout=1)
    gps = ublox_gps.UbloxGps(port)

    print("Configuring UBX Messages")
    configure(gps)
    print("Listening for UBX Messages")
    #msg = get_gnss(gps)
    #print (msg)
    #msg = get_sbas(gps)
    #print (msg)
    #msg = get_time(gps)
    #print (msg) 
    ubx_stream(gps)
        
if __name__ == '__main__':
    main()


