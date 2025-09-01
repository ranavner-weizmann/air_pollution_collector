"""
Pops sensor class
Programmers: Nitzan Yizhar and Lior Segev
Date 06/07/2023

"""
import socket 
from sensor import Sensor


class Pops(Sensor):
    IDENTIFIERS = ["BeagleBoard.org"]
    
    PV_NAMES = ['enable', 'DateTime', 'TimeSSM', 'Status', 'DataStatus', 'PartCt', 'HistSum', 'PartCon', 'BL', 'BLTH', 'STD', 'MaxSTD', 'P', 'TofP', 'PumpLife_hrs', 'WidthSTD', 'AveWidth', 'POPS_Flow',
                'Pump_FB', 'LDTemp', 'LaserFB', 'LD_Mon', 'Temp', 'BatV', 'LD_Mon', 'Flow_Set', 'BL_Start', 'TH_Mult', 'nbins',
                'logmin', 'logmax', 'Skip_save', 'MinPeakPts', 'MaxPeakPts', 'RawPts', 'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10', 'b11', 'b12', 'b13', 'b14', 'b15', 'bins']
    
    def __init__(self, name :str, location: str,
                demo_mode : bool, is_device : bool, device_name : str, sampling_time: int = 1):
        
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
        super().__init__(name=name, location=location, device_name=device_name, is_device=is_device, demo_mode=demo_mode, sampling_time=sampling_time)



    def measure_once(self):
        return self.request_data_inner()
    
    def init_sensor(self):
        if self.demo_mode:
            return Sensor.OK
        
        # Create a datagram socket
        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        # Bind to address and ip
        self.UDPServerSocket.bind((self.localIP, self.localPort))
        self.logger.info("UDP server up and listening")
        return Sensor.OK


    def request_data_inner(self):
        if self.demo_mode:
            return self.demo_data()

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
        self.pops_dict['DateTime']= Sensor.Nan
        self.pops_dict['enable']= Sensor.Nan
        self.pops_dict['Pump_FB']= Sensor.Nan
        self.pops_dict['Skip_save']= Sensor.Nan
        self.pops_dict['TimeSSM']=float(data[1])
        self.pops_dict['Status']=float(data[2])
        self.pops_dict['DataStatus']=float(data[3])
        self.pops_dict['PartCt']=float(data[4])
        self.pops_dict['HistSum']=float(data[5])
        self.pops_dict['PartCon']=float(data[6])
        self.pops_dict['BL']=float(data[7])
        self.pops_dict['BLTH']=float(data[8])
        self.pops_dict['STD']=float(data[9])
        self.pops_dict['MaxSTD']=float(data[10])
        self.pops_dict['P']=float(data[11])
        self.pops_dict['TofP']=float(data[12])
        self.pops_dict['PumpLife_hrs']=float(data[13])
        self.pops_dict['WidthSTD']=float(data[14])
        self.pops_dict['AveWidth']=float(data[15])
        self.pops_dict['POPS_Flow']=float(data[16])
        self.pops_dict['PumpFB']=float(data[17])
        self.pops_dict['LDTemp']=float(data[18])
        self.pops_dict['LaserFB']=float(data[19])
        self.pops_dict['LD_Mon']=float(data[20])
        self.pops_dict['Temp']=float(data[21])
        self.pops_dict['BatV']=float(data[22])
        self.pops_dict['Laser_Curent']=float(data[23])
        self.pops_dict['Flow_Set']=float(data[24])
        self.pops_dict['BL_Start']=float(data[25])
        self.pops_dict['TH_Mult']=float(data[26])
        self.pops_dict['nbins']=float(data[27])
        self.pops_dict['logmin']=float(data[28])
        self.pops_dict['logmax']=float(data[29])
        self.pops_dict['Skip_Save']=float(data[30])
        self.pops_dict['MinPeakPts']=float(data[31])
        self.pops_dict['MaxPeakPts']=float(data[32])
        self.pops_dict['RawPts']=float(data[33])
        self.pops_dict['b0']=float(data[34])
        self.pops_dict['b1']=float(data[35])
        self.pops_dict['b2']=float(data[36])
        self.pops_dict['b3']=float(data[37])
        self.pops_dict['b4']=float(data[38])
        self.pops_dict['b5']=float(data[39])
        self.pops_dict['b6']=float(data[40])
        self.pops_dict['b7']=float(data[41])
        self.pops_dict['b8']=float(data[42])
        self.pops_dict['b9']=float(data[43])
        self.pops_dict['b10']=float(data[44])
        self.pops_dict['b11']=float(data[45])
        self.pops_dict['b12']=float(data[46])
        self.pops_dict['b13']=float(data[47])
        self.pops_dict['b14']=float(data[48])
        self.pops_dict['b15']=float(data[49])
        self.pops_dict['bins'] = [self.pops_dict[f"b{i}"]  for i in range(16)]

        return(self.pops_dict)



        