# %%
import time
import logging
import yaml
import os
os.chdir('/home/pi/Documents/github/drone_dori/spectrometer')
from Spectrometer import *

with open('../config/config.yaml') as file: 
    config_data = yaml.load(file, Loader=yaml.FullLoader)
logging.basicConfig(format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)

def init_spectrometer_from_config():
    c = config_data["spectrometer"]
    spectrometer = Spectrometer(integration_time=c["integration_time"],demo_mode=c["is_demo_mode"],
                                spectrometer_ID=c["spectrometer_ID"],update_rate=c["update_rate"],
                                is_PV=c["is_PV"],name_PV=c["name_PV"],log_dir=c["default_log_dir"],
                                to_log=c["to_log"],add_time_to_filename=c["add_time_to_filename"])
    return spectrometer
                                        

if __name__ == "__main__":
    while True:
        try:
            spectrometer = init_spectrometer_from_config()
            time.sleep(0.1)
            while True:
                spectrometer.measure()
        except Exception as e:
            logging.info(f"{e}. Restarting...")
            time.sleep(3)            

# %%
