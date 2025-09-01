"""
GPS Sensor class
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023
Version 0.0.1

"""


import logging
import json
from sensor import Sensor
import serial
import time
    
class GPS(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "1546", "ID_MODEL": "01A9", "ID_SERIAL": "u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver"}
    PV_NAMES = ['latitude', 'longitude', 'altitude']

    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "port": self.port,
            "baudrate": 38400,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
            "timeout": 1     
        }
        return super().init_sensor()

    
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        for _ in range(10):
            try:
                line = self.serial.readline().decode()
                message = line
                data_received = message.split(',')
                if (len(data_received) != 15):
                    continue
                measures = {}
                measures["latitude"] = float(data_received[2])
                measures["longitude"] = float(data_received[4])
                measures["altitude"] = float(data_received[9])
                return measures
            except (IndexError, ValueError) as err:
                continue
        return None



