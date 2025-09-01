"""
Wind sensor class
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023

"""
# from ctypes import windll
from multiprocessing.sharedctypes import Value
import serial
import datetime
from sensor import Sensor

# NAMING VARIABLES
wait = 100e-06
    
class Wind(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "0403", "ID_MODEL": "6001", "ID_SERIAL": "FTDI_FT232R_USB_UART_AQ016RT1"}
    PV_NAMES = ["speed", "direction", "temperature"]

    def init_sensor(self):

        self.serial_opts = {
            "port": self.port,
            "baudrate": 9600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 5
        }
        return super().init_sensor()
        

    # def init_wind(self):
    #     self.init_sensor()

   
    def measure_once(self):
        byte_len = 35

        data_dict = None
        strings_array = []

        try:
            new_line = self.serial.readline()
            if len(new_line)<byte_len:
                pass
            else:
                decode_line = new_line.decode('utf-8')[8:-9]
                decode_line2 = decode_line.replace('+','')
                decode_line3 = decode_line2.replace(' ','')
                splitted_list = decode_line3.split(',')     

                temp_list = []
                for char in splitted_list:
                
                    temp_list.append(float(char))
                    strings_array.append(temp_list)
                data_dict = dict()
                data_dict['speed']=temp_list[0] 
                data_dict['direction']=temp_list[1]
                data_dict['temperature']=temp_list[3]
                return data_dict
        
        except ValueError:
            self.logger.info("the output bytes are not in the correct form, let's try again")
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        return None  
                       
                       