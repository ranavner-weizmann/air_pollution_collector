# -*- coding: utf-8 -*-
"""
This is the microaeth-MA200 sensor script
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023
Version 0.0.1

"""

import logging
import serial
import re
import time
from sensor import Sensor

integration = 5

# NAMING VARIABLES
wait = 100e-06
OK = 0


class FailedCommunication(Exception):
    pass


class Aeth(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "0403", "ID_MODEL": "6001", "ID_SERIAL": "FTDI_TTL232RG-VSW3V3_FT2GFEGC"}

    PV_NAMES =['comm_ON', 'tape_at_end_ON', 'sampling_ON', 'enable', 'data_ready', 'datum_id', 'session_id', 'data_format_ver', 'firmware_version', 'date_time_GMT', 'timezone_offset', 'gps_lat', 'gps_long', 'gps_speed',
               'timebase', 'status', 'battery', 'accel_x', 'accel_y', 'accel_z', 'tape_pos', 'flow_setpoint', 'flow_total', 'flow1', 'flow2', 'sample_temp', 'sample_RH', 'sample_dewpoint', 'int_pressure',
               'int_temp', 'optical_config', 'UV_sen1', 'UV_sen2', 'UV_ref', 'UV_ATN1', 'UV_ATN2', 'UV_K', 'blue_sen1', 'blue_sen2', 'blue_ref', 'blue_ATN1', 'blue_ATN2', 'blue_K', 'green_sen1', 'green_sen2', 'green_ref', 'green_ATN1',
               'green_ATN2', 'green_K', 'red_sen1', 'red_sen2', 'red_ref', 'red_ATN1', 'red_ATN2', 'red_K', 'IR_sen1', 'IR_sen2', 'IR_ref', 'IR_ATN1', 'IR_ATN2', 'IR_K', 'UV_BC1', 'UV_BC2',
               'UV_BCc', 'blue_BC1', 'blue_BC2', 'blue_BCc', 'green_BC1', 'green_BC2', 'green_BCc', 'red_BC1', 'red_BC2', 'red_BCc', 'IR_BC1', 'IR_BC2', 'IR_BCc'] 
    def __init__(self, name :str, location: str, demo_mode : bool, is_device : bool, device_name : str, sampling_time: int = 1):
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10;
        super().__init__(name=name, location=location, device_name=device_name, is_device=is_device, demo_mode=demo_mode, sampling_time=sampling_time)
        

    def init_sensor(self) -> None:
        self.serial_opts = {
            "port": self.port,
            "baudrate": 1000000,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 1
        }

        init_status = super().init_sensor()
        if init_status == Sensor.FAIL:
            return init_status
        
        if self.demo_mode:
            return Sensor.OK
        
        self.logger.info('updating measurements IDs..')
        init_status = self.update_measurment_ids()
        return init_status

    # def init_aeth(self) -> None:
    #     '''
    #     establish communication with AETH return OK if succedded and -1 if failed
    #     '''
    #     return self.init_sensor()

    def measure_once(self) -> dict:
        time.sleep(1) # The aeth doesn't provide data quick enough and spamming log.
        self.serial.write(b'dr\r')

        data = self.serial.readline().decode('utf-8').split(',')[1:-1]
        if len(data) == 0 or data is None or (int(data[0]) == self.current_id):
            return None
        
        # if int(data[0]) == self.current_id:
        #     #raise NoNewDataRecieved
        #     return None # no new data present
        else:
            # update the new ID
            if self.update_measurment_ids() == Sensor.FAIL:
                return None
        
        dict_data = dict()
        dict_data["datum_id"] = data[0]
        dict_data["session_id"] = data[1]
        dict_data["data_format_ver"] = data[2]
        dict_data["firmware_version"] = data[3]
        dict_data["date_time_GMT"] = data[4]
        dict_data["timezone_offset"] = data[5]
        dict_data["gps_lat"] = data[6]
        dict_data["gps_long"] = data[7]
        dict_data["gps_speed"] = data[8]
        dict_data["timebase"] = data[9]
        dict_data["status"] = data[10]
        dict_data["battery"] = data[11]
        dict_data["accel_x"] = data[12]
        dict_data["accel_y"] = data[13]
        dict_data["accel_z"] = data[14]
        dict_data["tape_pos"] = data[15]
        dict_data["flow_setpoint"] = data[16]
        dict_data["flow_total"] = data[17]
        dict_data["flow1"] = data[18]
        dict_data["flow2"] = data[19]
        dict_data["sample_temp"] = data[20]
        dict_data["sample_RH"] = data[21]
        dict_data["sample_dewpoint"] = data[22]
        dict_data["int_pressure"] = data[23]
        dict_data["int_temp"] = data[24]
        dict_data["optical_config"] = data[25]
        dict_data["UV_sen1"] = data[26]
        dict_data["UV_sen2"] = data[27]
        dict_data["UV_ref"] = data[28]
        dict_data["UV_ATN1"] = data[29]
        dict_data["UV_ATN2"] = data[30]
        dict_data["UV_K"] = data[31]
        dict_data["blue_sen1"] = data[32]
        dict_data["blue_sen2"] = data[33]
        dict_data["blue_ref"] = data[34]
        dict_data["blue_ATN1"] = data[35]
        dict_data["blue_ATN2"] = data[36]
        dict_data["blue_K"] = data[37]
        dict_data["green_sen1"] = data[38]
        dict_data["green_sen2"] = data[39]
        dict_data["green_ref"] = data[40]
        dict_data["green_ATN1"] = data[41]
        dict_data["green_ATN2"] = data[42]
        dict_data["green_K"] = data[43]
        dict_data["red_sen1"] = data[44]
        dict_data["red_sen2"] = data[45]
        dict_data["red_ref"] = data[46]
        dict_data["red_ATN1"] = data[47]
        dict_data["red_ATN2"] = data[48]
        dict_data["red_K"] = data[49]
        dict_data["IR_sen1"] = data[50]
        dict_data["IR_sen2"] = data[51]
        dict_data["IR_ref"] = data[52]
        dict_data["IR_ATN1"] = data[53]
        dict_data["IR_ATN2"] = data[54]
        dict_data["IR_K"] = data[55]
        dict_data["UV_BC1"] = data[56]
        dict_data["UV_BC2"] = data[57]
        dict_data["UV_BCc"] = data[58]
        dict_data["blue_BC1"] = data[59]
        dict_data["blue_BC2"] = data[60]
        dict_data["blue_BCc"] = data[61]
        dict_data["green_BC1"] = data[62]
        dict_data["green_BC2"] = data[63]
        dict_data["green_BCc"] = data[64]
        dict_data["red_BC1"] = data[65]
        dict_data["red_BC2"] = data[66]
        dict_data["red_BCc"] = data[67]
        dict_data["IR_BC1"] = data[68]
        dict_data["IR_BC2"] = data[69]
        dict_data["IR_BCc"] = data[70]
        
        #missing fields
        #'', '', 's', '', ''
        dict_data["comm_ON"] = str(Sensor.Nan)
        dict_data["tape_at_end_ON"] = str(Sensor.Nan)
        dict_data["sampling_ON"] = str(Sensor.Nan)
        dict_data["enable"] = str(Sensor.Nan)
        dict_data["data_ready"] = str(Sensor.Nan)

        return {
            key : dict_data[key] if dict_data[key] != "" else str(Sensor.Nan) for key in dict_data.keys()
        }

    def is_sampling(self):
        '''
        return True if sampling is on going and False otherwise
        '''
        self.serial.write(b'cs\r')
        self.serial.readline()
        status_str = self.serial.readline()
        self.serial.readline()
        status_re = re.findall('[0-9]+', status_str.decode('utf-8'))
        return True if int(status_re[3])==1 else False
        
    def update_measurment_ids(self):
        '''
        update measurements ids by checking status of AETH
        command: cs
        udpates state variables  firstid = , nextId=, currentId= , sampling = 0 or 1 
        '''
        self.serial.write(b'cs\r')
        self.serial.readline()
        status_str = self.serial.readline()
        self.serial.readline()

        status_re = re.findall('[0-9]+', status_str.decode('utf-8'))
        if status_re == []:
            return Sensor.FAIL
            
        self.first_id = int(status_re[0])
        self.next_id = int(status_re[1])
        self.current_id = int(status_re[2])
        
        return Sensor.OK
        

    def check_battery(self):
        '''
        request battery status
        '''

        self.serial.write(b'cb\r')
        re_battery_search = re.search('\d+', self.serial.readline().decode('utf-8') )
        return int(re_battery_search.group(0))

    def start_measurement(self):
        '''
        start measurement - returns True if sampling started
        '''
        if not self.is_sampling():
            self.serial.write(b'ms\r')

            while True:
                status_text = self.serial.readline()
                if status_text != b'':
                    self.logger.info(status_text)
                else:
                    time.sleep(10)
                    return self.is_sampling() == True
        else:
            return True

    def stop_measurement(self):
        '''
        stop measurement - return True if sampling stopped
        '''
        if self.is_sampling():
            self.serial.write(b'ms\r')

            while True:
                status_text = self.serial.readline()
                if status_text != b'':
                    self.logger.info(status_text)
                else:
                    return self.is_sampling() == False
        else:
            return True
