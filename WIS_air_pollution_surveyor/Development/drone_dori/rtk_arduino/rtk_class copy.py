import logging
import serial
import time
import sys

RTKNAME = "RTK"
RTKPORT = "/dev/arduino"
RTKLOCATION = "Drone"
OK = 0
time_delay = 0.25

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

        new_line = self.ser.readline()


        return new_line


if __name__ == '__main__':

    rtk = RTK(rtk_name=RTKNAME,
                rtk_port=RTKPORT)

    while True:
        data = rtk.request_data()
        print(data)
        # time.sleep(time_delay)