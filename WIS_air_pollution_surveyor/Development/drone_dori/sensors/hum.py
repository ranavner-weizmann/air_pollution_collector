"""
HUM Sensor class
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023

"""
import serial
from sensor import Sensor
from random import random
import time

class Hum(Sensor):
    labels_list = ['pressure','temp','rel_hum',
        'hum_temp','Date and time','unknown','longitude','latitude','altitude','sat','k']

    IDENTIFIERS = {"ID_VENDOR": "0403", "ID_MODEL": "6015", "ID_SERIAL": "FTDI_FT230X_Basic_UART_DN05BKPD"}

    PV_NAMES = ['pressure', 'temp', 'rel_hum', 'hum_temp', 'longitude', 'latitude', 'altitude', 'sat']
    

    def init_sensor(self):

        self.serial_opts = {
            "port": self.port,
            "baudrate": 57600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "timeout": 1
        }
        return super().init_sensor()

    def measure_once(self) -> dict:
        
        labels_list = Hum.labels_list
        data_dict = {}
        try:
            line = self.serial.readline()
       
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        
        decoded = line.decode('utf-8')
        decoded_list = decoded.split(',')
        decoded_list.pop(0)
        for i in range(len(decoded_list)):
            try:
                data_dict[labels_list[i]]=float(decoded_list[i])
            except (KeyError, ValueError, IndexError):
                pass
        if data_dict == {}:
            return None
        
        return data_dict
