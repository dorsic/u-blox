from ublox_gps import sparkfun_predefines, core
import struct
from collections import namedtuple
from enum import Enum
from typing import List


class UBX_FType(Enum):
    U1 = 'U1'
    I1 = 'I1'
    X1 = 'X1'
    RU1_3 = 'RU1_3'
    U2 = 'U2'
    I2 = 'I2'
    X2 = 'X2'
    RU2_5 = 'RU2_5'
    U4 = 'U4'
    I4 = 'I4'
    X4 = 'X4'
    R4 = 'R4'
    I8 = 'I8'
    R8  ='R8'
    CH = 'CH'

class UBX_BitType(Enum):
    X1 = 'X1'
    X2 = 'X2'
    X4 = 'X4'

class UBX_Field(core.Field):
    def __init__(self, name: str, _type: UBX_FType):
        self.value = None
        super().__init__(name, _type.value)

class UBX_Flag(core.Flag):
    def __init__(self, name: str, start: int, stop: int, codes: namedtuple = None):
        self.value = None
        self.codes = codes
        super().__init__(name, start, stop)

class UBX_BitField(core.BitField):

    fields_dict = {}

    def __init__(self, name: str, type_: UBX_BitType, subfields: List[UBX_Flag]):
        super().__init__(name, type_.value, subfields)

    def __getattribute__(self, name):
        if name == 'fields_dict':
            return super(UBX_BitField, self).__getattribute__(name)
        elif name in self.fields_dict:
            return self.fields_dict[name].value
        else:
            return super(UBX_BitField, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if name == 'fields_dict':
            super(UBX_BitField, self).__setattr__(name, value)
        elif name in self.fields_dict:
            self.fields_dict[name].value = value
        else:
            super(UBX_BitField, self).__setattr__(name, value)

class UBX_MSG(core.Message):
    fields_dict = {}    

    def __init__(self, id_: int, name: str, fields: list):
        super().__init__(id_, name, fields)

    def __getattribute__(self, name):
        if name == 'fields_dict':
            return super(UBX_MSG, self).__getattribute__(name)
        elif name in self.fields_dict:
            if isinstance(self.fields_dict[name], UBX_BitField):
                return self.fields_dict[name]
            return self.fields_dict[name].value
        else:
            return super(UBX_MSG, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if name == 'fields_dict':
            super(UBX_MSG, self).__setattr__(name, value)
        elif name in self.fields_dict:
            self.fields_dict[name].value = value
        else:
            super(UBX_MSG, self).__setattr__(name, value)

    def set_field_value(self, field_name: str, value):
        flds = [f for f in self._fields if f.name==field_name]
        if len(flds) != 1:
            raise KeyError('Uable to set field value. Message {0} of class 0x{1:02X} does not contain field with name "{2}".'
                .format(self.name, self._id, field_name))
        flds[0].value = value

    def set_values(self, values: dict):
        for field_name in values:
            self.set_field_value(field_name, values[field_name])

    def parse2(self, nt: namedtuple):
        for sc in type(self).__subclasses__():
            if sc.__name__.startswith('UBX_'+nt[0]+'_'+nt[1]):
                m = sc()
                for f in m.fields:
                    if isinstance(f, UBX_Field):
                        f.value = getattr(nt[2], f.name)
                    elif isinstance(f, UBX_BitField):
                        for i in range(len(f._subfields)):
                            f._subfields[i].value = getattr(nt[2], f.name)[i]
                    else:
                        raise ValueError('Unknown type of {} field'.format(f))
                return m

    def parse(self, payload: bytes):
        nt = super().parse(payload)
        for sc in type(self).__subclasses__():
            if sc.__name__.startswith('UBX_'+nt[0]+'_'+nt[1]):
                m = sc()
                for f in m.fields:
                    if isinstance(f, UBX_Field):
                        f.value = getattr(nt[2], f.name)
                    elif isinstance(f, UBX_BitField):
                        for i in range(len(f._subfields)):
                            f._subfields[i].value = getattr(nt[2], f.name)[i]
                    else:
                        raise ValueError('Unknown type of {} field'.format(f))
                return m
                #msg[2]._asdict()['ecefX']
                #getattr(msg[2], 'iTOW')
                #msg[2].flags[3]
                #msg[2].flags.TOWSET
                #getattr(msg[2].flags, 'TOWSET')


        return

    def payload(self) -> bytes:
        #typemap = {'U1': 'c', 'I1': 'b', 'X1': 'c', 'RU1_3': '',
        #            'U2': 'H', 'I2': 'h', 'X2': 'H', 'RU2_5': '',
        #            'U4': 'I', 'I4': 'i', 'X4': 'I', 'R4': 'f', 'I8': 'q', 'R8': 'd', 'CH': 'c'}
        values = []
        for f in self._fields:
            values.append(f.value)
        return struct.pack(self.fmt, *values)

class UBX_TIM_TP2(UBX_MSG):
    class UBX_TIM_TP2_flags(UBX_BitField):
        name = 'flags'
        _type = UBX_BitType.X1
        mode, run, newFailingEdge, utc, time, newRisingEdge = [None] * 6
        timebase = namedtuple('timebase', ['Receiver_Time', 'GNSS_Time', 'UTC'])(0, 1, 2)

        def __init__(self):
            self.bitfields = [
                UBX_Flag('mode', 0, 1, namedtuple('mode', ['single', 'running'])(0, 1)),
                UBX_Flag('run', 1, 2, namedtuple('run', ['armed', 'stopped'])(0, 1)),
                UBX_Flag('newFailingEdge', 2, 3),
                UBX_Flag('timebase', 3, 5, self.timebase),
                UBX_Flag('utc', 5, 6, namedtuple('utc', ['UTC_not_available', 'UTC_available'])(0, 1)),
                UBX_Flag('time', 6, 7, namedtuple('time', ['time_not_valid', 'time_valid'])(0, 1)),
                UBX_Flag('newRisingEdge', 7, 8)
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    cls_, id_ = 0x06, 0x03         
    ch, count, wnR, wnF, towMsR, towSubMsR, towMsF, towSubMsF, accEst = [None] * 9
    flags = UBX_TIM_TP2_flags()

    def __init__(self):
        self.fields = [
                UBX_Field('ch', UBX_FType.U1),
                self.UBX_TIM_TP2_flags(),
                UBX_Field('count', UBX_FType.U2),
                UBX_Field('wnR', UBX_FType.U2),
                UBX_Field('wnF', UBX_FType.U2),
                UBX_Field('towMsR', UBX_FType.U4),
                UBX_Field('towSubMsR', UBX_FType.U4),
                UBX_Field('towMsF', UBX_FType.U4),
                UBX_Field('towSubMsF', UBX_FType.U4),
                UBX_Field('accEst', UBX_FType.U4)]
        self.fields_dict = dict((f.name, f) for f in self.fields)
        super().__init__(self.id_, self.__class__.__name__, self.fields)

class UBX_CFG_PRT(UBX_MSG):

    class UBX_CFG_PRT_txReady(UBX_BitField):
        name = 'txReady'
        _type = UBX_BitType.X2
        en, pin = [None] * 2
        pol = namedtuple('Polarity', ['High_active', 'Low_active'])(0, 1)
        thres = namedtuple('Threshold', ['no_threshold']+['byte'+str(i) for i in range(8, 4096, 8)], defaults=[i for i in range(8, 4096, 8)])

        def __init__(self):
            self.bitfields = [
                UBX_Flag('en', 0, 1, self.pol),
                UBX_Flag('pol', 1, 2, self.pol),
                UBX_Flag('pin', 2, 7),
                UBX_Flag('thres', 8, 16, self.thres)
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    class UBX_CFG_PRT_mode(UBX_BitField):
        name = 'mode'
        _type = UBX_BitType.X4
        charLen = namedtuple('CharacterLength', ['bit5', 'bit6', 'bit7', 'bit8'])(0, 1, 2, 3)
        parity = namedtuple('Parity', ['Even_parity', 'Odd_parity', 'No_parity', 'Reserverd'])(0, 1, 256, 16)   # 000, 001, 10x, x1x
        nStopBits = namedtuple('StopBits', ['Stopbit1', 'Stopbit1_5', 'Stopbit2', 'Stopbit0_5'])(0, 1, 2, 3)

        def __init__(self):
            self.bitfields = [
                UBX_Flag('charLen', 6, 8, self.charLen),
                UBX_Flag('pariry', 9, 12, self.parity),
                UBX_Flag('nStopBits', 12, 14, self.nStopBits)
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    class UBX_CFG_PRT_inProtoMask(UBX_BitField):
        name = 'inProtoMask'
        _type = UBX_BitType.X2
        inUbx, inNmea, inRtcm, inRtcm3 = [None] * 4

        def __init__(self):
            self.bitfields = [
                UBX_Flag('inUbx', 0, 1),
                UBX_Flag('inNmea', 1, 2),
                UBX_Flag('inRtcm', 2, 3),
                UBX_Flag('inRtcm3', 5, 6)
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    class UBX_CFG_PRT_outProtoMask(UBX_BitField):
        name = 'outProtoMask'
        _type = UBX_BitType.X2
        inUbx, inNmea, inRtcm3 = [None] * 3

        def __init__(self):
            self.bitfields = [
                UBX_Flag('outUbx', 0, 1),
                UBX_Flag('outNmea', 1, 2),
                UBX_Flag('outRtcm3', 5, 6)
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    class UBX_CFG_PRT_flags(UBX_BitField):
        name = 'extendedTxTimeout'
        _type = UBX_BitType.X2
        extendedTxTimeout = None

        def __init__(self):
            self.bitfields = [
                UBX_Flag('extendedTxTimeout', 1, 2),
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    cls_, id_ = 0x06, 0x00        
    portID, baudRate = [None] * 2
    txReady = UBX_CFG_PRT_txReady()
    mode = UBX_CFG_PRT_mode()
    inProtoMask = UBX_CFG_PRT_inProtoMask()
    outProtoMask = UBX_CFG_PRT_outProtoMask()
    flags = UBX_CFG_PRT_flags()

    def __init__(self):
        self.fields = [
                UBX_Field('portID', UBX_FType.U1),
                UBX_Field('reserved1', UBX_FType.U1),
                self.UBX_CFG_PRT_txReady(),
                self.UBX_CFG_PRT_mode(),
                UBX_Field('baudRate', UBX_FType.U4),
                self.UBX_CFG_PRT_inProtoMask(),
                self.UBX_CFG_PRT_outProtoMask(),
                self.UBX_CFG_PRT_flags(),
                UBX_Field('reserved2', UBX_FType.U2)]
        self.fields_dict = dict((f.name, f) for f in self.fields)
        super().__init__(self.id_, self.__class__.__name__, self.fields)

class UBX_NAV_SOL(UBX_MSG):

    class UBX_NAV_SOL_flags(UBX_BitField):
        name = 'flags'
        _type = UBX_BitType.X1
        GPSfixOK, DiffSoln, WKNSET, TOWSET = [None] * 4

        def __init__(self):
            self.bitfields = [
                UBX_Flag('GPSfixOK', 0, 1),
                UBX_Flag('DiffSoln', 1, 2),
                UBX_Flag('WKNSET', 2, 3),
                UBX_Flag('TOWSET', 3, 4),
            ]
            self.fields_dict = dict((f.name, f) for f in self.bitfields)
            super().__init__(self.name, self._type, self.bitfields)

    cls_, id_ = 0x01, 0x06
    iTOW, fTOW, week, gpsFix, ecefX, ecefY, ecefZ, pAcc, ecefVX, ecefVY, ecefVZ, sAcc, pDOP, numSV = [None] * 14
    flags = UBX_NAV_SOL_flags()

    def __init__(self):
        self.fields = [
                UBX_Field('iTOW', UBX_FType.U4),
                UBX_Field('fTOW', UBX_FType.I4),
                UBX_Field('week', UBX_FType.I2),
                UBX_Field('gpsFix', UBX_FType.U1),
                self.UBX_NAV_SOL_flags(),
                UBX_Field('ecefX', UBX_FType.I4),
                UBX_Field('ecefY', UBX_FType.I4),
                UBX_Field('ecefZ', UBX_FType.I4),
                UBX_Field('pAcc', UBX_FType.U4),
                UBX_Field('ecefVX', UBX_FType.I4),
                UBX_Field('ecefVY', UBX_FType.I4),
                UBX_Field('ecefVZ', UBX_FType.I4),
                UBX_Field('sAcc', UBX_FType.U4),
                UBX_Field('pDOP', UBX_FType.U2),
                UBX_Field('reserved1', UBX_FType.U1),
                UBX_Field('numSV', UBX_FType.U1),
                UBX_Field('reserved2', UBX_FType.U4)]
        self.fields_dict = dict((f.name, f) for f in self.fields)
        super().__init__(self.id_, self.__class__.__name__, self.fields)

m = UBX_NAV_SOL()

flags = namedtuple('flags', ['GPSfixOK', 'DiffSoln', 'WKNSET', 'TOWSET'])
SOL = namedtuple('SOL', [f.name for f in m.fields])
nt = ('NAV', 'SOL', SOL(iTOW=167074000, fTOW=463836, week=2134, gpsFix=3, flags=flags(GPSfixOK=1, DiffSoln=0, WKNSET=1, TOWSET=13), ecefX=407505787, ecefY=125381478, ecefZ=472806895, pAcc=396, ecefVX=5, ecefVY=-1, ecefVZ=3, sAcc=37, pDOP=166, reserved1=2, numSV=15, reserved2=215776))
s = UBX_MSG(0x1, 'UBX_MSG', [])
n = s.parse2(nt)
print(n)