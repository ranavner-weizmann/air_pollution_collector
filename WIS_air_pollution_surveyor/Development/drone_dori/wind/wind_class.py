
# from ctypes import windll
import logging
from multiprocessing.sharedctypes import Value
import serial
import time
import sys
import datetime

# NAMING VARIABLES
WINDNAME = "FT-732"
WINDPORT = "/dev/wind"
LOCATION = "Drone"
wait = 100e-06
OK = 0

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class Error(Exception):
    '''
    Base class for other exceptions
    '''
    pass

class NoNewDataRecieved(Error):
    '''
    This is raised when no new data is available when polling the microWIND
    '''
    pass

class FailedCommunication(Error):
    '''
    failed communication exception
    '''
    pass
    
class WIND():
    '''
    The following methods are the actual interface:
    init_wind()
    '''
    def __init__(self,
                 wind_name="WIND",
                 wind_port="/dev/wind",
                 wind_location="some_location"):
        self.WINDNAME = wind_name
        self.WINDPORT = wind_port
        self.LOCATION = wind_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        time.sleep(0.5)
        comm_status = self.init_wind()
        if comm_status != OK:
            sys.exit
                           
        logging.info("Instantiated WIND class on port " + self.WINDPORT)
        # super().__init__()

    def init_wind(self):
        '''
        establish communication with WIND return OK if succedded and -1 if failed
        '''
        serial_opts = {
            "port": self.WINDPORT,
            "baudrate": 9600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 5
        }

        logging.info('openning serial port to WIND ' + self.WINDPORT)
        logging.info('initializing communication with WIND')
        self.ser = serial.Serial(**serial_opts)
        return OK

    def close(self):
        '''
        closing the the WIND serial port
        '''
        logging.info('closing serial port ' + self.WINDPORT)
        self.ser.close()
   
    def request_data(self):

        start_time = datetime.datetime.now()               
        time_delta = datetime.timedelta(seconds=50)
        end_time = start_time+time_delta
        byte_len = 35

        data_dict = {}
        strings_array = []

        while datetime.datetime.now() < end_time:
            try:
                new_line = self.ser.readline()
                if len(new_line)<byte_len:
                    pass
                else:
                    decode_line = new_line.decode('utf-8')[8:-9]
                    decode_line2 = decode_line.replace('+','')
                    decode_line3 = decode_line2.replace(' ','')
                    splitted_list = decode_line3.split(',')     

                    temp_list = []
                    for char in splitted_list:
                    
                        temp_list.append(float(char))
                        strings_array.append(temp_list)

                    data_dict['wind_speed']=temp_list[0] 
                    data_dict['wind_direction']=temp_list[1]
                    data_dict['temperature']=temp_list[3]
            except ValueError:
                logging.info("the output bytes are not in the correct form, let's try again")
            except:
                logging.info("there isn't serial communication, probably due some issue with the USB")
 
            time.sleep(0.1)
            return data_dict       
                       
if __name__ == '__main__':
    wind = WIND(wind_name="WIND",
              wind_port="/dev/wind",
              wind_location="drone")
    # if not wind.init_wind() == OK:
    #     sys.exit()
    
    while True:
        data = wind.request_data()
        print(data)
        time.sleep(0.01)
    
    WIND.close()