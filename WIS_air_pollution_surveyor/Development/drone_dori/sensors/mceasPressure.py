"""
mCEAS Pressure sensor class
Programmer: Eviatar Shemesh
Date 22/08/2023

"""

import logging
import json
from sensor import Sensor
import serial
import time



    
class mceasPressure(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "2341", "ID_MODEL": "0058", "ID_SERIAL": "Arduino_LLC_Arduino_Nano_Every_301B53D4514E4650414B2020FF0E3952"}
    PV_NAMES = ["p", "fp", "humidity", "temperature"]

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
            data = self.serial.readline().decode().strip()
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        
        try:
            d = {}
            if not data:
                return None
            data = data.split(",")
            d["p"] = float(data[0])
            d["fp"] = float(data[1])
            d["humidity"] = float(data[2])
            d["temperature"] = float(data[3])

            return d
        except:
            return None