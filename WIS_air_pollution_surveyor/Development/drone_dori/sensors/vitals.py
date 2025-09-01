import pandas as pd
from enum import Enum
import json
from datetime import datetime
import os
import pyudev
import serial
import time
import sensor_service
import sys
import yaml
from setproctitle import setproctitle
import csv
import pickle

class Version(Enum):
    DICT = 0
    LOG = 1

"""
Create a vitals.csv file that will use the sensor service.
Vitals.py will monitor this file and follow as planned
Also send data over radio if possible. (radio comm will be separate later to another service)

Vitals can operate in two ways, LOG mode and DICT mode
In LOG mode, vitals.csv will act as a log
In DICT mode, vitals.csv will only save the most recent values.
In both modes, we only send the newest data other the radio.
The mode can be controlled with the VITALS_MODE variable.

To support longer experiments, we introduced the lite version of vitals.
Each device has vital_attributes and a vital_attributes_lite.
Both versions of vitals will work at the same mode, but the regular vitals are what will be sent other the radio.
"""
PAUSE_BETWEEN_UPDATES = 1
INVALID_VALUE = -999
VITALS_MODE = Version.LOG
def main():
    setproctitle(f"python_vitals")
    ser = None
    try:
        devices_list = sys.argv[1].split(" ")
        logging_folder = sys.argv[2]
        path_vitals = os.path.join(logging_folder, "vitals.csv")
        path_vitals_lite = os.path.join(logging_folder, "vitals-lite.csv")
        if VITALS_MODE == Version.DICT:
            vitals = startVitalsDict(devices_list, path_vitals)
            vitals_lite = startVitalsDict(devices_list, path_vitals_lite)
    except Exception as e:
        quit(str(e))

    device_to_vitals_attributes = {}
    device_to_vitals_attributes_lite = {}
    try:
        with open("./config.yaml") as file:
            config_data = yaml.load(file, Loader=yaml.FullLoader)
    except:
        print("config.yaml not found at " + os.getcwd())
        exit(1)
    for device in devices_list:
        device_to_vitals_attributes[device] = config_data[device]['vital_attributes']
        device_to_vitals_attributes_lite[device] = config_data[device]['vital_attributes_lite']
    if VITALS_MODE == Version.LOG:
        startVitalsLog(devices_list, device_to_vitals_attributes, path_vitals)
        startVitalsLog(devices_list, device_to_vitals_attributes_lite, path_vitals_lite)
    
    radio_port = getRadioSerialPort()

    while True:
        #for each devices get last row
        try:
            data_dict = getVitalsFromDevices(device_to_vitals_attributes, logging_folder)
            data_dict_lite = getVitalsFromDevices(device_to_vitals_attributes_lite, logging_folder)
            if VITALS_MODE == Version.DICT:
                write_vitals_to_csv_dict(vitals, data_dict, path_vitals)            
                write_vitals_to_csv_dict(vitals_lite, data_dict_lite, path_vitals_lite)
            elif VITALS_MODE == Version.LOG:
                write_vitals_to_csv_log(data_dict, path_vitals, device_to_vitals_attributes)
                write_vitals_to_csv_log(data_dict_lite, path_vitals_lite, device_to_vitals_attributes_lite)
        except Exception as e:
            if ser:
                ser.close()
            quit(str(e))
        #send data in radio
        if radio_port is not None and not ser:
            ser = serial.Serial(radio_port, baudrate = 9600)  
        elif radio_port is None:
            radio_port = getRadioSerialPort()
            if radio_port:
                ser = serial.Serial(radio_port, baudrate = 9600)  
        if ser:
            vitals_data_bytes = pickle.dumps(data_dict)
            try:
                ser.write(vitals_data_bytes)
            except Exception as e:
                ser.close()
                ser = None
                print(f"Failed to write to serial port: {e}")            

        time.sleep(PAUSE_BETWEEN_UPDATES)
    

def getPVNAMEFromDeviceAttribute(device: str, attribute: str) -> str:
    """
    Parameters
    ----------
        device - name of device

        attribute - name of attribute

    Output
    ------
        A column name for the log in vitals.csv for this attribute of this device
    """
    return device + "_" + attribute

