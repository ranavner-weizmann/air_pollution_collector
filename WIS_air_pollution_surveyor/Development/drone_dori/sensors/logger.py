#!/home/pi/Documents/drone1/bin/python3


# import numpy as np
# import pandas as pd
import logging
import time
import epics
from datetime import datetime
# import warnings
import os
# from Development.drone_dori.sensors.imu import IMU_RTC
from imu import IMU
from hum import Hum
from opc import Opc
from pom import Pom
from pops import Pops
from sniffer import Sniffer
from wind import Wind
from aeth import Aeth
from gps import GPS
from mceasArduinoPump import mceasArduinoPump
from mceasPressure import mceasPressure
from spectrometer import Spectrometer
from tec import Tec
import argparse
from devices_variables import DEVICES

# warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)
logging.getLogger().setLevel(logging.INFO)
LOG_INTERVAL = 1
DEVICES_TO_LOG = DEVICES

def hide_cursor():
    print('\033[?25l', end="")

def show_cursor():
    print('\033[?25h', end="")


def print_log_start(pv_names_to_log : list) -> None:
    print("*" * 100)
    print("PVs being logged are: ")
    last_index = 0
    number_in_line = 5
    for i in range(number_in_line, len(pv_names_to_log), number_in_line):
        print(", ".join(pv_names_to_log[last_index : i]))
        last_index = i
    print(", ".join(pv_names_to_log[last_index:]))
    print("*" * 100)
    
    hide_cursor()
    print("\033[01m\033[32m" + "Log file is at: " + LOG_FILE + "\033[0m")
    print(f"Log start time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}".ljust(50))
    print("Logging at intervals of " + str(LOG_INTERVAL) + " seconds.")



def log(pv_names_to_log : list, log_file_name: str, interval: int) -> None:

    columns = ["logger_timestamp"] + pv_names_to_log
    epic_data = None
    time_stamp = None
    time_struct = None
    
    # Creating PVs
    # os.system("clear")
    print("Connecting to PVs")
    pvs_list = [epics.PV(name) for name in pv_names_to_log]
    for pv in pvs_list:
        if pv.wait_for_connection(timeout=2) == False:
            print(pv.pvname + " not connected")
    
    print_log_start(pv_names_to_log)
    print("PVs connected")
    number_of_measures = 0
    try:
        log_file = open(log_file_name, "w")
        log_file.write(",".join(columns) + "\n") # Writing headers
        log_file.flush()
        while True:
            try:
                # Fetching data from the epic server
                epic_data = [str(pv.get()) for pv in pvs_list]

                # Saving time stamp of the log
                time_struct = datetime.now()
                time_stamp = time_struct.strftime('%d/%m/%Y %H:%M:%S')
                log_file.write(time_stamp + "," + (",".join(epic_data)).replace('\n', '') + "\n")
                log_file.flush()

            except Exception:
                logging.error("Some exception occured at logger.\nContinuing...")
                
            number_of_measures += 1
            print(f"\rLast logging: {time_stamp}. Number of measures: {number_of_measures}".ljust(50), end="")
            
            # Some information about the epic server
            if epic_data is None:
                    print("Connection error to epics")
            seconds_past = (datetime.now() - time_struct).seconds
            if  seconds_past < interval:
                time.sleep(interval - seconds_past)
            

    finally:
        log_file.close()
        show_cursor()
        print()



def get_device_module(device_name: str):
    sensor_class = None

    if device_name == "imu":
        sensor_class = IMU
    
    elif device_name == "hum":
        sensor_class = Hum

    elif device_name == "opc":
        sensor_class = Opc    

    elif device_name == "pom":
        sensor_class = Pom
    
    elif device_name == "pops":
        sensor_class = Pops
    
    elif device_name == "sniffer":
        sensor_class = Sniffer
    
    elif device_name == "wind":
        sensor_class = Wind

    elif device_name == "aeth":
        sensor_class = Aeth
    
    elif device_name == "gps":
        sensor_class = GPS
    
    elif device_name == "spectrometer":
        sensor_class = Spectrometer

    elif device_name == "mceasPressure":
        sensor_class = mceasPressure

    elif device_name == "tec":
        sensor_class = Tec
    
    elif device_name == "mceasArduinoPump":
        sensor_class = mceasArduinoPump

    else:
        raise Exception("No such device: " + device_name)

    return [f"{device_name}:{pv_name}" for pv_name in sensor_class.PV_NAMES]



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Script to log the drone system. At least one of --devices or --all is required.")
    parser.add_argument("log_file_name", help="File name to put log in")
    parser.add_argument("--devices", help="Devices to log", nargs="+", default = [])
    parser.add_argument("-i", "--interval", default=1, type=float, help="Logging interval (seconds)")
    parser.add_argument("--override", action="store_true")

    args = parser.parse_args()
    assert args.interval > 0, "interval too small. should be > 0"


    LOG_FILE = args.log_file_name
    LOG_FILE = os.path.abspath(LOG_FILE)
    LOG_INTERVAL = args.interval
    DEVICES_TO_LOG = DEVICES
    if (args.devices):
        DEVICES_TO_LOG = args.devices


    if (not args.override) and os.path.exists(LOG_FILE):
        print(f"\033[31mFile: {LOG_FILE} already exists\033[0m")
        exit(1)

    pv_names_to_log = []
    for device in DEVICES_TO_LOG:
        pv_names_to_log += (get_device_module(device))
    
    try:
        log(pv_names_to_log=pv_names_to_log, log_file_name= LOG_FILE, interval = LOG_INTERVAL)
    except KeyboardInterrupt:
        print("Exiting logger")
        