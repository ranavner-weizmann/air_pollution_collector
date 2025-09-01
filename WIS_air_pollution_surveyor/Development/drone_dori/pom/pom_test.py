# from errno import EINPROGRESS

import serial
import pandas as pd
from datetime import datetime



# sec = pd.Timestamp(datetime.now())  

# abc = datetime.now()
# new = pd.Timestamp(abc)

now1 = datetime.now().strftime("%m/%d/%Y-%H:%M:%S")


a = b'742.3,304.8,741.1,0.7801,12.3,0000.00000,00000.00000,0.0,0,06/04/22,06:30:40\r\n'
decode_line = a.decode('utf-8').replace('\r\n','')
# new = decode_line.replace('\r\n','')
decode_list = decode_line.split(',')
decode_data = []
date_str = ''
for i in decode_list:
    try:
        decode_data.append(float(i))
    except:
        pass
combine_time = decode_list[9]+'-'+decode_list[10]                      # This line takes the time and date and 
timest = pd.Timestamp(combine_time)                                    # create timestamp.
decode_data.append(timest)


parameter_list = ['Ozone','Cell_Temperature','Cell_Pressure','Photodiode_Pressure','Power_Supply'
,'Latitude','Longitude','Atitude','GPS_Quality','DateTime']

data = {}
for i in range(10):
    data[parameter_list[i]] = decode_data[i]

# for num in range(decode_line):
#     pass


print('hello world')
# ser = serial.Serial(port='/dev/ttyACM0',baudrate=19200,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

# while True:
#     new_line = ser.readline()
#     print(new_line)
    