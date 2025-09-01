import time
import logging
import numpy as np
import epics
import yaml
import serial


import os
os.chdir('/home/pi/Documents/github/drone_dori/humidity')

# read config file and send to logger object
with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

if config_data['humidity']['demo']:
    from humidity_dummy_class import HUMIDITY
else:
    from humidity_class import HUMIDITY

empty_dict = {}
delay_time = 0.01
TIMEOUT = 100
OK = 0

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


def insert_data_into_epics(data):
    '''
     {'speed': np.random.random(), 'direction': np.random.random(), 'utcTime': now.strftime("%m/%d/%Y-%H:%M:%S")} 
    '''
#   'pressure','temp','rel_hum','hum_temp','longitude','latitude','altitude','sat'

    if isinstance(data, dict):
        try:  
            hum_dev_epics.pressure = data['pressure']
            hum_dev_epics.temp = data['temp']
            hum_dev_epics.rel_hum = data['rel_hum']
            hum_dev_epics.hum_temp = data['hum_temp']
            hum_dev_epics.longitude = data['longitude']
            hum_dev_epics.latitude = data['latitude']
            hum_dev_epics.altitude = data['altitude']
            hum_dev_epics.sat = data['sat']

        except KeyError as e:
            print(e)
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')
            return not OK
    
if __name__ == "__main__":
    while True:
        try:

            humidity = HUMIDITY(humidity_name="humidity",
                      humidity_port="/dev/hum",
                      humidity_location="drone")

            time.sleep(0.05)

            hum_dev_epics = epics.Device('hum:')

            while True:
                if hum_dev_epics.enable==1:
                    data = humidity.request_data()
                    if data == empty_dict:
                        logging.info('data is empty, probably due some communication problem')
                        continue
                    else:
                        logging.info(data)
                        insert_data_into_epics(data)
                        logging.info('data inserted into EPICS')
                        time.sleep(delay_time)
                else:
                    logging.info('the humidity:enable epics variable is disable. click humidity On button in phoebus')
                    time.sleep(0.5)
        except Exception as e:
            logging.info("Check the physical connection with the humidity sensor")
            print(e)
            time.sleep(3)