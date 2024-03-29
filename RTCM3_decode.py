#!/bin/python

#(*****************************************************************/
#/*                     CRC24 LOOKUP TABLE                        */
#/*****************************************************************)
crc24table =  (
 0x000000, 0x864CFB, 0x8AD50D, 0x0C99F6, 0x93E6E1, 0x15AA1A,
 0x1933EC, 0x9F7F17, 0xA18139, 0x27CDC2, 0x2B5434, 0xAD18CF,
 0x3267D8, 0xB42B23, 0xB8B2D5, 0x3EFE2E, 0xC54E89, 0x430272,
 0x4F9B84, 0xC9D77F, 0x56A868, 0xD0E493, 0xDC7D65, 0x5A319E,
 0x64CFB0, 0xE2834B, 0xEE1ABD, 0x685646, 0xF72951, 0x7165AA,
 0x7DFC5C, 0xFBB0A7, 0x0CD1E9, 0x8A9D12, 0x8604E4, 0x00481F,
 0x9F3708, 0x197BF3, 0x15E205, 0x93AEFE, 0xAD50D0, 0x2B1C2B,
 0x2785DD, 0xA1C926, 0x3EB631, 0xB8FACA, 0xB4633C, 0x322FC7,
 0xC99F60, 0x4FD39B, 0x434A6D, 0xC50696, 0x5A7981, 0xDC357A,
 0xD0AC8C, 0x56E077, 0x681E59, 0xEE52A2, 0xE2CB54, 0x6487AF,
 0xFBF8B8, 0x7DB443, 0x712DB5, 0xF7614E, 0x19A3D2, 0x9FEF29,
 0x9376DF, 0x153A24, 0x8A4533, 0x0C09C8, 0x00903E, 0x86DCC5,
 0xB822EB, 0x3E6E10, 0x32F7E6, 0xB4BB1D, 0x2BC40A, 0xAD88F1,
 0xA11107, 0x275DFC, 0xDCED5B, 0x5AA1A0, 0x563856, 0xD074AD,
 0x4F0BBA, 0xC94741, 0xC5DEB7, 0x43924C, 0x7D6C62, 0xFB2099,
 0xF7B96F, 0x71F594, 0xEE8A83, 0x68C678, 0x645F8E, 0xE21375,
 0x15723B, 0x933EC0, 0x9FA736, 0x19EBCD, 0x8694DA, 0x00D821,
 0x0C41D7, 0x8A0D2C, 0xB4F302, 0x32BFF9, 0x3E260F, 0xB86AF4,
 0x2715E3, 0xA15918, 0xADC0EE, 0x2B8C15, 0xD03CB2, 0x567049,
 0x5AE9BF, 0xDCA544, 0x43DA53, 0xC596A8, 0xC90F5E, 0x4F43A5,
 0x71BD8B, 0xF7F170, 0xFB6886, 0x7D247D, 0xE25B6A, 0x641791,
 0x688E67, 0xEEC29C, 0x3347A4, 0xB50B5F, 0xB992A9, 0x3FDE52,
 0xA0A145, 0x26EDBE, 0x2A7448, 0xAC38B3, 0x92C69D, 0x148A66,
 0x181390, 0x9E5F6B, 0x01207C, 0x876C87, 0x8BF571, 0x0DB98A,
 0xF6092D, 0x7045D6, 0x7CDC20, 0xFA90DB, 0x65EFCC, 0xE3A337,
 0xEF3AC1, 0x69763A, 0x578814, 0xD1C4EF, 0xDD5D19, 0x5B11E2,
 0xC46EF5, 0x42220E, 0x4EBBF8, 0xC8F703, 0x3F964D, 0xB9DAB6,
 0xB54340, 0x330FBB, 0xAC70AC, 0x2A3C57, 0x26A5A1, 0xA0E95A,
 0x9E1774, 0x185B8F, 0x14C279, 0x928E82, 0x0DF195, 0x8BBD6E,
 0x872498, 0x016863, 0xFAD8C4, 0x7C943F, 0x700DC9, 0xF64132,
 0x693E25, 0xEF72DE, 0xE3EB28, 0x65A7D3, 0x5B59FD, 0xDD1506,
 0xD18CF0, 0x57C00B, 0xC8BF1C, 0x4EF3E7, 0x426A11, 0xC426EA,
 0x2AE476, 0xACA88D, 0xA0317B, 0x267D80, 0xB90297, 0x3F4E6C,
 0x33D79A, 0xB59B61, 0x8B654F, 0x0D29B4, 0x01B042, 0x87FCB9,
 0x1883AE, 0x9ECF55, 0x9256A3, 0x141A58, 0xEFAAFF, 0x69E604,
 0x657FF2, 0xE33309, 0x7C4C1E, 0xFA00E5, 0xF69913, 0x70D5E8,
 0x4E2BC6, 0xC8673D, 0xC4FECB, 0x42B230, 0xDDCD27, 0x5B81DC,
 0x57182A, 0xD154D1, 0x26359F, 0xA07964, 0xACE092, 0x2AAC69,
 0xB5D37E, 0x339F85, 0x3F0673, 0xB94A88, 0x87B4A6, 0x01F85D,
 0x0D61AB, 0x8B2D50, 0x145247, 0x921EBC, 0x9E874A, 0x18CBB1,
 0xE37B16, 0x6537ED, 0x69AE1B, 0xEFE2E0, 0x709DF7, 0xF6D10C,
 0xFA48FA, 0x7C0401, 0x42FA2F, 0xC4B6D4, 0xC82F22, 0x4E63D9,
 0xD11CCE, 0x575035, 0x5BC9C3, 0xDD8538 );

