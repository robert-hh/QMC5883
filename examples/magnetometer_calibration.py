from qmc5883 import QMC5883
import machine , utime , sys





class Calibrator :
    calibrationData = []

    changed = False;
    done = False;
    t = 0;
    c = 0;
    mag = None
    i2c = None

    def setup(self):
      self.i2c  = machine.I2C( 0  , scl=machine.Pin(17), sda=machine.Pin(16), freq=1000 )
      self.mag = QMC5883(self.i2c)
      print("This will provide calibration settings for your QMC5883L chip. When prompted, move the magnetometer in all directions until the calibration is complete.");
      print("Calibration will begin in 5 seconds.");
      for c in range(0,3):
          self.calibrationData.append([sys.maxsize, sys.maxsize*-1])

      utime.sleep(2);
      
    
    def loop(self):
        x, y, z , _= self.mag.read_raw()
        changed = False
        data = [x , y , z]
        calibrationData = self.calibrationData
        
        for c in range(0,3):
            
            if data[c] < calibrationData[c][0]:
            
                calibrationData[c][0] = data[c];
                changed = True;
            if data[c] > calibrationData[0][1]:
            
                calibrationData[c][1] = data[c];
                changed = True;
            
        if changed :
            print("CALIBRATING... Keep moving your sensor around.")
            self.c = utime.time()
        
        self.t = utime.time()
        
        if self.t-self.c > 5 and not self.done:
            self.done = True
  
            self.done = True;
            print("DONE. Copy the line below and paste it into your projects sketch.);");
            print()
              
            print("compass.set_calibration(" , end='')
            print(calibrationData[0][0], end='')
            print(", ", end='')
            print(calibrationData[0][1], end='')
            print(", ", end='')
            print(calibrationData[1][0], end='')
            print(", ", end='')
            print(calibrationData[1][1], end='')
            print(", ", end='')
            print(calibrationData[2][0], end='')
            print(", ", end='')
            print(calibrationData[2][1], end='')
            print(");", end='')

  
 
c = Calibrator()
c.setup()
print("CALLIBRATING!!!!")
while not c.done :
    c.loop()
    
#compass.set_calibration(-1980, 1577, -3975, -713, -1650, 1576);