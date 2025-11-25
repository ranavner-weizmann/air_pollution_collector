# iMet_safe.py - Fixed Version
import csv
import signal
import sys
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

try:
    import serial
    # Check if serial has __version__ attribute
    if hasattr(serial, '__version__'):
        print(f"Using py-serial version: {serial.__version__}")
    else:
        print("Using py-serial (version attribute not available)")
except ImportError:
    print("ERROR: pyserial not installed. Install with: pip install pyserial")
    sys.exit(1)

try:
    import pyudev
except ImportError:
    print("ERROR: pyudev not installed. Install with: pip install pyudev")
    sys.exit(1)

class RobustiMetReader:
    # iMet device identifiers - updated for FTDI chip
    IDENTIFIERS = {
        "ID_VENDOR_ID": "0403",  # FTDI
        "ID_MODEL_ID": "6015",   # FT230X Basic UART
        "ID_VENDOR": "FTDI",
        "ID_MODEL": "FT230X_Basic_UART"
    }
    
    PV_NAMES = [
        'pressure', 'temp', 'rel_hum', 'hum_temp', 'date', 'time', 
        'longitude', 'latitude', 'altitude', 'sat', 'Timestamp'
    ]

    def __init__(self):
        self.running = True
        self.serial_conn = None
        self.port = None
        self.consecutive_failures = 0
        self.max_failures = 5
        self.reconnect_delay = 5
        self.last_successful_read = None
        self.health_check_interval = 30
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        """Setup logging"""
        formatter = logging.Formatter(fmt=f"%(asctime)s iMet: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger = logging.getLogger('iMet')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.logger.info("Stopping iMet data collection...")
        self.running = False

    def is_device_still_present(self):
        """Check if the device is still connected to the system"""
        try:
            context = pyudev.Context()
            for device in context.list_devices(subsystem='tty'):
                vendor_id = device.get('ID_VENDOR_ID')
                model_id = device.get('ID_MODEL_ID')
                if (vendor_id == self.IDENTIFIERS["ID_VENDOR_ID"] and 
                    model_id == self.IDENTIFIERS["ID_MODEL_ID"]):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking device presence: {e}")
            return False

    def find_imet_port(self):
        """Find iMet port using device identifiers"""
        try:
            self.logger.info("Searching for iMet device...")
            context = pyudev.Context()
            
            for device in context.list_devices(subsystem='tty'):
                vendor_id = device.get('ID_VENDOR_ID')
                model_id = device.get('ID_MODEL_ID')
                vendor = device.get('ID_VENDOR')
                model = device.get('ID_MODEL')
                
                matches_vendor_id = vendor_id == self.IDENTIFIERS["ID_VENDOR_ID"]
                matches_model_id = model_id == self.IDENTIFIERS["ID_MODEL_ID"]
                
                if matches_vendor_id and matches_model_id:
                    port = device.device_node
                    self.logger.info(f"Found iMet at port: {port}")
                    self.logger.info(f"Device info: {vendor} - {model}")
                    return port
            
            # If not found by exact match, try to find any FTDI device
            self.logger.info("Trying to find any FTDI device...")
            for device in context.list_devices(subsystem='tty'):
                vendor_id = device.get('ID_VENDOR_ID')
                if vendor_id == "0403":  # FTDI
                    port = device.device_node
                    self.logger.info(f"Found FTDI device at port: {port}")
                    return port
                
            self.logger.warning("iMet device not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding iMet port: {e}")
            return None

    def init_serial(self):
        """Initialize serial connection to iMet with health check"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except:
                pass
            
        self.port = self.find_imet_port()
        if not self.port:
            self.logger.error("Cannot find iMet device")
            return False
            
        try:
            self.logger.info(f"Attempting to connect to {self.port}...")
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=57600,
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,  # Increased timeout
                rtscts=False,
                dsrdtr=False,
                xonxoff=False
            )
            
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            time.sleep(3)  # Give device more time to initialize
            
            self.logger.info(f"Connected to iMet on {self.port}")
            self.consecutive_failures = 0
            self.last_successful_read = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.serial_conn = None
            self.consecutive_failures += 1
            return False

    def read_imet_data(self):
        """Read data from iMet with connection health monitoring"""
        if not self.serial_conn or not self.serial_conn.is_open:
            if not self.init_serial():
                return None

        try:
            # Check if device is still present in system
            if not self.is_device_still_present():
                self.logger.warning("Device disappeared from system!")
                self.serial_conn = None
                self.consecutive_failures += 1
                return None

            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline()
                try:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                except Exception as e:
                    self.logger.warning(f"Decode error: {e}")
                    return None
                
                if not decoded:
                    return None
                
                self.logger.info(f"Raw data: {decoded}")
                self.last_successful_read = time.time()
                return decoded
            else:
                # Check if we haven't received data for too long
                if (self.last_successful_read and 
                    time.time() - self.last_successful_read > self.health_check_interval):
                    self.logger.warning("No data received for extended period, checking connection...")
                    try:
                        self.serial_conn.reset_input_buffer()
                        # Try to send a harmless command or newline to wake device
                        self.serial_conn.write(b'\r\n')
                    except:
                        self.logger.warning("Buffer reset failed, reinitializing...")
                        self.serial_conn = None
                        self.consecutive_failures += 1
                return None
                
        except serial.SerialException as e:
            self.logger.error(f"Serial error: {e}")
            self.serial_conn = None
            self.consecutive_failures += 1
            return None
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            self.consecutive_failures += 1
            return None

    def parse_imet_data(self, data):
        """Parse iMet data string into structured format"""
        if not data:
            return None
            
        try:
            # Clean the data and split
            data = data.strip()
            # Remove any non-ASCII characters
            data = ''.join(char for char in data if ord(char) < 128)
            
            if data.startswith(','):
                data = data[1:]  # Remove leading comma if present
                
            data_list = data.split(',')
            
            # Expected format should have 10 fields + timestamp = 11 total
            if len(data_list) >= 10:  # At least 10 fields
                # Fill missing fields with empty strings
                while len(data_list) < 10:
                    data_list.append('')
                
                # Process temperature values (divide by 100)
                try:
                    if data_list[1]:  # temp
                        data_list[1] = str(float(data_list[1]) / 100)
                    if data_list[3] and len(data_list) > 3:  # hum_temp
                        data_list[3] = str(float(data_list[3]) / 100)
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error processing temperature values: {e}")
                
                # Adjust time by adding 2 hours if time field exists and is valid
                try:
                    if (data_list[5] and ':' in data_list[5] and 
                        len(data_list[5].split(':')) == 3):  # time (HH:MM:SS)
                        time_str = data_list[5]
                        time_obj = datetime.strptime(time_str, "%H:%M:%S")
                        adjusted_time = time_obj + timedelta(hours=2)
                        data_list[5] = adjusted_time.strftime("%H:%M:%S")
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error processing time: {e}")
                
                # Add timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_list.append(current_time)
                
                return data_list
            else:
                self.logger.warning(f"Unexpected data format: {len(data_list)} fields, data: {data}")
                return None
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}, data: {data}")
            return None

    def run(self):
        """Main data collection loop"""
        self.logger.info("Starting robust iMet data collection")
        
        # Ensure output directory exists
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Create output file with headers immediately
        output_file = 'output/iMet_data.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.PV_NAMES)
            csvfile.flush()
        
        self.logger.info(f"Output file created: {output_file}")
        
        if not self.init_serial():
            self.logger.error("Failed initial connection. Will retry...")

        last_reconnect_attempt = 0
        last_placeholder_time = 0
        
        with open(output_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Attempt reconnection if needed
                    if (self.serial_conn is None and 
                        current_time - last_reconnect_attempt >= self.reconnect_delay):
                        self.logger.info("Attempting to reconnect...")
                        if self.init_serial():
                            self.logger.info("Reconnection successful!")
                        else:
                            self.logger.warning("Reconnection failed")
                        last_reconnect_attempt = current_time

                    # Only try to read if we have an active connection
                    if self.serial_conn and self.serial_conn.is_open:
                        raw_data = self.read_imet_data()
                        
                        if raw_data:
                            parsed_data = self.parse_imet_data(raw_data)
                            
                            if parsed_data:
                                writer.writerow(parsed_data)
                                csvfile.flush()
                                self.logger.info(f"Written: Pressure: {parsed_data[0]} hPa, Temp: {parsed_data[1]} °C")
                                self.consecutive_failures = 0
                        
                        # Write placeholder every 30 seconds if no data
                        if current_time - last_placeholder_time >= 30:
                            placeholder = [''] * (len(self.PV_NAMES) - 1) + [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                            writer.writerow(placeholder)
                            csvfile.flush()
                            self.logger.debug("No data received, wrote placeholder")
                            last_placeholder_time = current_time

                    # Handle multiple failures
                    if self.consecutive_failures >= self.max_failures:
                        self.logger.warning(f"Multiple failures, will attempt reconnection in {self.reconnect_delay}s")
                        self.serial_conn = None
                        self.consecutive_failures = 0
                        last_reconnect_attempt = current_time
                    
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.consecutive_failures += 1
                    time.sleep(2)
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.logger.info("iMet data collection stopped")

def main():
    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    print("Starting iMet data collection...")
    reader = RobustiMetReader()
    reader.run()

if __name__ == "__main__":
    main()