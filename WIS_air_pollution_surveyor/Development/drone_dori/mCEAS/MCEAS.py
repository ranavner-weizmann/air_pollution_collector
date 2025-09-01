import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from seabreeze.spectrometers import Spectrometer as Spec
from datetime import datetime
import csv
import logging
import epics
import os
# os.chdir('/home/pi/Documents/github/drone_dori/mCEAS')
import sys
sys.path.insert(0, '../mCEAS/')
from calculation_functions import *

# TODO: split to logger/PV handler and claculation handler (insert to the functions' class?)

class MCEAS():
    
    def __init__(self,arduino_port,update_rate,is_demo_mode,default_log_dir,
                 measured_gases_and_sigma_filenames,atmospheric_gases_and_sigma_filenames,d_full,d_purging,
                 R_filename,R_wavelengths_filename,I0,T0,P0,I0_NO2,name_PV,spectrometer_name_PV,
                 measurement_gases,arduino_params,to_log,log_filename):
        # after init - start with self.calculate_reflectivity(tests,rayleighs,...) or self.load_reflectivity(filename)
        self.arduino_port = arduino_port
        self.update_rate = update_rate
        self.is_demo_mode = is_demo_mode
        self.default_log_dir = default_log_dir
        self.measured_gases_and_sigma_filenames = measured_gases_and_sigma_filenames
        self.atmospheric_gases_and_sigma_filenames = atmospheric_gases_and_sigma_filenames
        self.measured_gases_and_sigma = {}
        self.atmospheric_gases_and_sigma = {}
        self.d_full = d_full
        self.d_purging = d_purging
        self.R_filename = R_filename
        self.R_wavelengths_filename = R_wavelengths_filename
        self.T0,self.P0 = T0,P0
        self.I0_filename = I0
        self.I0_NO2 = I0_NO2
        self.current_arduino_data = {}
        self.init_wavelengths_and_I0()
        self.init_sigmas()
        self.name_PV = name_PV
        self.spectrometer_name_PV = spectrometer_name_PV
        self.arduino_params = arduino_params
        self.measurement_gases = measurement_gases
        self.data = self.null_dataframe()
        self.to_log = to_log
        self.log_filename = log_filename
        self.init_PV()
        self.init_log_file()

    def init_sigmas(self):
        for gas,sigma_filename in self.measured_gases_and_sigma_filenames.items():
            wavelengths_original,sigma_original = load_sigma_from_csv(sigma_filename,w_start=250,w_end=800,eps=None)
            self.measured_gases_and_sigma[gas] = sample_y_at_x(sigma_original,wavelengths_original,self.wavelengths)
        for gas,sigma_filename in self.atmospheric_gases_and_sigma_filenames.items():
            wavelengths_original,sigma_original = load_sigma_from_csv(sigma_filename,w_start=250,w_end=800,eps=None)
            self.atmospheric_gases_and_sigma[gas] = sample_y_at_x(sigma_original,wavelengths_original,self.wavelengths)

    def null_dataframe(self):
        columns = self.measurement_gases + self.arduino_params
        null_array = np.array([[np.NaN]*len(columns)])
        return pd.DataFrame(data=null_array,columns=columns,index=[pd.to_datetime(datetime.now())])
    
    def init_PV(self):
        self.PV = epics.Device(f"{self.name_PV}:")
        self.PV.enable = 1
        self.spectrometer_PV = epics.Device(f"{self.spectrometer_name_PV}:")

    def init_wavelengths_and_I0(self):
        # TODO: create an easy way to measure I0 without the csv file (using I_PV) - check type of file before loading
        self.wavelengths,self.I0 = load_wavelengths_and_average_I_from_spectrometer_csv(self.I0_filename) # assuming I0 measured in the lab
        # self.zero_I0_from_knwon_NO2()
    
    def read_from_arduino(self):
        if self.is_demo_mode: 
            arduino_dict = {"P":1013.25,"flow":150,"LED_intensity":150,"LED_T":-111,"peltier_T":-111,"P_volts":0,"pump":150}
        else:
            # arduino_dict = self.translate_arduino_string_to_dict() # TODO
            arduino_dict = {"P":1013.25,"flow":150,"LED_intensity":150,"LED_T":-111,"peltier_T":-111,"P_volts":0,"pump":150}
        self.update_params_from_arduino(arduino_dict)

    def translate_arduino_string_to_dict(self):
        # read from USB port, translate string to dict
        return

    def update_params_from_arduino(self,arduino_dict):
        self.current_arduino_data = {param:arduino_dict[param] for param in arduino_dict.keys()}
        try:
            self.P = arduino_dict["P"]
            self.LED_intensity = arduino_dict["LED_intensity"]
        except Exception as e:
            logging.info(f"Failed to read some data from arduino ({e})...")
            self.P,self.LED_intensity = 1013.25,150 # LED_intensity - for later input corrections (150 will be changed to last value)

    def read_T_RH(self):
        if self.is_demo_mode: 
            self.T,self.RH = 296.15,50.2
        self.T,self.RH = 296.15,50.2 # debug - ni iMet yet
        return # read T,RH from iMet PV 

    def read_intensities(self):
        if self.is_demo_mode: 
            levels = [316.14933884,313.50834711,310.52545455,306.48900826,299.64256198,297.34338843]
            self.I = np.ones(self.wavelengths.shape[0])*np.random.choice(levels)
            return
        self.I = self.spectrometer_PV.intensities

    def calculate_reflectivity(self,I1_filenames,I2_filenames,Ps1,Ps2,Ts1,Ts2,names1,names2):
        num_tests = len(I1_filenames) # assuming same length of all lists
        Rs = []
        for n in range(num_tests):
            w,I1=load_wavelengths_and_average_I_from_spectrometer_csv(filename=I1_filenames[n])
            _,I2=load_wavelengths_and_average_I_from_spectrometer_csv(filename=I2_filenames[n])
            N_air1,N_air2 = calculate_N_air(Ps1[n],Ts1[n]),calculate_N_air(Ps2[n],Ts2[n])
            # Assuming only Rayleigh scattering for both gases (both pure). Assuming no purging for reflectivity measurements
            alpha1 = N_air1*calculate_Rayleigh(names1[n],self.wavelengths)
            alpha2 = N_air2*calculate_Rayleigh(names2[n],self.wavelengths)
            I_ratio = I1/I2
            Rs.append(1.-self.d_full*(I_ratio*alpha1-alpha2)/(1.-I_ratio))
        Rs = np.array(Rs)
        return w,Rs,Rs.mean(0)

    def load_reflectivity(self):
        self.R = np.load(self.R_filename)

    def init_and_save_reflectivity(self,I1_filenames,I2_filenames,P1s,P2s,T1s,T2s,names1,names2):
        w,_,Rs_average = self.calculate_reflectivity(I1_filenames,I2_filenames,P1s,P2s,T1s,T2s,names1,names2)
        self.R = Rs_average
        np.save(self.R_filename,self.R)
        np.save(self.R_wavelengths_filename,w)
  
    def calculate_N_gases(self):
        return # implement statistic discrimination

    def calculate_N_NO2(self,alpha_NO2,w):
        sigma_NO2 = sum([no2_sigma for no2_name,no2_sigma in self.measured_gases_and_sigma.items() if "NO2" in no2_name ])
        N_NO2 = alpha_NO2/sigma_NO2
        return sample_y_at_x(N_NO2/calculate_N_air(self.P,self.T),self.wavelengths,w) # in num_molec/num_molec_in_air

    def calculate_alpha_measurements_no_purging(self):
        alpha_Rayleigh_air_0 = calculate_alpha_Rayleigh_air(self.wavelengths,self.P0,self.T0)
        alpha_Rayleigh_air_measurement = calculate_alpha_Rayleigh_air(self.wavelengths,self.P,self.T)
        a0,a1 = (1.-self.R)/self.d_full+alpha_Rayleigh_air_0,(1.-self.R)/self.d_full+alpha_Rayleigh_air_measurement
        alphas_sample = (self.I0/self.I-a1/a0)*a0
        return alphas_sample # Sum of all absorbing alphas in the sample

    def remove_atmospheric_alphas_from_measurement(self,alphas_full):
        return # remove known concentrations such as RH

    def measure(self):
        try:
            self.read_T_RH()
            self.read_from_arduino()
            self.read_intensities()
            alpha_NO2 = self.calculate_alpha_measurements_no_purging() # assuming only NO2 abosrbtions
            N_NO2 = self.calculate_N_NO2(alpha_NO2,[455])*1e9 # TODO: 455 as a class member per gas (662 for NO3 e.g.) (in ppb)
            self.data = pd.concat([self.data,self.null_dataframe()]) # To be filled with values
            for arduino_param,arduino_value in self.current_arduino_data.items():
                self.data.iloc[-1][arduino_param] = arduino_value
            self.data.iloc[-1]["NO2"] = N_NO2
        except Exception as e:
            logging.info(f"Failed to get measurement: {e}. Ignoring...")
            return      
        # self.calculate_N_gases()
        if (self.data.index[-1]-self.data.index[0]).total_seconds() >= 1./self.update_rate: 
            self.data = pd.DataFrame([self.data.mean(skipna=True)],index=[pd.to_datetime(datetime.now())]) 
            self.update_PV()
            self.log_data(self.data)
            self.data = self.null_dataframe()

    def update_PV(self):
        # return # implement dynamically?
        self.PV.NO2 = self.data["NO2"][0]
        # self.PV.LED_intensity = self.LED_intensity
        # self.PV.LED_T = self.LED_T
        # self.PV.peltier_T = self.peltier_T
        # self.PV.P = self.P
        # self.PV.P_volts = self.P_volts
        # self.PV.flow = self.flow
        # self.PV.pump = self.pump

    def zero_I0_from_knwon_NO2(self):
        # return self.I0*(1+self.calculate_alpha())/((1-self.reflectivity)/self.d_purging+self.calculate_alpha_Rayleigh(P,T))
        return 

    def init_log_file(self):
        if not self.to_log: return
        # TODO: if file exists = change filename (+now() to str)
        file_extension = f"_{datetime.now().strftime('%Y%m%d_%H%M.pkl')}" # if self.add_time_to_filename else ".pkl"
        self.log_filename = f"{self.default_log_dir}/{self.log_filename}{file_extension}"
        dataframe = self.null_dataframe()
        dataframe.to_pickle(self.log_filename)

    def log_data(self,dataframe_new):
        if not self.to_log: return
        dataframe_full= pd.read_pickle(self.log_filename)
        dataframe_full=pd.concat([dataframe_full,dataframe_new]).dropna()
        dataframe_full.to_pickle(self.log_filename)


