import logging
import serial
import time
import sys


# NAMING VARIABLES
POMNAME = "POM"
POMPORT = "/dev/ttyACM0"
LOCATION = "Pom"
wait = 100e-06
OK = 0
time_delay = 6
parameter_list = ['ozone','cell_temp','cell_pressure','photo_volt','power_supply'
,'latitude','longitude','altitude','gps_quality']    

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
    
class POM():
    '''
    The following methods are the actual interface:
    init_pom()
    '''
    def __init__(self,
                 pom_name="POM",
                 pom_port="/dev/pom",
                 pom_location="some_location"):
        self.POMNAME = pom_name
        self.POMPORT = pom_port
        self.LOCATION = pom_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        time.sleep(0.5)
        comm_status = self.init_pom()
        if comm_status != OK:
            sys.exit
                           
        logging.info("Instantiated POM class on port " + self.POMPORT)
        # super().__init__()

    def init_pom(self):
        '''
        establish communication with POM return OK if succedded and -1 if failed
        '''
        serial_opts = {
            "port": self.POMPORT,
            "baudrate": 19200,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 60
        }

        logging.info('openning serial port to POM ' + self.POMPORT)
        logging.info('initializing communication with POM')
        self.ser = serial.Serial(**serial_opts)
        return OK

    def close(self):
        '''
        closing the the POM serial port
        '''
        logging.info('closing serial port ' + self.POMPORT)
        self.ser.close()
   
    def request_data(self):

        data_dict = {}
        new_line = self.ser.readline()
        if len(new_line)==0:
            time.sleep(0.1)
            return

        decode_line = new_line.decode('utf-8').replace('\r\n','')
        if '\x00' in decode_line:                                              # in case that there is a null character.   
            decode_line = decode_line.replace('\x00','')
        decode_list = decode_line.split(',')
        decode_data = []

        for i in decode_list:
            try:
                decode_data.append(float(i))
            except:
                break

        try:
            for i in range(10):
                data_dict[parameter_list[i]] = decode_data[i]
        except:
            pass
        
        return data_dict    
                       
if __name__ == '__main__':
    pom = POM(pom_name="POM",
              pom_port="/dev/pom",
              pom_location="drone")
    
    while True:
        data = pom.request_data()
        print(data)
        time.sleep(time_delay)