"""
Spectrometer sensor class
Programmers: Nitzan Yizhar and Dori Nissenbaum
Date 06/07/2023

"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from seabreeze.spectrometers import Spectrometer as Spec
from datetime import datetime
from sensor import Sensor
from enum import Enum
import sys
import signal
import os
from seabreeze.cseabreeze._wrapper import SeaBreezeError



class Spectrometer(Sensor):

    PV_NAMES = ["i"+str(i) for i in range(1044)]
    PV_NAMES.append("tec_t_c")
    # INTEGRATION_TIME = 250000
    INTEGRATION_TIME = 125000
    SERIAL_ID = "QEP03372"
    WAVELENGTH_SIZE = 1044
    first = True

    class States(Enum):
        REFLECTIVITY = -1
        ZERO = 0
        MEASURING = 1


    def init_sensor(self):
        if self.demo_mode:
            return Sensor.OK
        
        self.logger.info(f"Starting spectrometer with Serial_ID = {self.SERIAL_ID}")
        try:
            self.spec = Spec.from_serial_number(self.SERIAL_ID)
            self.spec.open()
        except:
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
        # TODO - ressurection in case of request_data failure!
        # if self.state == Spectrometer.States.REFLECTIVITY:
        #     return {"intensities": self.spec.intensities(), "wavelengths": self.spec.wavelengths()}

        # if self.state == Spectrometer.States.ZERO:
        #     return {"intensities": self.spec.intensities(), "wavelengths": self.spec.wavelengths()}

        # if self.state == Spectrometer.States.MEASURING:
        if Spectrometer.first:
            d = {}
            for i in range(Spectrometer.WAVELENGTH_SIZE):
                d["i"+str(i)] = self.wavelengths[i]
            d["tec_t_c"] = self.spec.f.thermo_electric.read_temperature_degrees_celsius()
            Spectrometer.first = False
            return d
        try:
            wavelengths = self.PV_NAMES
            I = list(self.spec.intensities())
        except SeaBreezeError as err:
            self.end()
            self.init_sensor()
            return None
        # except self.serial.SerialException:
        except Exception as err:
            self.serial_failure()
            # return {w:-100.0 for w in Spectrometer.WAVELENGTH_SIZE}
            return None
        try:
            data = {}
            for i in range(Spectrometer.WAVELENGTH_SIZE):
                data["i"+str(i)] = I[i]
            data["tec_t_c"] = self.spec.f.thermo_electric.read_temperature_degrees_celsius()
            return data
        except:
            return None
    
    def demo_data(self):
        return {"intensities": self.generate_random_intensities().tolist(), "wavelengths": self.demo_wavelengths().tolist()}

    
    def generate_random_intensities(self):
        # return np.random.rand(self.wavelengths.shape[0])*8000
        return np.random.rand(Spectrometer.WAVELENGTH_SIZE)*8000

    def demo_wavelengths(self):
        return np.arange(200,801)*1.

    def generate_debug_intensities(self):
        # Measurements from NO2 calibration: around [0,10,30,50,80,100]
        levels = [316.14933884,313.50834711,310.52545455,306.48900826,299.64256198,297.34338843]
        return np.ones(Spectrometer.WAVELENGTH_SIZE)*np.random.choice(levels)


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


        
    



