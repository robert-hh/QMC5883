# QMC5883: Python class for the QMC5883 Three-Axis Digital Compass IC

This is a very short and simple class. It uses the I2C bus for the interface.

Initial code by Sebastian Folz, M.Sc. at
http://nobytes.blogspot.com/2018/03/qmc5883-magnetic-field-sensor.html

## Constructor

### QMC5883 = QMC5883(i2c [, temp_offset])

- i2c is an I2C object which has to be created by the caller.
- temp_offset specifies the offset to the temperature, as returned by the method
read_scaled. The unit is °C, the default is 50 °C.

## Methods

### (x, y, z, t) = QMC5883.read_raw()
Return the raw reading for the x,y, and z axis as well as the raw temperature
reading. The values are not scaled according to the sensitivity or possible offsets.

### (x, y, z, t) = QMC5883.read_scaled()
Return the scaled reading for the x,y, and z axis as well as the temperature
reading. The x ,y and z readings are scaled to Gauss, the temperature to °C with compensated offset

### QMC5883.set_sampling rate(sampling_rate)
Sets the sampling rate of the sensor. Accepted values are:

|Value|Sampling rate|
|:-:|:-:|
|0|10 Hz|
|1|50 Hz|
|2|100 Hz|
|3|200 Hz|

### QMC5883.set_oversampling(oversampling)
Sets the oversampling factor of the sensor. Accepted values are:

|Value|Oversampling|
|:-:|:-:|
|0|512|
|1|256|
|2|128|
|3|64|

### QMC5883.set_range(range)
Sets the magnetic field range of the sensor. Accepted values are:

|Value|Range|
|:-:|:-:|
|0|2 Gauss|
|1|8 Gauss|

### QMC5883.reset()

Resets the device using the previously configured settings. This call is **not**
required when settings are changed.

```
# Example for Pycom device.
# Connections:
# xxPy | QMC5883
# -----|-------
# P9   |  SDA
# P10  |  SCL
#
from machine import I2C
from QMC5883 import QMC5883

i2c = I2C(0, I2C.MASTER)
qmc5883 = QMC5883(i2c)

x, y, z, temp = qmc5883.read_scaled()
```
