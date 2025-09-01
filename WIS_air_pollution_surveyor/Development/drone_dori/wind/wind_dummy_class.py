import logging
import sys
import time
import numpy as np
from datetime import datetime

integration = 5

# NAMING VARIABLES
WINDNAME = "FT-742"
WINDPORT = "some_port"
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
    This is raised when no new data is available when polling the windSENSOR
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
                 wind_name="TestWIND",
                 wind_port="some_port",
                 wind_location="some_location"):
        self.WINDNAME = wind_name
        self.WINDPORT = wind_port
        self.LOCATION = wind_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        
        logging.info("Instantiated WIND class on port " + self.WINDPORT)
        # super().__init__()

    def init_wind(self):
        '''
        establish communication with WIND return OK if succedded and -1 if failed
        '''
        
        logging.info('openning serial port to wind ' + self.WINDPORT)
        logging.info('initializing communication with WIND')
        return OK

    def close(self):
        '''
        closing the the WIND serial port
        '''
        logging.info('closing serial port ' + self.WINDPORT)
   
    
    def request_data(self):
        '''
        request data from wind. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        now = datetime.now()

        data_dict = {'wind_speed': np.random.random(), 'wind_direction': np.random.random(), 'temperature': np.random.random() }
                                                
        return data_dict       
                       
if __name__ == '__main__':
    wind = WIND(wind_name="WindFT-742",
              wind_port="some_port",
              wind_location="drone")
    if not wind.init_wind() == OK:
        sys.exit()
    
    while True:
        data = wind.request_data()
        print(data)
        time.sleep(0.01)
    
    wind.close()