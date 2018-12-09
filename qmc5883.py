#
# initial code by Sebastian Folz, M.Sc. at
# http://nobytes.blogspot.com/2018/03/qmc5883-magnetic-field-sensor.html
# which, I assume, was itself ported from C-Code
# See also https://github.com/RigacciOrg/py-qmc5883l
#
# Changes and Additions:
# - port to micropython's I2C methods
# - add method read_scaled() for scaled values
# - reading register values into a static buffer
# - parsed register values in one single struct call
# - fixed a bug in the method set_rate()
# - added value checks for the set_xxx methods()
# - changed method names according to PEP8
# - apply PyLint and fixed bugs & warnings reported by it
#

import time
import struct
from machine import idle


class QMC5883:
    # Default I2C address
    ADDR = 0x0D

    # QMC5883 Register numbers
    X_LSB = 0
    X_MSB = 1
    Y_LSB = 2
    Y_MSB = 3
    Z_LSB = 4
    Z_MSB = 5
    STATUS = 6
    T_LSB = 7
    T_MSB = 8
    CONFIG = 9
    CONFIG2 = 10
    RESET = 11
    STATUS2 = 12
    CHIP_ID = 13

    # Bit values for the STATUS register
    STATUS_DRDY = 1
    STATUS_OVL = 2
    STATUS_DOR = 4

    # Oversampling values for the CONFIG register
    CONFIG_OS512 = 0b00000000
    CONFIG_OS256 = 0b01000000
    CONFIG_OS128 = 0b10000000
    CONFIG_OS64 = 0b11000000

    # Range values for the CONFIG register
    CONFIG_2GAUSS = 0b00000000
    CONFIG_8GAUSS = 0b00010000

    # Rate values for the CONFIG register
    CONFIG_10HZ = 0b00000000
    CONFIG_50HZ = 0b00000100
    CONFIG_100HZ = 0b00001000
    CONFIG_200HZ = 0b00001100

    # Mode values for the CONFIG register
    CONFIG_STANDBY = 0b00000000
    CONFIG_CONT = 0b00000001

    # Mode values for the CONFIG2 register
    CONFIG2_INT_DISABLE = 0b00000001
    CONFIG2_ROL_PTR = 0b01000000
    CONFIG2_SOFT_RST = 0b10000000

    def __init__(self, i2c, offset=50.0):
        self.i2c = i2c
        self.temp_offset = offset
        self.oversampling = QMC5883.CONFIG_OS64
        self.range = QMC5883.CONFIG_2GAUSS
        self.rate = QMC5883.CONFIG_100HZ
        self.mode = QMC5883.CONFIG_CONT
        self.register = bytearray(9)
        self.reset()

    def reset(self):
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.RESET, 0x01)
        time.sleep(0.1)
        self.reconfig()

    def reconfig(self):
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.CONFIG,
                             self.oversampling | self.range | self.rate | self.mode)
        time.sleep(0.01)
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.CONFIG2, QMC5883.CONFIG2_INT_DISABLE)
        time.sleep(0.01)

    def set_oversampling(self, sampling):
        if (sampling << 6) in (QMC5883.CONFIG_OS512, QMC5883.CONFIG_OS256,
                               QMC5883.CONFIG_OS128, QMC5883.CONFIG_OS64):
            self.oversampling = sampling << 6
            self.reconfig()
        else:
            raise ValueError("Invalid parameter")

    def set_range(self, rng):
        if (rng << 4) in (QMC5883.CONFIG_2GAUSS, QMC5883.CONFIG_8GAUSS):
            self.range = rng << 4
            self.reconfig()
        else:
            raise ValueError("Invalid parameter")

    def set_sampling_rate(self, rate):
        if (rate << 2) in (QMC5883.CONFIG_10HZ, QMC5883.CONFIG_50HZ,
                           QMC5883.CONFIG_100HZ, QMC5883.CONFIG_200HZ):
            self.rate = rate << 2
            self.reconfig()
        else:
            raise ValueError("Invalid parameter")

    def ready(self):
        status = self.i2c.readfrom_mem(QMC5883.ADDR, QMC5883.STATUS, 1)[0]
        # prevent hanging up here.
        # Happens when reading less bytes then then all 3 axis and will
        # end up in a loop. So, return any data but avoid the loop.
        if status == QMC5883.STATUS_DOR:
            print("Incomplete read")
            return QMC5883.STATUS_DRDY

        return status & QMC5883.STATUS_DRDY

    def read_raw(self):
        try:
            while not self.ready():
                idle()
            self.i2c.readfrom_mem_into(QMC5883.ADDR, QMC5883.X_LSB, self.register)
        except OSError as error:
            print("OSError", error)
            pass  # just silently re-use the old values
        # Convert the axis values to signed Short before returning
        x, y, z, _, temp = struct.unpack('<hhhBh', self.register)

        return (x, y, z, temp)

    def read_scaled(self):
        x, y, z, temp = self.read_raw()
        scale = 12000 if self.range == QMC5883.CONFIG_2GAUSS else 3000

        return (x / scale, y / scale, z / scale,
                (temp / 100 + self.temp_offset))
