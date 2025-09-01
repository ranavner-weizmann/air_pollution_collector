import logging
import time
import epics
import os
import yaml

os.chdir('/home/pi/Documents/github/drone_dori/pom')
empty_dict = {}
OK = 0
delay_time = 6
short_time = 0.01

with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

if config_data['pom']['demo']:
    from pom_dummy_class import POM
else:
    from pom_class import POM

logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                level=logging.DEBUG)

def insert_data_into_epics(data):

    if isinstance(data, dict):
        try:  
            pom_dev_epics.ozone = data['ozone']
            pom_dev_epics.cell_temp = data['cell_temp']
            pom_dev_epics.cell_pressure = data['cell_pressure']
            pom_dev_epics.photo_volt = data['photo_volt']
            pom_dev_epics.power_supply = data['power_supply']
            pom_dev_epics.latitude = data['latitude']
            pom_dev_epics.longitude = data['longitude']
            pom_dev_epics.altitude = data['altitude']
            # pom_dev_epics.gps_quality = data['gps_quality']
            # pom_dev_epics.utc_time = data['datetime']

        except KeyError:
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')
            return not OK

if __name__ == "__main__":
    while True:
        try:

            pom = POM(pom_name="pom",
                      pom_port="/dev/pom",
                      pom_location="drone")

            time.sleep(0.1)

            pom_dev_epics = epics.Device('pom:')

            while True:
                if pom_dev_epics.enable==1:
                    data = pom.request_data()
                    if data == empty_dict:
                        logging.info('data is empty, probably due some communication problem')
                        continue
                    else:
                        logging.info(data)
                        insert_data_into_epics(data)
                        logging.info('data inserted into EPICS')
                        time.sleep(3)
                else:
                    logging.info('the pom:enable epics variable is disable. click POM On button in phoebus')
                    time.sleep(3)

        except Exception as e:
            logging.info("Check the physical connection with the POM")
            print(e)
            time.sleep(3)

