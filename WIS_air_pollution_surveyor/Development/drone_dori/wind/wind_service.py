import time
import logging
import numpy as np
import epics
import yaml
import serial


import os
os.chdir('/home/pi/Documents/github/drone_dori/wind')

# read config file and send to logger object
with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

if config_data['wind']['demo']:
    from wind_dummy_class import WIND
else:
    from wind_class import WIND

empty_dict = {}
delay_time = 0.1
TIMEOUT = 100
OK = 0

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


def insert_data_into_epics(data):
    '''
     {'speed': np.random.random(), 'direction': np.random.random(), 'utcTime': now.strftime("%m/%d/%Y-%H:%M:%S")} 
    '''
    
    if isinstance(data, dict):
        try:  
            wind_dev_epics.speed = data['wind_speed']
            wind_dev_epics.direction = data['wind_direction']
            wind_dev_epics.temperature = data['temperature']
        except KeyError:
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')
            return not OK
    
if __name__ == "__main__":
    while True:
        try:

            wind = WIND(wind_name="wind",
                      wind_port="/dev/wind",
                      wind_location="drone")

            time.sleep(0.05)

            wind_dev_epics = epics.Device('wind:')

           # this block of code run in two option: 
           # 1. demo mode. 2. real mode, after serial communication was created.

            while True:
                if wind_dev_epics.enable==1:
                    data = wind.request_data()
                    if data == empty_dict:
                        logging.info('data is empty, probably due some communication problem')
                        continue
                    else:
                        logging.info(data)
                        insert_data_into_epics(data)
                        logging.info('data inserted into EPICS')
                        time.sleep(delay_time)
                else:
                    logging.info('the wind:enable epics variable is disable. click Wind On button in phoebus')
                    time.sleep(0.5)
        except Exception as e:
            logging.info("Check the physical connection with the FT72")
            print(e)
            time.sleep(3)
