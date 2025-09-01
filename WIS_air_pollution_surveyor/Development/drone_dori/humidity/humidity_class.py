import serial
import sys
import time
import logging
OK = 0

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class HUMIDITY():

    def __init__(self,
                 humidity_name="HUMIDITY",
                 humidity_port="/dev/hum",
                 humidity_location="some_location"):
        self.HUMNAME = humidity_name
        self.HUMPORT = humidity_port
        self.LOCATION = humidity_location
        time.sleep(0.5)
        comm_status = self.init_humidity()
        if comm_status != OK:
            sys.exit

    def init_humidity(self):

        serial_opts = {
            "port": self.HUMPORT,
            "baudrate": 57600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "timeout": 1
        }

        logging.info('openning serial port to HUMIDITY ' + self.HUMPORT)
        logging.info('initializing communication with HUMIDITY')
        self.ser = serial.Serial(**serial_opts)
        return OK

    def request_data(self):

        labels_list = ['pressure','temp','rel_hum',
        'hum_temp','Date and time','unknown','longitude','latitude','altitude','sat','k']
        data_dict = {}
        line = self.ser.readline()
        decoded = line.decode('utf-8')
        decoded_list = decoded.split(',')
        decoded_list.pop(0)
        for i in range(len(decoded_list)):
            try:
                data_dict[labels_list[i]]=float(decoded_list[i])
            except:
                pass

        return(data_dict)

if __name__ == '__main__':
    humidity = HUMIDITY(humidity_name="HUMIDITY",
              humidity_port="/dev/hum",
              humidity_location="drone")
    
    while True:
        data = humidity.request_data()
        print(data)
        time.sleep(0.01)