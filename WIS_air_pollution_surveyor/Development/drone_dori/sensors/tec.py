"""
Tec sensor class
Programmer: Nitzan Yizhar & Eviatar Shemesh
Date 22/08/2023

"""

import logging
import json
from sensor import Sensor
from meerstetterSensor import MeerstetterSensor
from serial import SerialException

    
class Tec(Sensor):

    IDENTIFIERS = {"ID_VENDOR": "0403", "ID_MODEL": "6015", "ID_SERIAL": "FTDI_FT230X_Basic_UART_DK0FPPD7"}
    PV_NAMES = ["ls", "temp", "target", "voltage_cur", "voltage_out", "sink_temp", "ramp_temp" ]
    
    COMMAND_TABLE = {
        "loop status": [1200, ""],
        "object temperature": [1000, "degC"],
        "target object temperature": [1010, "degC"],
        "output current": [1020, "A"],
        "output voltage": [1021, "V"],
        "sink temperature": [1001, "degC"],
        "ramp temperature": [1011, "degC"],
    }
    D = {"loop status": "ls",
        "object temperature": "temp",
        "target object temperature": "target",
        "output current": "voltage_cur",
        "output voltage": "voltage_out",
        "sink temperature": "sink_temp",
        "ramp temperature": "ramp_temp" }
    
            
    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "baudrate": 9600,
            "port": self.port,
            "timeout": 2
        }
        try:
            self.mc = MeerstetterSensor(Tec.IDENTIFIERS["ID_SERIAL"], command_table=self.COMMAND_TABLE)
            return super().init_sensor()
        except:
            return Sensor.FAIL

    
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        try:
            data = self.mc.get_data()
        except :
            return None
        try:
            d = {}
            if not data:
                return None
            for key in data.keys():
                d[Tec.D[key]] = data[key][0]
            return d
        except:
            return None
        
        
        
    
    