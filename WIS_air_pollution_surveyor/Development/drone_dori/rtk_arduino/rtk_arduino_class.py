import logging
import serial
import time
import sys
import json

RTKNAME = "RTK"
# RTKPORT = "/dev/arduino"
RTKPORT = "/dev/arduino"
RTKLOCATION = "Drone"
OK = 0
time_delay = 0.1

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class RTK():

    def __init__(self,
                 rtk_name=RTKNAME,
                 rtk_port=RTKPORT):
        self.RTKNAME = rtk_name
        self.RTKPORT = rtk_port
        time.sleep(0.5)
        comm_status = self.init_rtk()
        if comm_status != OK:
            sys.exit
                           
        logging.info("Instantiated rtk class on port " + self.RTKPORT)
  
    def init_rtk(self):
        '''
        establish communication with rtk return OK if succedded and -1 if failed
        '''
        serial_opts = {
            "port": self.RTKPORT,
            "baudrate": 115200}

        logging.info('openning serial port to rtk ' + self.RTKPORT)
        logging.info('initializing communication with rtk')
        self.ser = serial.Serial(**serial_opts)
        return OK

    def request_data(self):

        while True:
            try:
                data_string_line = self.ser.readline()
                if data_string_line == b'Start Measurement\r\n':
                    data_string_line = self.ser.readline()
                    while data_string_line != b'End of Measurement\r\n':
                        data_string_line = data_string_line.rstrip()
                        json_string = data_string_line.decode('utf-8')
                        data_dict = json.loads(json_string)
                        data_string_line = self.ser.readline()
                    break
                # if data_string line is not 'Start Measurement'
                else:
                    continue 
            except:
                logging.info("Error occured while trying to read data from RTK")       
                    

            # break when self.ser.readline() == 'Stop Measurment'


        return data_dict


if __name__ == '__main__':

    rtk = RTK(rtk_name=RTKNAME,
                rtk_port=RTKPORT)

    while True:
        data = rtk.request_data()
        print(data)
        time.sleep(0.01)