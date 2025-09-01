"""
Spectrometer sensor class
Programmers: Nitzan Yizhar and Dori Nissenbaum
Date 06/07/2023

"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seabreeze
seabreeze.use('pyseabreeze')
from seabreeze.spectrometers import Spectrometer as Spec
from seabreeze.pyseabreeze import SeaBreezeError
from datetime import datetime
from sensor import Sensor
from enum import Enum
import sys
import signal
import os



class StSpectrometer(Sensor):

    WAVELENGTH_SIZE = 1516
    PV_NAMES = ["i"+str(i) for i in range(1516)]
    # INTEGRATION_TIME = 250000
    INTEGRATION_TIME = 125000
    SERIAL_ID = "ST01054"    
    first = True

    class States(Enum):
        REFLECTIVITY = -1
        ZERO = 0
        MEASURING = 1


    def init_sensor(self):
        if self.demo_mode:
            return Sensor.OK
        
        self.logger.info(f"Starting st-spectrometer with Serial_ID = {self.SERIAL_ID}")
        try:
            self.spec = Spec.from_serial_number(self.SERIAL_ID)
        except Exception as err:
            self.spec = None
            return Sensor.FAIL  
        self.state = self.States.REFLECTIVITY
        self.spec.integration_time_micros(self.INTEGRATION_TIME)
        self.logger.info(f"Integration time set to {self.INTEGRATION_TIME/1000000} seconds")
        self.wavelengths = self.spec.wavelengths() # TODO change PV names to theses
        # self.WAVELENGTH_SIZE = len(self.wavelengths)
        # self.PV_NAMES = self.wavelengths
        # super().init_sensor()
        signal.signal(signal.SIGTERM, self.signal_handler)

        return Sensor.OK

    def measure_once(self):
        # if self.state == Spectrometer.States.REFLECTIVITY:
        #     return {"intensities": self.spec.intensities(), "wavelengths": self.spec.wavelengths()}

        # if self.state == Spectrometer.States.ZERO:
        #     return {"intensities": self.spec.intensities(), "wavelengths": self.spec.wavelengths()}

        # if self.state == Spectrometer.States.MEASURING:
        if StSpectrometer.first:
            d = {}
            for i in range(StSpectrometer.WAVELENGTH_SIZE):
                d["i"+str(i)] = self.wavelengths[i]
            StSpectrometer.first = False
            return d
        try:
            wavelengths = self.PV_NAMES
            I = list(self.spec.intensities())
        except SeaBreezeError as err:
            self.end()
            self.init_sensor()
            return None
        except Exception as err:
            self.serial_failure()
            return None
        try:
            data = {}
            for i in range(StSpectrometer.WAVELENGTH_SIZE):
                data["i"+str(i)] = I[i]
            return data
        except:
            return None
    
    def demo_data(self):
        return {"intensities": self.generate_random_intensities().tolist(), "wavelengths": self.demo_wavelengths().tolist()}

    
    def generate_random_intensities(self):
        # return np.random.rand(self.wavelengths.shape[0])*8000
        return np.random.rand(StSpectrometer.WAVELENGTH_SIZE)*8000

    def demo_wavelengths(self):
        return np.arange(200,801)*1.

    def generate_debug_intensities(self):
        # Measurements from NO2 calibration: around [0,10,30,50,80,100]
        levels = [316.14933884,313.50834711,310.52545455,306.48900826,299.64256198,297.34338843]
        return np.ones(StSpectrometer.WAVELENGTH_SIZE)*np.random.choice(levels)


    def log_data(self,dataframe_new):
        if not self.to_log: return
        dataframe_full= pd.read_pickle(f"{self.log_dir}/{self.filename}")
        dataframe_full=pd.concat([dataframe_full,dataframe_new]).dropna()
        dataframe_full.to_pickle(f"{self.log_dir}/{self.filename}")
        # self.plot_sample_data()

    def plot_sample_data(self,idx=-1):
        dataframe= pd.read_pickle(f"{self.log_dir}/{self.filename}")
        plt.plot(dataframe.columns,dataframe.iloc[idx])
        plt.show()

    def end(self):
        if self.spec:
            self.spec.close()

    def signal_handler(self, signal_num, frame):
        self.end()
        os._exit(1)


        
    



