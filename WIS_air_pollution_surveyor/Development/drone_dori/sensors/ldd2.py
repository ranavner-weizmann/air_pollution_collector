from ldd import Ldd

class Ldd2(Ldd):
    def init_sensor(self):
        MODEL_NUMBER = 2
        return super().init_sensor(MODEL_NUMBER)