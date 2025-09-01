import logging
import time
import epics
import os
import yaml
import numpy as np
import serial
from xbee_class import Xbee

os.chdir('/home/pi/Documents/github/drone_dori/rtk')
empty_dict = {} # or None
OK = 0
delay_time = 0.1

with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


targets = config_data['xbee']['targets']

target_id = 0

def calc_string_to_xbee():
    # example data:
    """north_target, east_target, down_target = 31.923727, 34.827658, 0.05
    north_position, east_position, down_position = 31.913640, 34.817652, 179.12
    roll, pitch, heading = -265, 3, 120"""

    current_target = targets[target_id]

    real_time_location = xbee.request_data_from_db()

    north_position = real_time_location.get("longitude")
    east_position = real_time_location.get("latitude")
    down_position = real_time_location.get("height")
    geo_position = np.array([north_position, east_position, down_position])  # ########

    # if button pressed options:
    if xbee_ser.read() == "next" :
        """calc for next target"""
        current_target = targets[target_id+1]
    elif xbee_ser.read() == "previous" :
        """calc for previous target"""
        current_target = targets[target_id-1]
    else:
        """calc for current target"""
        pass
    north_target = current_target.get("longitude")
    east_target = current_target.get("latitude")
    down_target = current_target.get("height")
    geo_target = np.array([north_target, east_target, down_target])  # #####
    
    distance_geo = geo_target - geo_position
    current_roll = real_time_location.get("roll")
    current_pitch = real_time_location.get("pitch")
    current_heading = real_time_location.get("heading")
    distance_local = Xbee.rotate_v_by_roll_pitch_heading(distance_geo,
                                                         current_roll, current_pitch,current_heading)
    

    row1 = "$1T" + Xbee.geo_to_string(geo_target[0]) + "__" + Xbee.geo_to_string(
        geo_target[1]) + "__" + Xbee.down_str(geo_target[2])
    row2 = "$2P" + Xbee.geo_to_string(geo_position[0]) + "__" + Xbee.geo_to_string(
        geo_position[1]) + "__" + Xbee.down_str(geo_position[2])
    row3 = "$3D" + Xbee.local_distance_print(distance_local[0]) + "__" + Xbee.local_distance_print(
        distance_local[1]) + "__" + Xbee.local_distance_print(distance_local[2])[:5]
    row4 = "$4R" + Xbee.angle_str(current_roll) + "_P" + Xbee.angle_str(current_pitch) + "_H" + Xbee.angle_str(
        current_heading) + "_" + "nm"
    massage = row1 + row2 + row3 + row4
    print(massage)
    return massage


if __name__ == "__main__":
    while True:
        try:
            xbee = Xbee(xbee_name="xbee",
                        xbee_port="/dev/ttyUSB0",
                        xbee_baudrate=9600,
                        xbee_location="drone")
            time.sleep(0.1)
            xbee.init_xbee()
            xbee_ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.050)

            rtk_dev_epics = epics.Device('rtk:')

            while True:
                if rtk_dev_epics.enable == 1:
                    data = xbee.request_data_from_db()
                    if data == empty_dict:
                        logging.info('data is empty, probably due some communication problem')
                        continue
                    else:
                        massage = calc_string_to_xbee()
                        xbee_ser.write(massage.encode())
                        logging.info('data sent to xbee')
                        time.sleep(delay_time)
                else:
                    logging.info('xbee :something with epix')
                    time.sleep(3)

        except Exception as e:
            # logging.info("Check the physical connection with the xbee")
            print(e)
            time.sleep(3)