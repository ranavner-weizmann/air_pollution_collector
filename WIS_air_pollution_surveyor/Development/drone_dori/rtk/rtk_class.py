import logging
import serial
import time
import sys
from ublox_gps import UbloxGps



import epics


# NAMING VARIABLES
rtkNAME = "rtk"
rtkPORT = "/dev/rtk"
LOCATION = "rtk"
wait = 100e-06
OK = 0
parameter_list = ['ozone','cell_temp','cell_pressure','photo_volt','power_supply'
,'latitude','longitude','altitude','gps_quality','datetime']    

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class Error(Exception):
    '''
    Base class for other exceptions
    '''
    pass

class NoNewDataRecieved(Error):
 
    pass

class FailedCommunication(Error):
    '''
    failed communication exception
    '''
    pass
    
class RTK():
    '''
    The following methods are the actual interface:
    init_rtk()
    '''
    def __init__(self,
                 rtk_name="RTK",
                 rtk_port="/dev/rtk",
                 rtk_location="some_location"):
        self.rtkNAME = rtk_name
        self.rtkPORT = rtk_port
        self.LOCATION = rtk_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10
        time.sleep(0.5)
        comm_status = self.init_rtk()
        if comm_status != OK:
            sys.exit
                           
        logging.info("Instantiated rtk class on port " + self.rtkPORT)
        # super().__init__()

    def init_rtk(self):
   
        port = serial.Serial('/dev/rtk', baudrate=38400, timeout=1)
        self.gps = UbloxGps(port)

    def close(self):
        '''
        closing the the rtk serial port
        '''
        logging.info('closing serial port ' + self.rtkPORT)
        self.ser.close()
   
    def request_data(self):

        dyn = self.gps.vehicle_dynamics()
        # time.sleep(0.1)
        
        yAcc = dyn.yAccel
        xAcc = dyn.xAccel
        zAcc = dyn.zAccel
        xAng = dyn.xAngRate
        yAng = dyn.yAngRate   
        zAng = dyn.zAngRate

        # time.sleep(0.1)
        geo = self.gps.geo_coords()
        # time.sleep(0.1)

        longitude = geo.lon
        latitude = geo.lat
        height_elips = geo.height
        height_sea = geo.hMSL
        velN = geo.velN
        velE = geo.velE
        velD = geo.velD
        head = geo.headMot
        numSV = geo.numSV

        # gspeed = geo.gSpeed
    
        # time.sleep(0.1)
        veh = self.gps.veh_attitude()

        roll = veh.roll
        pitch = veh.pitch
        heading = veh.heading
        accRoll = veh.accRoll
        accPitch = veh.accPitch
        accHeading = veh.accHeading
        # time.sleep(0.1)

        data = {'xAcc':xAcc, 'yAcc' : yAcc, 'zAcc':zAcc, 'xAng':xAng, 'yAng':yAng, 'zAng':zAng, 'longitude':longitude, 'latitude':latitude,
        'height_elips':height_elips, 'height_sea':height_sea, 'velN':velN, 'velE':velE, 'velD':velD, 'head':head, 'numSV':numSV, 
        'roll':roll, 'pitch':pitch, 'heading':heading, 'accRoll':accRoll, 'accPitch':accPitch, 'accHeading':accHeading }

        return data   
                       
if __name__ == '__main__':
    rtk = RTK(rtk_name="RTK",
              rtk_port="/dev/rtk",
              rtk_location="drone")
    
    while True:
        data = rtk.request_data()
        print(data)
        time.sleep(0.01)