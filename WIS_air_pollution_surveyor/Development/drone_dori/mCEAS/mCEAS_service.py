# %%
import time
import logging
import yaml
import os
os.chdir('/home/pi/Documents/github/drone_dori/mCEAS')
from MCEAS import *

with open('../config/config.yaml') as file: 
    config_data = yaml.load(file, Loader=yaml.FullLoader)
logging.basicConfig(format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)
c = config_data["mCEAS"]

def init_mCEAS_from_config():
    mCEAS = MCEAS(arduino_port=c["arduino_port"],update_rate=c["update_rate"],is_demo_mode=c["is_demo_mode"],
                  default_log_dir=c["default_log_dir"],measured_gases_and_sigma_filenames=c["measured_gases_and_sigma_filenames"],
                  atmospheric_gases_and_sigma_filenames=c["atmospheric_gases_and_sigma_filenames"],d_full=c["d_full"],
                  d_purging=["d_purging"], R_filename=c["reflectivity_filename"], R_wavelengths_filename=c["reflectivity_wavelengths_filename"],
                  I0=c["I0_filename"],T0=c["T0"],P0=c["P0"],I0_NO2=c["I0_NO2"],
                  name_PV=c["name_PV"],spectrometer_name_PV=config_data["spectrometer"]["name_PV"],
                  measurement_gases=c["measurement_gases"],arduino_params=c["arduino_params"],to_log=c["to_log"],log_filename=c["log_filename"])
    return mCEAS

if __name__ == "__main__":
    while True:
        try:
            mCEAS = init_mCEAS_from_config()
            try:
                mCEAS.load_reflectivity()
            except Exception as e:
                logging.info(f"{e}. Calculating and saving new reflectivity...")
                mCEAS.init_and_save_reflectivity(
                    c["lab_reflectivity_Is1"],c["lab_reflectivity_Is2"],
                    c["reflectivity_Ps1"],c["reflectivity_Ps2"],c["reflectivity_Ts1"],c["reflectivity_Ts2"],
                    c["lab_reflectivity_names1"],c["lab_reflectivity_names2"]
                )
            time.sleep(0.1)
            while True:
                mCEAS.measure()
        except Exception as e:
            logging.info(f"{e}. Restarting...")
            time.sleep(3)            

# %%
