import serial
import csv
import signal
import sys
from datetime import datetime, timedelta

headers = ['pressure', 'temp', 'rel_hum', 'hum_temp', 'date', 'time', 'longitude', 'latitude', 'altitude', 'sat']


running = True

def signal_handler(sig, frame):
    global running
    print("\nStopping...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

with open('output/iMet_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    
    ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=1)
    
    ser.reset_input_buffer()
    
    try:
        while running:
            if ser.in_waiting > 0:
                line = ser.readline()
                decoded = line.decode('utf-8').strip()
                print(decoded)
                
                data_list = decoded.split(',')[1:]
                
                if len(data_list) == len(headers):
                    data_list[1] = str(float(data_list[1]) / 100)
                    data_list[3] = str(float(data_list[3]) / 100)
                    
                    time_str = data_list[5]
                    time_obj = datetime.strptime(time_str, "%H:%M:%S")
                    adjusted_time = time_obj + timedelta(hours=2)
                    data_list[5] = adjusted_time.strftime("%H:%M:%S")
                    
                    writer.writerow(data_list)
                    csvfile.flush()
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()
        print("Serial connection closed.")