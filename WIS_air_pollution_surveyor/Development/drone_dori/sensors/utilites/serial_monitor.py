import serial
import time
import argparse



parser = argparse.ArgumentParser()
parser.add_argument("port", help="Device port")
parser.add_argument("baudrate", help="Baudrate", type=int)
parser.add_argument("--time", help="Seconds between prints", type=float)


args = parser.parse_args()

try:
    ser = serial.Serial(args.port, args.baudrate);
    while True: 
        line = ser.readline().strip().decode('utf8')
        # print("*" * 20 + str("latitude" in line) + "*"*20)
        print(time.ctime(time.time()) + ": " + line )
        if (args.time):
            time.sleep(args.time)
except Exception as e:
    print(e)
    if (ser):
        ser.close()

print("Monitor closed")