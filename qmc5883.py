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
# Michał Banaś changes:
# - added calibration (set callibartion)
# - added examples and calibration program
# - added smooth option to obtain more accurate data 
# - added heading function to obtain heading easily 
# - modified read function to support setting parameters 
# Changes insired/ported from https://github.com/mprograms/QMC5883LCompass/blob/master/src/QMC5883LCompass.cpp


import time
import struct
import math


class QMC5883:
    # probe the existence of const()
    try:
        _canary = const(0xfeed)
    except:
        const = lambda x: x

    # Default I2C address
    ADDR = const(0x0D)

    # QMC5883 Register numbers
    X_LSB = const(0)
    X_MSB = const(1)
    Y_LSB = const(2)
    Y_MSB = const(3)
    Z_LSB = const(4)
    Z_MSB = const(5)
    STATUS = const(6)
    T_LSB = const(7)
    T_MSB = const(8)
    CONFIG = const(9)
    CONFIG2 = const(10)
    RESET = const(11)
    STATUS2 = const(12)
    CHIP_ID = const(13)

    # Bit values for the STATUS register
    STATUS_DRDY = const(1)
    STATUS_OVL = const(2)
    STATUS_DOR = const(4)

    # Oversampling values for the CONFIG register
    CONFIG_OS512 = const(0b00000000)
    CONFIG_OS256 = const(0b01000000)
    CONFIG_OS128 = const(0b10000000)
    CONFIG_OS64 = const(0b11000000)

    # Range values for the CONFIG register
    CONFIG_2GAUSS = const(0b00000000)
    CONFIG_8GAUSS = const(0b00010000)

    # Rate values for the CONFIG register
    CONFIG_10HZ = const(0b00000000)
    CONFIG_50HZ = const(0b00000100)
    CONFIG_100HZ = const(0b00001000)
    CONFIG_200HZ = const(0b00001100)

    # Mode values for the CONFIG register
    CONFIG_STANDBY = const(0b00000000)
    CONFIG_CONT = const(0b00000001)

    # Mode values for the CONFIG2 register
    CONFIG2_INT_DISABLE = const(0b00000001)
    CONFIG2_ROL_PTR = const(0b01000000)
    CONFIG2_SOFT_RST = const(0b10000000)
    _vCalibration = []
    
    
    

    def __init__(self, i2c, offset=50.0, declination=(5, 37)):
        self.i2c = i2c
        self.temp_offset = offset
        self.oversampling = QMC5883.CONFIG_OS64
        self.range = QMC5883.CONFIG_8GAUSS
        self.rate = QMC5883.CONFIG_100HZ
        self.mode = QMC5883.CONFIG_CONT
        self.register = bytearray(9)
        self.command = bytearray(1)
        self.reset()
        self.declination = (declination[0] + declination[1] / 60) * math.pi / 180
        for c in range(0,3):
            self._vCalibration.append([0,0])

    def reset(self):
        self.command[0] = 1
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.RESET, self.command)
        time.sleep(0.1)
        self.reconfig()

    def reconfig(self):
        self.command[0] = (self.oversampling | self.range |
                           self.rate | self.mode)
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.CONFIG,
                             self.command)
        time.sleep(0.01)
        self.command[0] = QMC5883.CONFIG2_INT_DISABLE
        self.i2c.writeto_mem(QMC5883.ADDR, QMC5883.CONFIG2,
                             self.command)
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


    def set_calibration(self , x_min, x_max, y_min, y_max, z_min, z_max):
        """ Take a look at magnetometer_calibration.py to obtain valid data. basically takes max and min for each axis. 'Only' usefull if you are going to read callibrated data """
        self.calibrationUse = True;

        self._vCalibration[0][0] = x_min;
        self._vCalibration[0][1] = x_max;
        self._vCalibration[1][0] = y_min;
        self._vCalibration[1][1] = y_max;
        self._vCalibration[2][0] = z_min;
        self._vCalibration[2][1] = z_max;
    
    def _apply_callibration (self , x, y, z , t = 0):
        
        _vCalibration = self._vCalibration
        x_offset = (_vCalibration[0][0] + _vCalibration[0][1])/2;
        y_offset = (_vCalibration[1][0] + _vCalibration[1][1])/2;
        z_offset = (_vCalibration[2][0] + _vCalibration[2][1])/2;
        x_avg_delta = (_vCalibration[0][1] - _vCalibration[0][0])/2;
        y_avg_delta = (_vCalibration[1][1] - _vCalibration[1][0])/2;
        z_avg_delta = (_vCalibration[2][1] - _vCalibration[2][0])/2;

        avg_delta = (x_avg_delta + y_avg_delta + z_avg_delta) / 3;

        x_scale = avg_delta / x_avg_delta;
        y_scale = avg_delta / y_avg_delta;
        z_scale = avg_delta / z_avg_delta;


        return (x - x_offset) * x_scale , (y - y_offset) * y_scale , (z - z_offset) * z_scale;

    
    def read_raw(self):
        """ reads raw data"""
        try:
            while not self.ready():
                time.sleep(0.001)
            self.i2c.readfrom_mem_into(QMC5883.ADDR, QMC5883.X_LSB,
                                       self.register)
        except OSError as error:
            print("OSError", error)
            pass  # just silently re-use the old values
        # Convert the axis values to signed Short before returning
        x, y, z, _, temp = struct.unpack('<hhhBh', self.register)
    
        return (x, y, z, temp)
    
    def _read_smoothed(self , steps  ):
        """ Reads raw data {step} times , removes min and max values and retrurns x , y , z , temp . Makes reading longer, but more accurate """
        x_arr = []
        y_arr = []
        z_arr = []
        temp_arr = []
        for x in range(0, steps):
            x, y, z, temp = self.read_raw()
            x_arr.append(x)
            y_arr.append(y)
            z_arr.append(z)
            temp_arr.append(temp)
        
        data  =[]
        for a in [x_arr , y_arr , z_arr , temp_arr]:
            min_v = min(a)
            max_v = max(a)
            a.remove(min_v)
            a.remove(max_v)
            data.append(sum(a)/len(a))
        return (data[0] , data[1] , data[2] , data[3])
        
    
    def read(self, scalled = False , callibrated = False , smooothed = False , smooth_steps = 10 ):
        x, y, z, temp = (0 , 0,0 ,0 )
        if smooothed :
            x, y, z, temp = self._read_smoothed(smooth_steps)
        else:
            x, y, z, temp = self.read_raw()
    
        if callibrated:
            x, y , z = self._apply_callibration(x, y, z)
        if scalled:
            x, y, z, temp  = self._apply_scale(x, y, z, temp)
        
        return (x, y, z, temp)
        
        
        

    def _apply_scale(self , x, y, z, temp):
        scale = 12000 if self.range == QMC5883.CONFIG_2GAUSS else 3000

        return (x / scale, y / scale, z / scale,
                (temp / 100 + self.temp_offset))
    
    def heading(self, x, y):
        heading_rad = math.atan2(y, x)
        heading_rad += self.declination

        # Correct reverse heading.
        if heading_rad < 0:
            heading_rad += 2 * math.pi

        # Compensate for wrapping.
        elif heading_rad > 2 * math.pi:
            heading_rad -= 2 * math.pi

        # Convert from radians to degrees.
        heading = heading_rad * 180 / math.pi
        degrees = math.floor(heading)
        minutes = round((heading - degrees) * 60)
        return degrees, minutes
