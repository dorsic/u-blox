import pyubx2
import os
import json
from tqdm import tqdm

WAITING = 1         # waiting for the header occurence
INTERMEDIATE = 2     # valid header found and message is being processed
MESSAGE = 3         # full message is in the buffer

class UbxMessage(object):
    # https://pypi.org/project/pyubx2/

    #header = [b'\xb5', b'\x62']
    header = [181, 98]
    msgids = pyubx2.UBX_MSGIDS
    classes = pyubx2.UBX_CLASSES

    def __init__(self, msgIdsCheck=False):
        self._state = WAITING
        self._buffer = 65540 * [0]
        self._i = 0
        self._length = None
        self._msgid = None
        self.msgIdsCheck = msgIdsCheck

    def length(self):
        if self._length: 
            return length
        self._length = (self._buffer[5] << 8) + self._buffer[4]
        return self._length

    def addData(self, byte):
        if self._state == INTERMEDIATE:
            self._buffer[self._i] = byte
            self._i += 1
            if self._i-8 == self._length:
                self._state = MESSAGE
                return
        elif (self._state == WAITING or self._state == MESSAGE) and (self._i == 0 and byte == self.header[0]):
            self._state = WAITING
            self._buffer[self._i] = byte
            self._i += 1
        elif self._state == WAITING and (self._i == 1 and byte == self.header[1]):
            self._state = INTERMEDIATE
            self._buffer[self._i] = byte
            self._i += 1
        if self._i == 6:
            self.length()
        if self._i == 4 and self._msgIdsCheck:
            if not self.name:
                self.clear()

    def isMessage(self):
        if self._i-8 != self._length:
            return False
        #if self._buffer[2] not in self.classes:
        #    return False
        #if (self._buffer[2]+self._buffer[3]) not in self.msgids:
        #    return False
        return True

    def clear(self):
        self._i = 0
        self._length = None
        self._state = WAITING
        self._msgid = None

    def messages(self, inputfile):
        blocksize = 2**18
        with open(inputfile, 'rb') as fin:
            self.clear()
            buf = fin.read(blocksize)
            while buf:
                for bt in buf:
                    self.addData(bt)
                    if self.state == MESSAGE:
                        yield self.message
                        self.clear()
            buf = fin.read(blocksize)

    def messages2(self, inputfile, filter=None):
        with open(inputfile, 'rb') as fin:
            ureader = pyubx2.UBXReader(fin, True)
            #for (raw_data, parsed_data) in ureader:
            itr = iter(ureader)
            raw_data, parsed_data = next(itr)
            while parsed_data:
                if filter:
                    if parsed_data.identity in filter:
                        yield parsed_data
                else:
                    yield parsed_data
                try:
                    # we are able to skip one bad message at a time
                    raw_data, parsed_data = next(itr)
                except:
                    raw_data, parsed_data = next(itr)

    @property 
    def message(self):
        return self._buffer[0:self._i] if self.isMessage() else None

    @property
    def state(self):
        return self._state

    @property
    def msgid(self):
        if self._msgid:
            return self._msgid
        if self._i >= 4:
            self._msgid = b''.join([x.to_bytes(1, byteorder='big') for x in self._buffer[2:4]])
        return self._msgid
        
    @property
    def name(self):
        return pyubx2.UBX_MSGIDS[self.msgid] if self.msgid and (self.msgid in pyubx2.UBX_MSGIDS) else None

    @property
    def msgIdsCheck(self):
        return self._msgIdsCheck

    @msgIdsCheck.setter
    def msgIdsCheck(self, value):
        self._msgIdsCheck = value

    def trimfile(self, maxsize, inputfile, outputfile):
        blocksize = 2**18
        cnt = 1
        with open(inputfile, 'rb') as fin:
            with open(outputfile, 'wb') as fout:
                buf = fin.read(blocksize)
                while buf:
                    if (cnt < maxsize/blocksize):
                        fout.write(buf)
                        cnt += 1
                    else:
                        # find new last message and end
                        self.clear()
                        for bt in buf:
                            self.addData(bt)
                            fout.write(bt.to_bytes(1, byteorder='big'))
                            if self.state == MESSAGE:
                                return
                    buf = fin.read(blocksize)

