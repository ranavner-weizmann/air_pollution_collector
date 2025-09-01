# -*- coding: utf-8 -*-
"""
This is the sniffer4D driver file
Programmers: Nitzan Yizhar and Lior Segev
Date 12 Nov 2020
Version 0.0.1

"""

from __future__ import print_function
import serial
import json
from sensor import Sensor
from datetime import datetime
import numpy as np

wait = 100e-06
    
class Sniffer(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "067b", "ID_MODEL": "2303", "ID_SERIAL": "Prolific_Technology_Inc._USB-Serial_Controller"}
    PV_NAMES = ['comm_ON', 'enable', 'data_ready', 'CO', 'NO2', 'Ox', 'PM1', 'PM10', 'PM2dot5', 'SO2',
                'altitude', 'hdop', 'humidity', 'latitude', 'longitude', 'pressure', 'sateNum', 'sequence', 'serial', 'temperature', 'utcTime']
    

    def init_sniffer(self):
        '''
        establish communication with SNIFFER return OK if succedded and -1 if failed
        '''
        self.init_sensor()

    def init_sensor(self):
        '''
        establish communication with SNIFFER return OK if succedded and -1 if failed
        '''
        if self.demo_mode:
            return Sensor.OK
        
        self.serial_opts = {
            "port": self.port,
            "baudrate": 115200,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 5
        }
        return super().init_sensor()
   
    def demo_data(self):
        '''
        request data from sniffer. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        now = datetime.now()
        data_dict  = {key : np.random.random() for key in self.PV_NAMES}
        data_dict["utcTime"] = now.strftime("%m/%d/%Y-%H:%M:%S")
        return data_dict
    
    def measure_once(self):
        '''
        request data from sniffer. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        
        while True:
            array_strings =[]    
            while True:
                try:
                    data_string_line = self.serial.readline()
                except serial.SerialException as e:
                    self.logger.error(f"{self.name} serial expection: " + str(e))
                    self.serial_failure()
                    return None

                if data_string_line == b'\n':
                    break
                else:
                    try:
                        array_strings.append(data_string_line.decode('utf-8'))
                    except UnicodeDecodeError:
                        self.logger.error('decoding of string failed. will try again')
                        break

            sep = ''
            json_string = sep.join(array_strings)
            try:
                data_dict = json.loads(json_string)
                break
            except json.decoder.JSONDecodeError:
                self.logger.error('json read exception occured, retrying next data frame....')
                
        result_dict = {
            "CO": data_dict["airData"]["CO(ppm)"],
            "NO2": data_dict["airData"]["NO2(ppm)"],
            "Ox": data_dict["airData"]["Ox(ppm)"],
            "PM1": data_dict["airData"]["PM1.0(ug/m3)"],
            "PM10": data_dict["airData"]["PM10(ug/m3)"],
            "PM2dot5": data_dict["airData"]["PM2.5(ug/m3)"],
            "SO2": data_dict["airData"]["SO2(ppm)"],
            "altitude": data_dict["altitude"],
            "hdop": data_dict["hdop"],
            "humidity": data_dict["humidity"],
            "latitude": data_dict["latitude"],
            "longitude": data_dict["longitude"],
            "pressure": data_dict["pressure"],
            "sateNum": data_dict["sateNum"],
            "sequence": data_dict["sequence"],
            "serial": data_dict["serial"],
            "temperature": data_dict["temperature"],
            "utcTime": data_dict["utcTime"]
        }
        
        #missing fields
        #'', '', 's', '', ''
        result_dict["comm_ON"] = str(Sensor.Nan)
        result_dict["enable"] = str(Sensor.Nan)
        result_dict["data_ready"] = str(Sensor.Nan)
        
        return result_dict
                                        
