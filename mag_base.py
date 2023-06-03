# Compass base class

class mag_base:
    def __init__(self, i2c):
        self.i2c = i2c

    def read_scaled(self):
        return (0.0, 0.0, 0.0, 0.0)

    def read_raw(self):
        return (0, 0, 0)

    def set_sampling_rate(self, rate):
        pass

    def set_range(self, val):
        pass

    def set_oversampling(self, val):
        pass

    def reset(self):
        pass
