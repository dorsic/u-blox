from ublox_tim_pyubx2 import Ublox_TIM, TIMTM2

#import ublox_tim_pyubx2

def read_ubx(ubx):
    print("Start reading ubx messages")
    for msg in ubx.ubx_stream():
        print("new message")
        print(msg)
        if (TIMTM2.isMessageOf(msg)):
            tm2 = TIMTM2(msg)
            print(tm2)


def main():
    ubx = Ublox_TIM(serialPort='/dev/cu.usbserial-14410', baudRate=115200)
    read_ubx(ubx)

if __name__ == '__main__':
    main()