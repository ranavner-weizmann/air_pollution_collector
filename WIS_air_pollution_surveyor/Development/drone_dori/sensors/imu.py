"""
IMU and RTC sensor class
Programmer: Nitzan Yizhar
Date 06/07/2023

"""
import logging
import json
from sensor import Sensor
import serial
import time
    
class IMU(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "0403", "ID_MODEL": "6001", "ID_SERIAL": "FTDI_FT232R_USB_UART_AR0KL18F"}
    PV_NAMES = ['acc_direction_x', 'acc_direction_y', 'acc_direction_z','gyro_rotation_x', 'gyro_rotation_y', 'gyro_rotation_z']

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
        measures = {item: 0 for item in self.PV_NAMES}
        try:
            data = self.serial.readline().decode().strip()
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        
        if data:
            splitted = data.split(",")
            for variable, value in zip(self.PV_NAMES, splitted):
                measures[variable] = float(value)
            return measures
            
        return None
        
        