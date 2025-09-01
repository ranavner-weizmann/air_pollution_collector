import logging
import time
import epics
import os
import yaml
from datetime import datetime
import pandas as pd


empty_dict = {}
OK = 0
delay_time = 0.1
with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

from rtk_arduino_class import RTK

logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                level=logging.DEBUG)

def insert_data_into_epics(data):

    if isinstance(data, dict):
        try:
            if 'FusionMode' in data.keys():  
                rtk_dev_epics.FusionMode = data['FusionMode']
            if 'Ground Speed' in data.keys(): 
                rtk_dev_epics.GroundSpeed = data['Ground Speed']
            if 'Lat' in data.keys(): 
                rtk_dev_epics.Lat = data['Lat']
            if 'Long' in data.keys(): 
                rtk_dev_epics.Long = data['Long']
            if 'X Ang Rate' in data.keys(): 
                rtk_dev_epics.xAngRate = data['X Ang Rate']
            if 'Y Ang Rate' in data.keys(): 
                rtk_dev_epics.yAngRate = data['Y Ang Rate']
            if 'Z Ang Rate' in data.keys(): 
                rtk_dev_epics.zAngRate = data['Z Ang Rate']
            if 'X Accel' in data.keys(): 
                rtk_dev_epics.xAccel = data['X Accel']
            if 'Y Accel' in data.keys(): 
                rtk_dev_epics.yAccel = data['Y Accel']
            if 'Z Accel' in data.keys(): 
                rtk_dev_epics.zAccel = data['Z Accel']
            if 'Pitch' in data.keys(): 
                rtk_dev_epics.pitch = data['Pitch']
            if 'Roll' in data.keys(): 
                rtk_dev_epics.roll = data['Roll']
            if 'Heading' in data.keys(): 
                rtk_dev_epics.heading = data['Heading']
            if 'Status' in data.keys(): 
                rtk_dev_epics.status = data['Status']
            

        except KeyError:
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')
            return not OK

if __name__ == "__main__":
    while True:
        try:
            rtk = RTK(rtk_name="RTK",
                      rtk_port="/dev/arduino")
            time.sleep(0.1)
            rtk_dev_epics = epics.Device('rtk_arduino:')
            
            while True:
                if rtk_dev_epics.enable==1:
                    data = rtk.request_data()
                    if data == empty_dict:
                        logging.info('Data is empty, probably due some communication problem')
                        continue
                    else:
                        logging.info(data)
                        insert_data_into_epics(data)
                        logging.info('data inserted into EPICS')
                        time.sleep(delay_time)
                else:
                    logging.info('the rtk:enable epics variable is disable, click rtk "On" button in phoebus')
                    time.sleep(3)

        except Exception as e:
            print(e)
            time.sleep(3)