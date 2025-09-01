import logging
import time
import epics
import os
import yaml
from datetime import datetime
import pandas as pd

os.chdir('/home/pi/Documents/github/drone_dori/rtk')
empty_dict = {}
OK = 0
delay_time = 0.1

with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

# if config_data['rtk']['demo']:
#     from rtk_dummy_class import rtk
# else:
from rtk_class import RTK

logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                level=logging.DEBUG)

def insert_data_into_epics(data):
    
    # Here I have to check that the dict's names match.

    if isinstance(data, dict):
        try:  
            rtk_dev_epics.xAcc = data['xAcc']
            rtk_dev_epics.yAcc = data['yAcc']
            rtk_dev_epics.zAcc = data['zAcc']
            rtk_dev_epics.xAng = data['xAng']
            rtk_dev_epics.yAng = data['yAng']
            rtk_dev_epics.zAng = data['zAng']
            rtk_dev_epics.longitude = data['longitude']
            rtk_dev_epics.latitude = data['latitude']
            rtk_dev_epics.height = data['height_elips']
            rtk_dev_epics.hMSL = data['height_sea']
            rtk_dev_epics.velN = data['velN']
            rtk_dev_epics.velD = data['velD']
            rtk_dev_epics.velE = data['velE']
            # rtk_dev_epics.head = data['head']
            rtk_dev_epics.numSV = data['numSV']
            rtk_dev_epics.roll = data['roll']
            rtk_dev_epics.pitch = data['pitch']
            rtk_dev_epics.heading = data['heading']
            rtk_dev_epics.accRoll = data['accRoll']
            rtk_dev_epics.accPitch = data['accPitch']
            rtk_dev_epics.accHeading = data['accHeading']

        except KeyError:
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')
            return not OK

if __name__ == "__main__":
    while True:
        try:

            rtk = RTK(rtk_name="rtk",
                      rtk_port="/dev/rtk",
                      rtk_location="drone")

            time.sleep(0.1)

            rtk_dev_epics = epics.Device('rtk:')
            
            while True:
                if rtk_dev_epics.enable==1:
                    data = rtk.request_data()
                    if data == empty_dict:
                        logging.info('data is empty, probably due some communication problem')
                        continue
                    else:
                        logging.info(data)
                        insert_data_into_epics(data)
                        logging.info('data inserted into EPICS')
                        time.sleep(delay_time)
                else:
                    logging.info('the rtk:enable epics variable is disable.Click rtk "On" button in phoebus')
                    time.sleep(3)

        except Exception as e:
            # logging.info("Check the physical connection with the rtk")
            print(e)
            time.sleep(3)
