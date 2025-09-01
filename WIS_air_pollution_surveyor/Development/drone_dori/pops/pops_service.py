import time
import logging
import numpy as np
import epics
from pops_class import POPS

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

def insert_data_into_epics(data):

    if isinstance(data,dict):
        try:
            # pops_dev_epics.DateTime = data['DateTime']
            pops_dev_epics.TimeSSM = data['TimeSSM']
            pops_dev_epics.Status = data['Status']
            pops_dev_epics.DataStatus = data['DataStatus']
            pops_dev_epics.PartCt = data['PartCt']
            pops_dev_epics.HistSum = data['HistSum']
            pops_dev_epics.BL = data['BL']
            pops_dev_epics.BLTH = data['BLTH']
            pops_dev_epics.STD = data['STD']
            pops_dev_epics.P = data['P']
            pops_dev_epics.TofP = data['TofP']
            pops_dev_epics.PumpLife_hrs = data['PumpLife_hrs']
            pops_dev_epics.WidthSTD = data['WidthSTD']
            pops_dev_epics.AveWidth = data['AveWidth']
            pops_dev_epics.POPS_Flow= data['POPS_Flow']
            # pops_dev_epics.PumpFB = data['PumpFB'] 
            pops_dev_epics.LDTemp = data['LDTemp']
            pops_dev_epics.LaserFB = data['LaserFB']
            pops_dev_epics.LD_Mon = data['LD_Mon']
            pops_dev_epics.Temp = data['Temp']
            pops_dev_epics.BatV = data['BatV']
            # pops_dev_epics.Laser_Curent = data['Laser_Curent']
            # pops_dev_epics.Flow_Set = data['Flow_Set']
            pops_dev_epics.BL_Start = data['BL_Start']
            pops_dev_epics.TH_Mult = data['TH_Mult']
            pops_dev_epics.nbins = data['nbins']
            pops_dev_epics.logmin = data['logmin']
            pops_dev_epics.logmax = data['logmax']
            # pops_dev_epics.Skip_Save = data['Skip_Save']
            pops_dev_epics.MinPeakPts = data['MinPeakPts']
            pops_dev_epics.MaxPeakPts = data['MaxPeakPts'] 
            pops_dev_epics.RawPts = data['RawPts'] 
            pops_dev_epics.b0 = data['b0'] 
            pops_dev_epics.b1 = data['b1']
            pops_dev_epics.b2 = data['b2'] 
            pops_dev_epics.b3 = data['b3'] 
            pops_dev_epics.b4 = data['b4'] 
            pops_dev_epics.b5 = data['b5'] 
            pops_dev_epics.b6 = data['b6'] 
            pops_dev_epics.b7 = data['b7'] 
            pops_dev_epics.b8 = data['b8'] 
            pops_dev_epics.b9 = data['b9'] 
            pops_dev_epics.b10 = data['b10'] 
            pops_dev_epics.b11 = data['b11'] 
            pops_dev_epics.b12 = data['b12'] 
            pops_dev_epics.b13 = data['b13'] 
            pops_dev_epics.b14 = data['b14'] 
            pops_dev_epics.b15 = data['b15'] 

        except KeyError as e:
            print(e)
            logging.error('one of the keys of dictionary is not correct, probably due to bad communication data string')


if __name__ == '__main__':

    while True:
        try:
            pops = POPS()
            while True:     #maybe have some connection flag?
                try:
                    pops_dev_epics = epics.Device('pops:')
                    if pops_dev_epics.enable == 0:
                        logging.info('"enable" if off, change it to on')    
                        time.sleep(3)
                        continue
                    else:
                        while True:
                            data = pops.request_data()
                            insert_data_into_epics(data)
                            logging.info('data inserted into EPICS')   
                            print(data)                    
                except:
                    logging.error("epics variable wasn't created. check softIoc")            
        except KeyError as e:
            logging.error("Check the physical connections")
            print(e)







    