def startVitalsLog(devices_list: list[str], device_to_vitals_attributes: dict[str, list[str]], path_vitals: str) -> None:
    """
    Parameters
    ----------
        devices_list - a list of all the active devices

        device_to_vitals_attributes - a dictionary that maps between each device and it's vital attributes

        path_vitals - the path of the vitals file

    This function initializes vitals file in LOG mode at the specified path
    """
    PV_NAMES = ["timestamp"]
    for device in devices_list:
        for attribute in device_to_vitals_attributes[device]:
            field_name = getPVNAMEFromDeviceAttribute(device, attribute)
            PV_NAMES.append(field_name)
    with open(path_vitals, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PV_NAMES)

def startVitalsDict(device_list: list[str], path_vitals: str) -> pd.DataFrame:
    """
    Parameters
    ----------
        devices_list - a list of all the active devices

        path_vitals - the path of the vitals file

    Output
    ------
        a data frame for vitals

    This function initializes vitals file in DICT mode at the specified path
    """
    data = {
        "Device Name" : device_list,
        "Measurement" : [json.dumps({}) for _ in device_list],
        "Data Time": [pd.to_datetime(datetime.now())for _ in device_list]
    }    
    vitals = pd.DataFrame(data)
    vitals.to_csv(path_vitals, index=False)    
    return vitals


def getRadioSerialPort()-> str | None:
    """
    Output
    ------
        The serial port for the radio if the device is found
        None if the device wasn't found
    """
    id_vendor = "0403"
    id_model = "6015"
    id_serial = "FTDI_FT230X_Basic_UART_D3088KZL"
    device_list = pyudev.Context().list_devices()
    for device in device_list.match_subsystem("tty"):
        device_vendor = device.get("ID_VENDOR_ID")
        device_model = device.get("ID_MODEL_ID")
        device_serial = device.get("ID_SERIAL")
        found_vendor = id_vendor == device_vendor
        found_model = id_model == device_model
        found_serial = id_serial == device_serial
        if found_vendor and found_model and found_serial:
            return str(device.device_node)
    return None
        
def getFirstAndLastLineOfFile(filePath:str)-> list[str] | None:
    """
    Parameters
    ----------
        filePath - the path to the file we want to read the first and last line from

    Output
    ------
        a list of length two with the first line of the line and then the last line

    The function extracts the first and last line of a file and returns the result.
    If there are less then two lines, None will be returened
    """
    lines=[]
    with open(filePath, "rb") as file:
        lines.append(file.readline().decode().strip())        
        try:
            # Go to the end of the file before the last break-line
            file.seek(-2, os.SEEK_END) 
            # Keep reading backward until you find the next break-line
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR) 
            lines.append(file.readline().decode().strip())
        except OSError:
            #we reached the start of the file and can't go anymore backwards. this means there was only one line in the file and we should return None
            return None
    return lines

def shouldFileBeReplaced(currentFile:str, newFile:str)->bool:
    """
    Parameters
    ----------
        currentFile - the name of the file that vitals is currently reading from

        newFile - the name that we want to compare with

    Output
    ------
        True if the newFile is newer than the current file and should be replaced

    the function goes through the date in the file name and checks if the file is newer
    the order it checks is: year, month, day, hours, minutes, seconds
    the current format of the file paths is:
    DEVICE_DAY_MONTH_YEAR_HOUR_MINUTE_SECONDS
    """
    currentFileSplitted = currentFile.split(".")[0].split("_")
    newFileSplitted = newFile.split(".")[0].split("_")
    if(currentFileSplitted[0] != newFileSplitted[0]):
        #files are related to different devices, maybe add log
        return False

    YEAR_INDEX = 3
    MONTH_INDEX = 2
    DAY_INDEX = 1
    HOUR_INDEX = 4
    MINUTE_INDEX = 5
    SECOND_INDEX = 6
    orderedIndices = [YEAR_INDEX, MONTH_INDEX, DAY_INDEX, HOUR_INDEX, MINUTE_INDEX, SECOND_INDEX]
    for index in orderedIndices:
        try:
            currentFileField = int(currentFileSplitted[index])
            newFileField = int(newFileSplitted[index])
        except ValueError:
            #malformed file name, maybe add log
            return False
        if newFileField > currentFileField:
            #if the new field is bigger in the new file, file should be replaced
            return True
        if currentFileField > newFileField:
            #if the current field is bigger, file should not be replaced
            return False

    #if we finished the loop but not returned, this means that the file names are equal, this should be logged even though this should never happen
    return False