class RtcmMessage(object):
    #header = [b'\xd3']
    header = [211]
    classes = [1005, 1077, 1087, 1097, 1127, 1230, 4072.0, 4072.1]

    def __init__(self, data=None):
        self._state = WAITING
        self._buffer = 8192 * [0]
        self._i = 0
        self._length = None
        if data:
            self._buffer = data
            self._i = len(data)
            self.length
            self.msgid
            self._state = MESSAGE if self.isMessage() else INTERMEDIATE

    def length(self):
        if self._length:
            return self._length
        if self._i < 2:
            return -1
        self._length = ((self._buffer[1] & 0x03) << 8) | self._buffer[2]
        return self._length

    def msgid(self):
        if self._msgid:
            return _msgid
        if self._i < 5:
            return -1
        self._msgid = self._buffer[3] << 4 | ((self._buffer[4] & 0xf0) >> 4) 
        return self._msgid
    
    def _message_length(self, data):
        result = -1
        if len(data)>2:
            result = ((data[1] & 0x03) << 8) | data[2]
        return result

    def _message_id(self, data):
        result = -1
        if len(data) > 4:
            result = data[3] << 4 | ((data[4] & 0xf0) >> 4) 
        return result

    def addData(self, byte):
        if self._state == INTERMEDIATE:
            self._buffer[self._i] = byte
            self._i += 1
            if self._i-6 == self._length:
                self._state = MESSAGE
        elif (self._state == WAITING or self._state == MESSAGE) and (self._i == 0 and byte == self.header[0]):
            self._buffer[self._i] = byte
            self._i += 1
            self._state = INTERMEDIATE
        if self._i == 3:
            self.length()

    def isMessage(self):
        if self._i-6 != self._length:
            return False
        return True

    def clear(self):
        self._i = 0
        self._length = None 
        self._state = WAITING
    
    def messages(self, inputfile):
        blocksize = 2**18
        with open(inputfile, 'rb') as fin:
            buf = fin.read(blocksize)
            self.clear()
            while buf:
                for bt in buf:
                    self.addData(bt)
                    if self.state == MESSAGE:
                        yield self.message
                        self.clear()
                buf = fin.read(blocksize)

    def messages2(self, inputfile):
        blocksize = 2**18
        buffer = [0]*(2*blocksize)
        with open(inputfile, 'rb') as fin:
            r = fin.read(blocksize)
            n = len(r)
            i, j = 0, n
            buffer[i:j] = list(r)
            while n > 0:
                while buffer[i] != 0xd3 and i < j:
                    i += 1
                if (i < j):
                    l = self._message_length(buffer[i:i+5])
                    t = self._message_id(buffer[i:i+5])
                    if i+l+6 > blocksize:
                        # uncomplete message in the buffer
                        r = fin.read(blocksize)
                        n = len(r)
                        buffer[j:j+n] = list(r)
                        buffer[0:j+n-i] = buffer[i:j+n]
                        j = j+n-i
                        i = 0
                    if l > 0 and t > 0:
                        yield t, l, buffer[i:i+l+6]
                        i += l+6
                    else:
                        # invalid message size or type
                        i += 1
                else:
                    r = fin.read(blocksize)
                    n = len(r)
                    buffer[0:n] = list(r)
                    i = 0  

    @property 
    def message(self):
        return self._buffer[0:self._i] if self.isMessage() else None

    @property
    def state(self):
        return self._state

class NmeaMessage(object):
    #header = [b'\x24', b'\x47']
    header = [36, 71]

    def __init__(self):
        self._state = WAITING
        self._buffer = 8192 * [0]
        self._i = 0
        self._length = None

    def addData(self, byte):
        if self._state == INTERMEDIATE:
            if (byte < 32 or 128 < byte) and (byte not in [10, 13]):
                self.clear()
                return

            self._buffer[self._i] = byte
            self._i += 1
            if self.isMessage():
                self._state = MESSAGE
        elif byte == self.header[0]:
            self.clear()
            self._buffer[self._i] = byte
            self._i += 1
            self._state = WAITING
        elif self._state == WAITING and (self._i == 1 and byte == self.header[1]):
            self._buffer[self._i] = byte
            self._i += 1
            self._state = INTERMEDIATE


    def isMessage(self):
        if self._i < 5:
            return False
        if self._buffer[self._i-5] != 42:
            return False
        if self._buffer[self._i-1] != 10:
            return False
        return True

    def clear(self):
        self._i = 0
        self._length = None
        self._state = WAITING
        
    @property 
    def message(self):
        return self._buffer[0:self._i]

    @property
    def state(self):
        return self._state

class MessageFilter():

    def __init__(self, filterMessages):
        self.filter = filterMessages

    # returns true if the message is in the filter
    def filter(message):
        return message.name in self.filter

