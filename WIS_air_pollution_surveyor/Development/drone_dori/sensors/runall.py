#!/home/pi/evia/venv/bin/python
"""#!/home/pi/Documents/drone1/bin/python3"""
'''
Python script for running the entire drone system for measuring.
Written by: Nitzan Yizhar
Date: 09/07/2023
'''







import time
import logging
import os
import subprocess
from time import sleep
from sys import exit
import argparse
from datetime import datetime
from serviceMenu import ServiceMenu
from devices_variables import *
import sys
import json
import vitals

global log_format
log_format = '%(asctime)s %(filename)s: %(message)s'




def start_epic_server(devices_list):
    dbs = "".join([" -d " + os.path.join(DB_PATH, device + ".db") for device in devices_list])
    #if problem with epics, use this line instead:
    #return ["epics", subprocess.Popen(['softIoc -S ' + dbs], shell=True)]    
    return ["epics", subprocess.Popen(['softIoc -S ' + dbs], shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)]


def start_logger(devices_list, log_name = "drone_flight_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".csv"):
    arguments = [LOGGER_PATH, log_name]
    if devices_list is not DEVICES:
        devices_to_log = "--devices " + " ".join(devices_list)
        arguments.append(devices_to_log)

    return ["logger", subprocess.Popen(arguments)]

def start_service(device_name, LOGGING_FOLDER):
    return [device_name, subprocess.Popen(["/home/pi/evia/venv/bin/python", SERVICE_PATH, device_name, "-lf", LOGGING_FOLDER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env={**os.environ, "SENSOR_LABEL": device_name} )]
    return [device_name, subprocess.Popen([SERVICE_PATH, device_name], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)]

def start_vitals(devices_list, logging_folder):
    # vitals.main(devices_list, logging_folder)
    devices_str = ' '.join(devices_list)
    return ["vitals", subprocess.Popen(["/home/pi/evia/venv/bin/python", "./vitals.py", devices_str, logging_folder])]
    


def main():
    #is used for bash script to check if runall is running
    
            
    logging.basicConfig(filename = "/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/boot_log.txt", level = logging.DEBUG)
    parser = argparse.ArgumentParser(description="Script to run the drone system runs all devices by default")
    # parser.add_argument("path_to_config", help="path to config.yaml file")
    # parser.add_argument("path_to_service", help="path to service file.")
    parser.add_argument("--devices", help="Devices to run", nargs="+", type=str, default=[])
    # parser.add_argument("--all", help="Run all devices on drone", action="store_true")
    parser.add_argument('--debug', action='store_true', help='Enable debugging')
    args = parser.parse_args()
    if not args.debug:
        with open("/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/is_on.txt", "w") as f:
            f.write("On")

    
    devices_list = DEVICES
    if (args.devices):
        devices_list = args.devices

    
    # Saftey measures
    for device in devices_list:
        if device not in DEVICE_OPTIONS:
            print(f"Device: {device} not a valid device")
            exit(1)
    
    LOGGING_FOLDER = "./logs/logs_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    LOGGING_FOLDER = os.path.realpath(LOGGING_FOLDER)
    if (os.path.exists(LOGGING_FOLDER)):
        print(f"{colors.CREDBG}Cannot create loggin folder.{colors.CEND}", file=sys.stderr)
        exit(1)
    
    


    processes = []
    os.system("clear")
    os.mkdir(LOGGING_FOLDER)
    log_path = os.path.join(LOGGING_FOLDER, "main_log_")
    log_path +=  str(datetime.now().strftime("%m_%d_%Y_%H_%M_%S")) + ".txt"
    log_path = os.path.realpath(log_path)
    with open("/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/main_log_path.txt", "w") as f:
        f.write(log_path+"\n")
        f.write(log_format)
    # logging.basicConfig(filename=log_path, format=log_format, level=logging.INFO)
    print("PID for terminating: ", os.getpid())
    print(f"{colors.CGREENBG}Log files are at {LOGGING_FOLDER}{colors.CEND}", file=sys.stderr)

    try:
        print("Starting epics server")
        proc = start_epic_server(devices_list)
        processes.append(proc)
        time.sleep(3)
        if (proc[1].poll() is not None):
            print("Epics server failed to run")
            exit(1)
         
        print("Epic server started")

        # Starting devices services.
        for device in devices_list:
            processes.append(start_service(device, LOGGING_FOLDER))
        
        sleep(5)

        #starting vitals service
        processes.append(start_vitals(devices_list, LOGGING_FOLDER))

        print("All devices services intialized")
        
        
        # time.sleep(5)
        # proc = start_logger(devices_list)
        # processes.append(proc)
        # if (proc[1].poll() is not None):
        #     print("Logger failed to run")
        #     exit(1)

        # logging.info("Logger started!")
        
        serviceMenu = ServiceMenu()
        while True:
            if serviceMenu.should_start():
                processName, message = serviceMenu.start()
                processesNames = [processPair[0] for processPair in processes]
                processIndex = processesNames.index(processName)
                process = processes[processIndex][1]
                process.stdin.write(message.encode())
                process.stdin.flush()
            for i, proc_info in enumerate(processes):
                if not proc_info:
                    processes.pop(i)
                    continue
                device, proc = proc_info
                if proc == None:
                    continue
                
                try:
                    poll = proc.poll()
                except Exception as err:
                    poll = 1
                    
                
                # Restarting in case a service crashes for some reason.
                if  poll is not None:
                    # Something happend to the device --> run service again
                    logging.error("Service crashed: " + device)
                    if (device in DEVICE_OPTIONS):
                        processes[i] = start_service(device, LOGGING_FOLDER)
                    elif device == "epics":
                        processes[i] = start_epic_server(devices_list)
                    elif device == "logger":
                        processes[i] = start_logger(devices_list)
                    elif device == "vitals":
                        processes[i] = start_vitals(devices_list, LOGGING_FOLDER)
                        
                    
            sleep(5)
    except Exception as e:
        logging.error(str(e))

    finally:        
        print("\n\n\x1b[31;20mTerminating... Please don't press anything until proccess dies\x1b[0m\n\n")
        for proc_info in processes:
            proc = proc_info[1]
            if proc.poll() is None:
                try:
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    # Just in case the process wont shut down on its own. We send it a singal to terminate
                    logging.critical("Terminating " + proc_info[0])
                    proc.terminate()
                    proc.wait()
        proc = processes[0]
        os.system('pkill -9 -f "softIoc"')
        exit(0)
    
    

    
### We want to  create a device for each sensor on the drone for instance
if __name__ == '__main__':
    main()    
