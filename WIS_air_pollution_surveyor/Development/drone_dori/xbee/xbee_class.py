import logging
import sys
import time
import epics
import os
import yaml
import numpy as np
import serial

os.chdir('/home/pi/Documents/github/drone_dori/rtk')
with open('../config/config.yaml') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)

# NAMING VARIABLES
xbeeNAME = "xbee"
xbeePORT = config_data['xbee']['port']
LOCATION = "xbee"
wait = 100e-06
OK = 0
xbeePVs = config_data['xbee']['xbee_PVs']
current_data = {}

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class Xbee:
    """
    Purpose: send to xbee the most recent data from RTK
    """

    def __init__(self,
                 xbee_name="xbee",
                 xbee_port=xbeePORT,
                 xbee_baudrate = 9600,
                 xbee_location="some_location"):
        self.xbeeNAME = xbee_name
        self.xbeePORT = xbee_port
        self.LOCATION = xbee_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        time.sleep(0.5)
        comm_status = self.init_xbee()
        if comm_status != OK:
            sys.exit

        logging.info("Instantiated xbee class on port " + self.xbeePORT)
        # super().__init__()

    def init_xbee(self):
        self.ser = serial.Serial(xbeePORT, baudrate=9600, timeout=1)


    def close(self):
        """
        closing the xbee serial port
        """
        logging.info('closing serial port ' + self.xbeePORT)
        self.ser.close()

    def request_data_from_db(self):
        rtk_dev_epics = epics.Device('rtk:')
        for xbee_var in xbeePVs: 
            current_data.update({xbee_var: rtk_dev_epics.get(xbee_var)})
        return current_data

        """
    limits (N,E): (31.90878, 34.81985), (31.90944, 34.82238), (31.91215, 34.81993), (31.91199, 34.81955)
    
       1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    1  T  2  3  4  5  6  _  2  3  4  5  6  _  1  2  3       =>      target, 31.1(2345)67 N, 31.1(2345)67 E, 123 H 
    2  P  2  3  4  5  6  _  2  3  4  5  6  _  1  2  3       =>      position, 31.1(2345)67 N, 31.1(2345)67 E, 123 H 
    3  D  S  3  4  5  6  _  S  3  4  5  6  _  S  2  3       =>      distance in local frame, if value is too large - will print 9  9  9  9 .... until settles. S is the sign (+/-)
    4  R  1  2  3  P  1  2  3  H  1  2  3  #  1  2  3       =>      roll (to be changed if higher res is possible - 1(2.12) ), pitch, heading (same), # means number of target point
    
       1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20
    1  T  2  3  4  5  6  7  _  2  3  4  5  6  7  _  1  2  3  1  2             =>      target, 31.1(23456)7 N, 31.1(23456)7 E, 123.12 H 
    2  P  2  3  4  5  6  7  _  2  3  4  5  6  7  _  1  2  3  1  2             =>      position, 31.1(23456)7 N, 31.1(23456)7 E, 123.12 H 
    3  D  S  3  4  5  6  7  _  S  3  4  5  6  7  _  S  2  3  1  2             =>      distance in local frame, if value is too large - will print 9  9  9  9 .... until settles. S is the sign (+/-)
    4  R  1  2  3  1  P  1  2  3  1  H  1  2  3  1  #  1  2  3  4             =>      roll (to be changed if higher res is possible - 1(2.12) ), pitch, heading (same), # means number of target point
    
    """


    def rotate_v_by_roll_pitch_heading(v, R, P, H):
        T_geo_to_local_R = np.array([[1, 0, 0], [0, np.cos(R), np.sin(R)], [0, -np.sin(R), np.cos(R)]])
        T_geo_to_local_P = np.array([[np.cos(P), 0, -np.sin(P)], [0, 1, 0], [np.sin(P), 0, np.cos(P)]])
        T_geo_to_local_H = np.array([[np.cos(H), np.sin(H), 0], [-np.sin(H), np.cos(H), 0], [0, 0, 1]])
        T_geo_to_local = np.matmul(T_geo_to_local_R, np.matmul(T_geo_to_local_P, T_geo_to_local_H))
        return np.matmul(T_geo_to_local, v)


    def geo_to_string(geo_coor, first_decimal=1, last_decimal=5):
        # if geo is 31.1234567, returns 12345 (for default values)
        decimal = geo_coor - np.floor(geo_coor)
        decimal_as_str = str(decimal)
        return decimal_as_str[first_decimal + 1:last_decimal + 1 + 1]

    def local_distance_print(x):
        if abs(x) > 1.0:
            y = str(9999)
        else:
            y = str(abs(x) % 1)[2:7]
        return str("+" if x > 0 else "-") + y


    def down_str(x):
        y = (str(int(x)) + str(abs(x) % 1)[2:4])[:5]
        if len(y) == 4:
            y = "0" + y
        if len(y) == 3:
            y = "00" + y
        return y


    def angle_str(x):
        y = str(abs(x))[:3]
        if len(y) == 2:
            y = "0" + y
        if len(y) == 1:
            y = "00" + y
        return str("+" if x > 0 else "-") + y

if __name__ == '__main__':
    xbee = Xbee(xbee_name="Xbee",
                xbee_port=xbeePORT,
                xbee_baudrate = 9600,
                xbee_location="drone")

    while True:
        data = xbee.request_data_from_db()
        print(data)
        time.sleep(0.1)