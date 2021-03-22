import machine
from qmc5883 import QMC5883
import utime

i2c  = machine.I2C( 0  , scl=machine.Pin(17), sda=machine.Pin(16), freq=1000 )



mag = QMC5883(i2c)
mag.set_calibration(-1980, 1577, -3975, -713, -1650, 1576);




if __name__ == "__main__":
    while True:
        a = mag.read(callibrated = True , scalled = False, smooothed = True)
        h  =mag.heading(a[0]  , a[1])
        print(h)