#(**********************************************************************
# * Compute the CRC24 checksum using a lookup table method.
# *
# *********************************************************************)



head_size = 0

class Msg_1077(object):
    message_number = 0
    reference_station_id = 0
    gps_epoch_time = 0
    multiple_message_bit = 0
    idos = 0
    clock_steering_indicator = 0
    external_clock_indicator = 0
    gps_dsi = 0
    gps_si = 0

    nsat = 0
    nsig = 0
    sats = [0]*512
    sigs = [0]*512
    cellmask = [0]*4000

class RTCM3:
    def __init__(self):
        self.buffer1 = bytearray((''.encode('ASCII'))*10000)
        self.buffer2 = bytearray((''.encode('ASCII'))*10000)
        self.length = 0
        self.length2 = 0
        self.msg_id = 0
        self.msg_id2 = 0

    def decode(self, data, length, msg_id):
        computed_crc = self._crc_normal(data[0:length+3])
        crc = data[3+length]
        crc = crc << 8
        crc = crc | data[3+length+1]
        crc = crc << 8
        crc = crc | data[3+length+2]

        if crc == computed_crc:
            data = data[3:length+3]
            print("crc success!")
        else:
            print("msg "+str(msg_id)+" crc failed!!!!!!")

        if msg_id == 1077:
            msg_1077, ncell = self._decode_1077(data)

            if head_size+msg_1077.nsat*36+ncell*80>(length+3)*8:
                print("rtcm3 1077 length error!!!!")
                print("result: " + str(head_size+msg_1077.nsat*36+ncell*80))
                print("length+3: " + str((length+3)*8))

    def _crc_normal (self, message_buffer):
        crc = 0
        #   print "CRC Length: " + str(len(Message_Buffer))
        for b in message_buffer:
            crc = crc24table[((crc >> 16) ^ b) & 0xFF] ^ (crc << 8);
        return(crc & 0xFFFFFF);

    def _makeBitArray(self, data):
        current_index=0
        bitArray = ((len(data)+6)*8)*['0']
        for b in data:
            for i in range(0,8):
                if (b & 0x80) != 0:
                    bitArray[current_index]='1'
                b<<=1
                current_index+=1
        return(bitArray)

    def _bitValue(self, bitArray, start, length):
        s = ""
        for i in range(start,start+length):
            s += bitArray[i]
        return(int(s,2))

    def _decode_1077(self, data):
        msg_1077 = Msg_1077()
        msg_1077.nsat = 0
        msg_1077.nsig = 0
        msg_1077.sats = [0]*512
        msg_1077.sigs = [0]*512
        msg_1077.cellmask = [0]*4000

        bit_array = self._makeBitArray(data)
        current_bit = 12
        msg_1077.reference_station_id = self._bitValue(bit_array, current_bit, 12)
        current_bit += 12
        msg_1077.gps_epoch_time = self._bitValue(bit_array, current_bit, 30)*0.001
        current_bit += 30
        msg_1077.multiple_message_bit = self._bitValue(bit_array, current_bit, 1)
        current_bit += 1
        msg_1077.idos = self._bitValue(bit_array, current_bit, 3)
        current_bit += 3
        current_bit += 7
        msg_1077.clock_steering_indicator = self._bitValue(bit_array, current_bit, 2)
        current_bit += 2
        msg_1077.external_clock_indicator = self._bitValue(bit_array, current_bit, 2)
        current_bit += 2
        msg_1077.gps_dsi = self._bitValue(bit_array, current_bit, 1)
        current_bit += 1
        msg_1077.gps_si = self._bitValue(bit_array, current_bit, 3)
        current_bit += 3
        for i in range(1,65):
            mask = self._bitValue(bit_array, current_bit, 1)
            current_bit += 1
            if mask:
                msg_1077.sats[msg_1077.nsat] = i
                msg_1077.nsat += 1

        for i in range(1,33):
            mask = self._bitValue(bit_array, current_bit, 1)
            current_bit += 1
            if mask:
                msg_1077.sigs[msg_1077.nsig] = i
                msg_1077.nsig += 1

        ncell = 0
        print("current_id!!!!!: " + str(current_bit+24))
        for i in range(0, msg_1077.nsat * msg_1077.nsig):
            msg_1077.cellmask[i] = self._bitValue(bit_array, current_bit, 1)
            current_bit += 1
            if msg_1077.cellmask[i]:
                ncell += 1

        head_size = current_bit+24
        print("time: " + str(msg_1077.gps_epoch_time))
        print("satelites: " + str(msg_1077.nsat))
        print(msg_1077)
        return msg_1077, ncell

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

    def messages(self, inputfile):
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

    def decode_file(self, filename):
        for t, l, m in self.messages(filename):
            self.decode(m, l, t)


filename = '/Users/dorsic/Downloads/compare/mms.rtcm3'
filename = 'serial_raw_log.mix'
rtcm = RTCM3()
rtcm.decode_file(filename)
