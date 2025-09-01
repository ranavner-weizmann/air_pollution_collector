import socket 
import logging
import time
import sys

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class POPS():
    
    def __init__(self):

        self.localIP = "0.0.0.0"
        self.localPort = 10080
        self.bufferSize = 4096

        self.pops_dict = {'DateTime': '', 'TimeSSM': '', 'Status': '', 'DataStatus': '', 'PartCt': '', 'HistSum': '',
            'PartCon': '', 'BL': '', 'BLTH': '', 'STD' : '', 'MaxSTD': '', 'P': '', 'TofP': '', 
            'PumpLife_hrs': '', 'WidthSTD': '', 'AveWidth': '', 'POPS_Flow': '', 'PumpFB': '',
            'LDTemp': '', 'LaserFB': '', 'LD_Mon': '', 'Temp': '', 'BatV': '', 'Laser_Curent': '',
            'Flow_Set': '', 'BL_Start': '', 'TH_Mult': '','nbins': '', 'logmin': '', 'logmax': '', 'Skip_Save': '',
            'MinPeakPts': '', 'MaxPeakPts': '', 'RawPts': '', 'b0': '', 'b1': '', 'b2': '', 'b3': '', 'b4': '',
            'b5': '', 'b6': '', 'b7': '', 'b8': '', 'b9': '', 'b10': '', 'b11': '', 'b12': '', 'b13': '', 'b14': '',
            'b15': ''}



        # Create a datagram socket
        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        # Bind to address and ip
        self.UDPServerSocket.bind((self.localIP, self.localPort))
        logging.info("UDP server up and listening")

    def request_data(self):

        try:
            bytesAddressPair = self.UDPServerSocket.recvfrom(self.bufferSize)
            message = bytesAddressPair[0]
            address = bytesAddressPair[1]
            clientMsg = "Message from Client:{}".format(message)
            clientIP  = "Client IP Address:{}".format(address)
            # print(clientMsg)
            # print(clientIP)
            sliced_message = clientMsg[0:-5]
            message = sliced_message.split(',')
            data = message[3:]
            self.pops_dict['DateTime']=data[0]
            self.pops_dict['TimeSSM']=data[1]
            self.pops_dict['Status']=data[2]
            self.pops_dict['DataStatus']=data[3]
            self.pops_dict['PartCt']=data[4]
            self.pops_dict['HistSum']=data[5]
            self.pops_dict['PartCon']=data[6]
            self.pops_dict['BL']=data[7]
            self.pops_dict['BLTH']=data[8]
            self.pops_dict['STD']=data[9]
            self.pops_dict['MaxSTD']=data[10]
            self.pops_dict['P']=data[11]
            self.pops_dict['TofP']=data[12]
            self.pops_dict['PumpLife_hrs']=data[13]
            self.pops_dict['WidthSTD']=data[14]
            self.pops_dict['AveWidth']=data[15]
            self.pops_dict['POPS_Flow']=data[16]
            self.pops_dict['PumpFB']=data[17]
            self.pops_dict['LDTemp']=data[18]
            self.pops_dict['LaserFB']=data[19]
            self.pops_dict['LD_Mon']=data[20]
            self.pops_dict['Temp']=data[21]
            self.pops_dict['BatV']=data[22]
            self.pops_dict['Laser_Curent']=data[23]
            self.pops_dict['Flow_Set']=data[24]
            self.pops_dict['BL_Start']=data[25]
            self.pops_dict['TH_Mult']=data[26]
            self.pops_dict['nbins']=data[27]
            self.pops_dict['logmin']=data[28]
            self.pops_dict['logmax']=data[29]
            self.pops_dict['Skip_Save']=data[30]
            self.pops_dict['MinPeakPts']=data[31]
            self.pops_dict['MaxPeakPts']=data[32]
            self.pops_dict['RawPts']=data[33]
            self.pops_dict['b0']=data[34]
            self.pops_dict['b1']=data[35]
            self.pops_dict['b2']=data[36]
            self.pops_dict['b3']=data[37]
            self.pops_dict['b4']=data[38]
            self.pops_dict['b5']=data[39]
            self.pops_dict['b6']=data[40]
            self.pops_dict['b7']=data[41]
            self.pops_dict['b8']=data[42]
            self.pops_dict['b9']=data[43]
            self.pops_dict['b10']=data[44]
            self.pops_dict['b11']=data[45]
            self.pops_dict['b12']=data[46]
            self.pops_dict['b13']=data[47]
            self.pops_dict['b14']=data[48]
            self.pops_dict['b15']=data[49]

        except:
            logging.info("Error occured while trying to read data from POPS")

        return(self.pops_dict)

if __name__ == '__main__':

    pops = POPS()

    while True:
        data = pops.request_data()
        print(data)



        