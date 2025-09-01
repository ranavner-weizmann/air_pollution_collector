import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from seabreeze.spectrometers import Spectrometer as Spec
from datetime import datetime
import logging
import epics


class Spectrometer():
    
    def __init__(self,integration_time,demo_mode,spectrometer_ID,update_rate,
                 is_PV,name_PV,log_dir,to_log,filename="spectrometer",add_time_to_filename=True):
        """
        update rate is the same for both PV updates and data logging
        """
        logging.basicConfig(format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)
        self.integration_time = integration_time
        self.demo_mode = demo_mode
        spectrometer_ID = spectrometer_ID
        self.update_rate = update_rate
        self.is_PV = is_PV
        self.name_PV = name_PV
        self.log_dir = log_dir
        self.to_log = to_log
        self.filename = filename
        self.spec = None if self.demo_mode else Spec.from_serial_number(spectrometer_ID)
        self.wavelengths = self.demo_wavelengths() if self.demo_mode else self.spec.wavelengths()
        self.data = []
        self.add_time_to_filename = add_time_to_filename
        self.timestamps = []
        if self.is_PV: self.init_PV()
        self.init_file()
        
    def init_PV(self):
        self.PV = epics.Device(f"{self.name_PV}:")
        self.PV.wavelengths = self.wavelengths
        self.PV.enable = 1

    def init_file(self):
        if not self.to_log: return
        # TODO: if file exists = change filename (+now() to str)
        file_extension = f"_{datetime.now().strftime('%Y%m%d_%H%M.pkl')}" if self.add_time_to_filename else ".pkl"
        self.filename += file_extension
        null_array = np.expand_dims(np.full_like(self.wavelengths, np.NaN),0)
        dataframe = pd.DataFrame(data=null_array,columns=self.wavelengths,index=[pd.to_datetime(datetime.now())]) 
        dataframe.to_pickle(f"{self.log_dir}/{self.filename}")

    def get_measurement(self):
        if self.demo_mode:
            return self.generate_random_intensities()
        return self.spec.intensities()

    def generate_random_intensities(self):
        return np.random.rand(self.wavelengths.shape[0])*8000

    def demo_wavelengths(self):
        return np.arange(200,801)*1.

    def generate_debug_intensities(self):
        # Measurements from NO2 calibration: around [0,10,30,50,80,100]
        levels = [316.14933884,313.50834711,310.52545455,306.48900826,299.64256198,297.34338843]
        return np.ones(self.wavelengths.shape[0])*np.random.choice(levels)

    def measure(self):
        try:
            self.timestamps.append(pd.to_datetime(datetime.now()))
            self.data.append(self.get_measurement())
        except Exception as e:
            logging.info(f"Failed to get measurement: {e}. Ignoring...")
            return            
        if len(self.timestamps) == 0: return
        if (self.timestamps[-1]-self.timestamps[0]).total_seconds() >= 1./self.update_rate: 
            data,timestamp = np.array(self.data).mean(0),pd.to_datetime(datetime.now())
            data_df = pd.DataFrame(data=np.expand_dims(data,0),columns=self.wavelengths,index=[timestamp])
            if self.is_PV: self.update_PV(data)
            self.log_data(data_df)
            self.timestamps,self.data = [],[]
    
    def update_PV(self,data):
        if not self.is_PV: return
        self.PV.intensities = data # data is np.array

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