def getVitalsFromDevices(device_to_vitals_attributes: dict[str, list[str]], logging_folder: str)->dict:
    """
    Parameters
    ----------
        device_to_vitals_attributes - list of string representing device names

        logging_folder - directory to look for csv files

    Output
    ------
        A dictionary where all keys are taken from the devices list and the value is the last line of the most recent csv file that belong to that device

    the function loops on all the files, tries to find the most recent file for each device,
    then for each device it goes to its most recent file and extracts the last line using getLastLineOfCSVFile
    """
    mostRecentFilePathsForDevice={}
    deviceVitals={}
    for deviceName in device_to_vitals_attributes:
        mostRecentFilePathsForDevice[deviceName] = None
        deviceVitals[deviceName] = None

    for file_path in os.listdir(logging_folder):
        # check if current file_path is a file
        if os.path.isfile(os.path.join(logging_folder, file_path)):
            splittedFileName = file_path.split(".")[0].split("_")
            currentDevice = splittedFileName[0]
            if currentDevice not in mostRecentFilePathsForDevice:
                #this device is not in our dict
                continue
            elif mostRecentFilePathsForDevice[currentDevice] is None:
                mostRecentFilePathsForDevice[currentDevice] = file_path
            else:
                if shouldFileBeReplaced(mostRecentFilePathsForDevice[currentDevice], file_path):
                    mostRecentFilePathsForDevice[currentDevice] = file_path
    for deviceName, vitalValues in device_to_vitals_attributes.items():
        if mostRecentFilePathsForDevice[deviceName] is None:
            deviceVitals[deviceName] = None
            #there was a device that no path was found for it
            continue
        lines = getFirstAndLastLineOfFile(os.path.join(logging_folder, mostRecentFilePathsForDevice[deviceName]))
        if lines is None:
            deviceVitals[deviceName] = None
            continue
        splittedTitles = lines[0].split(",")
        splittedvalues = list(csv.reader([lines[1]]))[0]
        vitalDict={}
        for vitalValue in vitalValues:
            index = splittedTitles.index(vitalValue)
            vitalDict[vitalValue] = splittedvalues[index]
        deviceVitals[deviceName] = vitalDict
    return deviceVitals

def write_vitals_to_csv_dict(vitals: pd.DataFrame ,data_dict: dict, path_vitals: str) -> None:
    """
    Parameters
    ----------
        vitals - dataframe to update

        data_dict - vitals values to update

        path_vitals - the path of the vitals file
    
    writes the data from data_dict to vitals in DICT mode.
    """
    #for each devices update vitals data
    if data_dict:
        for device in data_dict.keys():
            new_data = data_dict[device]
            if not new_data:
                continue
            data_time = new_data.pop("timestamp")
            vitals.loc[vitals["Device Name"] == device, "Measurement"] = json.dumps(new_data)
            vitals.loc[vitals["Device Name"] == device, "Data Time"] = pd.to_datetime(data_time)
        #use dataframe in future usage for the radio
        vitals.to_csv(path_vitals, index=False)

def write_vitals_to_csv_log(data_dict: dict, path_vitals: str, device_to_vitals_attributes: dict) -> None:
    """
    Parameters
    ----------
        data_dict - vitals values to update

        path_vitals - the path of the vitals file

        device_to_vitals_attributes - list of string representing device names
    
    writes the data from data_dict to vitals in LOG mode.
    """
    #for each devices write vitals data
    if not data_dict:
        return
    csv_row = [datetime.now().strftime("%m/%d/%Y %H:%M:%S")]
    for device in data_dict.keys():
        collected_device_data = data_dict[device]
        vitals_parameters_amount = len(device_to_vitals_attributes[device])
        new_data = [INVALID_VALUE] * vitals_parameters_amount
        if collected_device_data:
            if len(collected_device_data) != vitals_parameters_amount:
                #TODO: add logger to vitals
                print("VITALS_ERROR: GOT WRONG AMOUNT OF PARAMETERS FROM FILE")
            for i, attribute in enumerate(device_to_vitals_attributes[device]):
                new_data[i] = collected_device_data.get(attribute, INVALID_VALUE)               
        csv_row.extend(new_data)    
    with open(path_vitals, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_row)    

            
if __name__ == '__main__':
    main()
        