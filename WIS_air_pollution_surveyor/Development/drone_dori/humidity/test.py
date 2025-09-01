import serial
import sys

serial_opts = {
            "port": '/dev/ttyACM0',
            "baudrate": 19200,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 10
        }

ser = serial.Serial(**serial_opts)
ser.isOpen()

while True:
    line = ser.readline()
    decoded = line.decode('utf-8')
    decoded_list = decoded.split(',')
    print(decoded)
    print('alright')



