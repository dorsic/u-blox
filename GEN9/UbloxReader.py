import os
from datetime import datetime
from pyubx2 import UBXReader, UBXMessage, ubxtypes_configdb
from serial import Serial

class UbloxReader():
    ubr = None
    sport = None

    def __init__(self, serialport='/dev/ttyS0', baudrate=115200, configdir='./'):
        self.sport = Serial(serialport, baudrate=baudrate)
        self.configdir = configdir
        self.ubr = UBXReader(self.sport)
    
    @staticmethod
    def is_ubx_message(ubx_msg):
        return hasattr(ubx_msg, 'identity')

    # config file format from u-Center Generation 9 Advanced Configuration tool
    def apply_valset(self, layer, cmd, value, timeout=3):
        msg = UBXMessage.config_set(layer, ubxtypes_configdb.TXN_NONE, [(cmd, value)])
        self.sport.write(msg.serialize())
        st = datetime.now()
        while True:
            try:
                (raw_data, parsed_data) = self.ubr.read()
                if self.is_ubx_message(parsed_data):                    
                    if (parsed_data.identity == 'ACK-ACK'):
                        return True
                    if (parsed_data.identity == 'ACK-NAK'):
                        return False
                if ((datetime.now()-st).seconds > timeout):
                    return False
            except KeyboardInterrupt:
                self.exit()   

    def apply_valdel(self, layer, cmd, timeout=3):
        msg = UBXMessage.config_del(layer, ubxtypes_configdb.TXN_NONE, [cmd])
        self.sport.write(msg.serialize())
        st = datetime.now()
        while True:
            try:
                (raw_data, parsed_data) = self.ubr.read()
                if self.is_ubx_message(parsed_data):
                    if (parsed_data.identity == 'ACK-ACK'):
                        return True
                    if (parsed_data.identity == 'ACK-NAK'):
                        return False
                if ((datetime.now()-st).seconds > timeout):
                    return False
            except KeyboardInterrupt:
                self.exit()   

    def apply_configfile(self, config_filename):
        delcmd = {'RAM': [], 'BBR': [], 'Flash': []}
        setcmd = {'RAM': [], 'BBR': [], 'Flash': []}
        deleting = False
        with open(config_filename, 'r') as cf:
            for line in cf:
                try:
                    ln = line.strip()
                    if not ln:
                        continue
                    if ln.startswith('#'):
                        continue
                    if ln.startswith('[del]'):
                        deleting = True
                        continue
                    if ln.startswith('[set]'):
                        deleting = False
                        continue
                    cmd = ln.split('#')[0]
                    cmd = ' '.join(cmd.split()).split(' ')
                    cmd_id = cmd[1].replace('-', '_')
                    if not deleting:
                        cmd_val = int(cmd[2], 16)
                    if cmd[0] not in setcmd.keys():
                        print("wARNING> Ignoring config message ", cmd)
                    if deleting:
                        delcmd[cmd[0]].append(cmd_id)
                    else:
                        setcmd[cmd[0]].append((cmd_id, cmd_val))
                except:
                    print('ERROR in config file at line "', ln, '"')
                    exit(1)

        for layer, layer_id in [('Flash', ubxtypes_configdb.SET_LAYER_FLASH), ('BBR', ubxtypes_configdb.SET_LAYER_BBR), ('RAM', ubxtypes_configdb.SET_LAYER_RAM)]:
            for cmd in delcmd[layer]:
                if not self.apply_valdel(layer_id, cmd):
                    print("WARNING: Unable to del ", cmd, " in ", layer)
            for cmd in setcmd[layer]:
                if not self.apply_valset(layer_id, cmd[0], cmd[1]):
                    print("WARNING: Unable to set value ", cmd, " in ", layer)