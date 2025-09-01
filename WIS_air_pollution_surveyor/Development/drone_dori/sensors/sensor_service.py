#!/home/pi/Documents/drone1/bin/python3
"""
Sensor service for running and logging all the sensors on the drone
Programmers: Nitzan Yizhar
Date 06/07/2023

"""
from sys import exit
from sensor import Sensor
# from Development.drone_dori.sensors.imu import IMU_RTC
from imu import IMU
from hum import Hum
from opc import Opc
from pom import Pom
from pops import Pops
from sniffer import Sniffer
from aeth import Aeth
from wind import Wind
from gps import GPS
from mceasPressure import mceasPressure
from tec import Tec
from ldd1 import Ldd1
from ldd2 import Ldd2
from mceasArduinoPump import mceasArduinoPump
from mceasArduino import MceasArduino
from thermacoupleGroove import ThermacoupleGroove
import yaml, os, logging
import argparse
import json
from datetime import datetime
import time
import sys
from devices_variables import colors
import csv
from setproctitle import setproctitle
import vitals

_DEBUG = False
_LOG = False

try:
    with open("./config.yaml") as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
except FileNotFoundError:
    print("config.yaml not found at " + os.getcwd())
    exit(1)
except Exception as err:
    print("General error while opening config.yaml: " + str(err))
    exit(1)

def retrieve_device(device_name: str) -> (Sensor, list):
    attributes = {"name": device_name}
    sensor_class = None
    vital_attributes = None

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
        from spectrometer import Spectrometer
        sensor_class = Spectrometer
    elif device_name == "stSpectrometer":
        from stSpectrometer import StSpectrometer
        sensor_class = StSpectrometer

    elif device_name == "mceasPressure":
        sensor_class = mceasPressure

    elif device_name == "tec":
        sensor_class = Tec
    
    elif device_name == "mceasArduinoPump":
        sensor_class = mceasArduinoPump

    elif device_name == "thermacoupleGroove":
        sensor_class = ThermacoupleGroove

    elif device_name == "mceasArduino":
        sensor_class = MceasArduino
    
    elif device_name == "ldd2":
        sensor_class = Ldd2
    elif device_name == "ldd1":
        sensor_class = Ldd1
    
    else:
        raise ValueError("Device not found")

    attributes.update(config_data[device_name])
    if 'vital_attributes' in attributes:
        #vital attributes was once defined in the switch case above, but now it's defined in the yaml.
        #it's important to delete the vital_attributes and vital_attributes_lite from the dict because the sensor constructor doesn't expect it (and this data is not needed there)
        vital_attributes = attributes['vital_attributes']
        del attributes['vital_attributes']
        del attributes['vital_attributes_lite']
    return sensor_class(**attributes), vital_attributes


def create_log_file(device, log_folder):
    log_path = os.path.join(log_folder, device.name + "_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".csv")
    log_path = os.path.realpath(log_path)
    
    if os.path.exists(log_path):
        print("Log file exists", file=sys.stderr)
        exit(1)
    
    if not hasattr(device, "PV_NAMES"):
        print("Devices has not attribute PV_NAMES")
        exit(1)
    
    vars = device.PV_NAMES
    if "num_samples" not in vars:
        vars.append("num_samples")
    
    log_file = open(log_path, "w")
    print(f"{colors.CGREENBG}{colors.CWHITE}{device.name.upper()} log file created at: {log_path}{colors.CEND}", file=sys.stderr)
    writer = csv.writer(log_file)
    writer.writerow(["timestamp"] + vars)
    log_file.flush()
    return log_file
    
def write_data_to_log(device, data, log_file, vitality_attributes) -> None:
    measures = [datetime.now().strftime("%m/%d/%Y %H:%M:%S")]
    vars = device.PV_NAMES
    if "num_samples" not in device.PV_NAMES:
        vars.append("num_samples")
    for pv_name in vars:
        value = str(data.get(pv_name, Sensor.Nan))
        value_stripped = value.replace("\n", "")
        measures.append(value_stripped)
    
    writer = csv.writer(log_file)
    writer.writerow(measures)
    log_file.flush()



def main():
    setproctitle(f"python_{sys.argv[1]}")
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help = "Name of the device")
    parser.add_argument("-d", "--debug", action="store_true", help="prints data from sensor")
    parser.add_argument("-lf", "--log-folder", help="Path to folder to put the log in")

    args = parser.parse_args()
    _DEBUG = args.debug
    _LOG_FOLDER = args.log_folder
    _LOG = args.log_folder is not None
    log_file = None

    if (_LOG and not os.path.isdir(_LOG_FOLDER)):
        print(f"{colors.CREDBG}{os.path.realpath(_LOG_FOLDER)} is not a folder.{colors.CEND}")
        exit(1)

    sen, vitality_attributes = None, None
    try:
        sen, vitality_attributes = retrieve_device(args.name)
        delay = sen.vitality_cooldown if hasattr(sen, "vitality_cooldown") else 0.1

        if sen == None:
            raise Exception("Something failed during sensor initialization")    
        if _LOG:
            log_file = create_log_file(sen, _LOG_FOLDER)
        
        while True:
            message = sen.try_read_message()
            if message:
                sen.send_message_to_device(message.encode())

            data = sen.request_data()
            if _LOG and data:
                write_data_to_log(sen, data, log_file, vitality_attributes)

            if _DEBUG and data:
                print(json.dumps(data, indent=4))

            sen.update_pv(data)
            time.sleep(delay)
    
    except Exception as e:
        logging.error(str(e))
    
    finally:
        if sen is not None:
            sen.close()
        if log_file is not None:
            log_file.close()
        exit(1)
    
if __name__ == '__main__':
    main()