#!/bin/python3
import sys
sys.path.append("..")
import re
import subprocess
from imu_rtc import IMU_RTC
from datetime import datetime


def main(args):
    '''
    Updates the time of the Pi by taking it from the RTC connected to the arduino.
    '''

    sen = IMU_RTC("clock", location="", demo_mode = False, is_device=False, device_name="")
    data = None
    time = None

    while data is None:
        data = sen.request_data()
        if data:
            time = data["time"]
            break;
    # Got the time from the arudino
    sen.close()

    assert re.match("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", time), "Date taken doesn't fit pattern"
    time = datetime.strptime(time, "%d/%m/%Y %H:%M:%S")
    proc = subprocess.run([f"sudo date -s '{time}'"], shell=True) # This changes the time in the machine

    print(f"\033[92mMachine time changed to: {time}\033[0m")
    

if __name__ == "__main__":
    main(sys.argv)



