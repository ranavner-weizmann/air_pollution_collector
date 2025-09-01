



import serial
import time
from datetime import datetime
import argparse

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="Serial port")
    parser.add_argument("-i", '--interval', default=5, type=float, metavar="<seconds>")
    args = parser.parse_args()


    # Configure the serial port
    ser = serial.Serial(args.port, 9600)

    while True:
        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Send the time to the serial port
        ser.write(current_time.encode())

        # Wait for 5 seconds
        time.sleep(5)


if __name__ == "__main__":
    main()