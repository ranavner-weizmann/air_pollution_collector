import serial
import csv
import signal
import sys
import time
from datetime import datetime

# CSV headers based on POM data format
headers = [
    'Log_Number',           # Log number (if present)
    'Ozone_ppb',           # Ozone concentration (ppb)
    'Cell_Temperature_K',   # Cell temperature (K)
    'Cell_Pressure_torr',   # Cell pressure (torr)
    'Photodiode_Voltage_V', # Photodiode voltage (V)
    'Power_Supply_V',       # Power supply voltage (V)
    'Latitude',             # Latitude
    'Longitude',            # Longitude
    'Altitude_m',           # Altitude (meters)
    'GPS_Quality',          # GPS quality indicator
    'Date',                 # Date (DD/MM/YY)
    'Time',                 # Time (HH:MM:SS)
    'Timestamp'             # Merged timestamp (YYYY-MM-DD HH:MM:SS)
]

# Global variable to control the main loop
running = True

def signal_handler(sig, frame):
    global running
    print("\nStopping POM data collection...")
    running = False

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Open CSV file for writing
with open('pom_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    
    # Configure serial connection for POM - USE ttyACM0
    ser = serial.Serial(
        port='/dev/ttyACM0',  # This is the correct port!
        baudrate=19200,       # POM specific baud rate
        parity=serial.PARITY_NONE,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
        # For ACM devices, we might need to disable flow control
        rtscts=False,
        dsrdtr=False
    )
    
    # Clear any existing data in the serial buffer
    ser.reset_input_buffer()
    print("Starting Personal Ozone Monitor data collection. Press Ctrl+C to stop.")
    print(f"Connected to {ser.port} at {ser.baudrate} baud")
    print("Waiting for POM data...")
    
    # Skip initial header lines from POM
    header_lines_skipped = 0
    max_header_lines = 10
    
    try:
        while running:
            if ser.in_waiting > 0:
                line = ser.readline()
                try:
                    decoded = line.decode('utf-8').strip()
                    
                    # Skip header lines and empty lines
                    if not decoded or "Personal Ozone Monitor" in decoded or decoded.isdigit():
                        header_lines_skipped += 1
                        if header_lines_skipped <= max_header_lines:
                            print(f"Skipping header line: {decoded}")
                        continue
                    
                    print(f"POM Data: {decoded}")
                    
                    # Parse the comma-separated data
                    data_list = decoded.split(',')
                    
                    # Handle both real-time and logged data formats
                    if len(data_list) == 11:
                        # Real-time data (no log number) - add empty log number
                        data_list = [''] + data_list
                    elif len(data_list) == 12:
                        # Logged data (with log number) - already correct format
                        pass
                    else:
                        print(f"Unexpected data format: {len(data_list)} fields")
                        continue
                    
                    # Add current timestamp for merging
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_list.append(current_time)
                    
                    # Write to CSV
                    writer.writerow(data_list)
                    csvfile.flush()  # Ensure data is written immediately
                    
                    print(f"Written: Ozone: {data_list[1]} ppb, Temp: {data_list[2]} K")
                        
                except UnicodeDecodeError:
                    print("Warning: Could not decode line from POM")
                except Exception as e:
                    print(f"Error processing POM data: {e}")
                
            time.sleep(0.1)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Properly close the serial connection
        if ser and ser.is_open:
            ser.close()
        print("Serial connection closed.")
        print("POM data saved to pom_data.csv")