class UbloxMessageSplitter(object):

    nmea = NmeaMessage()
    ubx = UbxMessage()
    rtcm = RtcmMessage()

    def __init__(self, filename, outputfilename):
        self.filename = filename
        self.outputfilename = outputfilename

    def split(self, checkUbxMsgIds=False):
        blocksize = 2**18
        memory = None
        output = None
        self.ubx.msgIdsCheck = True
        counter = [0, 0, 0]
        filesize = os.stat(self.filename).st_size
        pbar = tqdm(total=filesize)
        with open(self.filename, 'rb') as fin:
            with open(self.outputfilename + '.nmea', 'wb') as fnmea:
                with open(self.outputfilename + '.ubx', 'wb') as fubx:
                    with open(self.outputfilename + '.rtcm3.o', 'wb') as frctm:
                        buf = fin.read(blocksize)
                        while buf:
                            for b in buf:
                                if self.ubx.state == INTERMEDIATE:
                                    self.ubx.addData(b)
                                elif self.rtcm.state == INTERMEDIATE:
                                    self.rtcm.addData(b)
                                # even when nmea.state == INTERMEDIATE we want to send the data to ubx and rtcm, maybe its an incomplete nmea message, so we can start new.
                                #elif self.nmea.state == INTERMEDIATE:
                                #    self.nmea.addData(b)
                                else:
                                    self.nmea.addData(b)
                                    self.ubx.addData(b)
                                    self.rtcm.addData(b)

                                if self.nmea.state == MESSAGE:
                                    output = fnmea
                                    memory = self.nmea.message
                                    counter[0] += 1
                                elif self.ubx.state == MESSAGE:
                                    output = fubx
                                    memory = self.ubx.message
                                    counter[1] += 1
                                elif self.rtcm.state == MESSAGE:
                                    output = frctm
                                    memory = self.rtcm.message
                                    counter[2] += 1

                                if memory:
                                    output.write(self.listtobytes(memory))
                                    self.nmea.clear()
                                    self.ubx.clear()
                                    self.rtcm.clear()
                                    memory = None
                                    #output = None
                            buf = fin.read(blocksize)
                            pbar.update(blocksize)
        pbar.close()
        return counter

    def search(self, bts):
        with open(self.filename, 'rb') as fin:
            buf = fin.read(65536)
            abuf = buf
            cnt = 0
            while buf:
                if bts in abuf:
                    return True
                buf = fin.read(65536)
                abuf = abuf[-4:] + buf
                cnt += 1
            return cnt                

    def trimfile(self, type, maxsize, input, output):
        if type == 'ubx':
            self.ubx.trimfile(maxsize, input, output)

    def listtobytes(self, byteslist):
        return b''.join([x.to_bytes(1, byteorder='big') for x in byteslist])

    def midmessages(self, type, inputfile, outputfile, start=0, stop=None):
        cnt = 0
        stop = stop if stop else os.stat(inputfile).st_size
        with open(outputfile, 'wb') as fout:
            if type == 'rtcm':
                for msg in self.rtcm.messages(inputfile):
                    if cnt >= start and cnt <= stop:
                        fout.write(self.listtobytes(msg))
                    if cnt > stop:
                        break
                    cnt += 1
        return cnt

SPLIT_MIX = 1
FILTER_UBX = 2
FILTER_RTCM = 3

mode = SPLIT_MIX
filename = '/Users/dorsic/Development/data-ublox/palisady/ublox-P8-balkonNW.mix'
#outputfilename = '/Users/dorsic/Development/github/u-blox/measurements/vrchslatina/ublox-9f659cc9-5572-4c47-bf35-1ad5a5c13857'
outputfilename = filename[:-4]
filtered_ubx_in = outputfilename + '.ubx'
filtered_ubx_out = outputfilename + '.json'

if mode == SPLIT_MIX:
    #### SPLITTING 
    splitter = UbloxMessageSplitter(filename, outputfilename)
    cnt = splitter.split()
    #cnt = splitter.midmessages('rtcm', filename, 'zed9t_palisady-40+.rtcm3', 40)
    # cnt = splitter.search(b'\xb5\x62\x02\x59')
    print(cnt)
    #splitter.trimfile('ubx', 262144000, filename, outputfilename)
elif mode == FILTER_UBX:
    ubx = UbxMessage()
    stats = {}
    with open(filtered_ubx_out, 'w') as fout:
        for msg in ubx.messages2(filtered_ubx_in, filter=['TIM-TP']):
            stats[msg.identity] = stats[msg.identity] + 1 if msg.identity in stats else 1
            js = {a: (msg.__dict__[a]) if not isinstance(msg.__dict__[a], bytes) else ord(msg.__dict__[a]) for a in msg._get_dict()}
            js["msg"] = "TIM-TP"
            fout.write(json.dumps(js))
            fout.write('\n')
            #print(msg)
    print(stats)
elif mode == FILTER_RTCM:
    #### RTCM FILTERING
    stats = {}
    rtcm = RtcmMessage()
    with open(outputfilename, 'wb') as fout:
        for t, l, m in rtcm.messages2(filename):
            stats[t] = stats[t] + 1 if t in stats else 1
            #if t in [1077]:
            fout.write(bytearray(m))
    print(stats)
print('DONE.')

