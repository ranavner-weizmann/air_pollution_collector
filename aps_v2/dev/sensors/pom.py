"""
POM sensor class
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023

"""

import serial
import time
import sys
from sensors.sensor import Sensor
from datetime import datetime
import numpy as np


# NAMING VARIABLES
wait = 100e-06
time_delay = 6    
    
class Pom(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "04d8", "ID_MODEL": "000a", "ID_SERIAL": "Microchip_Technology_Inc._CDC_RS-232_Emulation_Demo"}
    PV_NAMES = ['ozone','cell_temp','cell_pressure','photo_volt','power_supply', 'latitude','longitude','altitude']
                           

    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "port": self.port,
            "baudrate": 19200,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 20
        }
        return super().init_sensor()
    
    def demo_data(self) -> dict:
        """
        Returns a demo data dictionary

        Returns
        -------
        dict - holding demo data
        """
        data_dict = {'ozone': np.random.random(), 'cell_temp': np.random.random(), 'cell_pressure': np.random.random(), 'photo_volt': np.random.random(),
        'power_supply': np.random.random(), 'latitude': np.random.random(), 'longitude': np.random.random(), 'altitude': np.random.random(), 'gps_quality': np.random.random(), 
        }
                                                
        return data_dict 

    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        parameter_list = self.PV_NAMES
        data_dict = {}
        try:
            new_line = self.serial.readline()
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None

        if len(new_line)==0:
            #time.sleep(0.1)
            return None
        decode_line = new_line.decode('utf-8').replace('\r\n','')
        if '\x00' in decode_line:                                              # in case that there is a null character.   
            decode_line = decode_line.replace('\x00','')
        decode_list = decode_line.split(',')
        decode_data = []
        for i in decode_list:
            try:
                decode_data.append(float(i))
            except:
                break

        try:
            for i in range(len(Pom.PV_NAMES)):
                data_dict[Pom.PV_NAMES[i]] = decode_data[i]
        except:
            return None
        
        return data_dict
                
            
        