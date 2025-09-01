"""
mCEAS arduino pump sensor class
Programmer: Eviatar Shemesh
Date 22/08/2023

"""

import logging
import json
from sensor import Sensor
import serial
import time



    
class mceasArduinoPump(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "2341", "ID_MODEL": "8036", "ID_SERIAL": "Arduino_LLC_Arduino_Leonardo"}
    PV_NAMES = ["FLM", "FTARGET", "CPSI", "CMB"]

    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "baudrate": 9600,
            "port": self.port,
            "timeout": 2
        }
        return super().init_sensor()

    
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        try:
            data = self.serial.readline().decode()
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        try:
            if not data:
                return None
            lst = data.split(",")
            d = {}
            for s in lst:
                key = s.split(":")[0]
                val = float(s.split(":")[1][1:].strip())
                d[key] = val
            return d
        except:
            return None 
        