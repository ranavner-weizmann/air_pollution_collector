import logging
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime

integration = 5

# NAMING VARIABLES
POMNAME = "POM"
POMPORT = "/dev/ttyACM0"
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


class FailedCommunication(Error):
    '''
    failed communication exception
    '''
    pass
    
class POM():
    
    def __init__(self,
                 pom_name="POM",
                 pom_port="pom",
                 pom_location="drone"):
        self.POMNAME = pom_name
        self.POMPORT = pom_port
        self.LOCATION = pom_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        
        logging.info("Instantiated POM class on port " + self.POMPORT)
        # super().__init__()

    def init_pom(self):
        '''
        establish communication with POM return OK if succedded and -1 if failed
        '''
        
        logging.info('openning serial port to pom ' + self.POMPORT)
        logging.info('initializing communication with POM')
        return OK

    def close(self):
        '''
        closing the the POM serial port
        '''
        logging.info('closing serial port ' + self.POMPORT)
   
    
    def request_data(self):
        '''
        request data from wind. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        now = datetime.now()

        data_dict = {'ozone': np.random.random(), 'cell_temp': np.random.random(), 'cell_pressure': np.random.random(), 'photo_volt': np.random.random(),
        'power_supply': np.random.random(), 'latitude': np.random.random(), 'longitude': np.random.random(), 'altitude': np.random.random(), 'gps_quality': np.random.random(), 
        'datetime': datetime.now().strftime("%m/%d/%Y-%H:%M:%S")}
                                                
        return data_dict     
                       
if __name__ == '__main__':
    pom = POM(pom_name="POM",
              pom_port="/dev/ttyACM0",
              pom_location="drone")
    if not pom.init_pom() == OK:
        sys.exit()
    
    while True:
        data = pom.request_data()
        print(data)
        time.sleep(0.01)