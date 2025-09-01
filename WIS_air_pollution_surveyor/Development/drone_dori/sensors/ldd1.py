from ldd import Ldd

class Ldd1(Ldd):
    def init_sensor(self):
        MODEL_NUMBER = 1
        return super().init_sensor(MODEL_NUMBER)