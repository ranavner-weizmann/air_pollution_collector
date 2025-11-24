import serial
import csv
import signal
import sys
import time
from datetime import datetime, timedelta
import pyudev
import logging

class RobustiMetReader:
    # iMet device identifiers - update these based on your iMet's actual IDs
    IDENTIFIERS = {
        "ID_VENDOR_ID": "067b",  # Prolific Technology, Inc. - common for USB-serial
        "ID_MODEL_ID": "23a3",   # USB-Serial Controller
        "ID_VENDOR": "Prolific Technology, Inc.",
        "ID_MODEL": "USB-Serial Controller"
    }
    
    PV_NAMES = [
        'pressure', 'temp', 'rel_hum', 'hum_temp', 'date', 'time', 
        'longitude', 'latitude', 'altitude', 'sat', 'Timestamp'
    ]

    def __init__(self):
        self.running = True
        self.serial = None
        self.port = None
        self.consecutive_failures = 0
        self.max_failures = 5
        self.reconnect_delay = 5  # Seconds between reconnection attempts
        self.last_successful_read = None
        self.health_check_interval = 30  # Check connection health every 30 seconds
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
                
            self.logger.warning("iMet device not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding iMet port: {e}")
            return None

    def init_serial(self):
        """Initialize serial connection to iMet with health check"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except:
                pass
            
        self.port = self.find_imet_port()
        if not self.port:
            self.logger.error("Cannot find iMet device")
            return False
            
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=57600,
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                rtscts=False,
                dsrdtr=False
            )
            
            self.serial.reset_input_buffer()
            time.sleep(2)  # Give device time to initialize
            
            # Test the connection by trying to read
            test_start = time.time()
            while time.time() - test_start < 3:  # Test for 3 seconds
                if self.serial.in_waiting > 0:
                    try:
                        line = self.serial.readline()
                        decoded = line.decode('utf-8').strip()
                        if decoded:
                            self.logger.info(f"Connection test successful: {decoded}")
                            break
                    except:
                        pass
                time.sleep(0.1)
            
            self.logger.info(f"Connected to iMet on {self.port}")
            self.consecutive_failures = 0
            self.last_successful_read = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.serial = None
            self.consecutive_failures += 1
            return False

    def read_imet_data(self):
        """Read data from iMet with connection health monitoring"""
        if not self.serial or not self.serial.is_open:
            if not self.init_serial():
                return None

        try:
            # Check if device is still present in system
            if not self.is_device_still_present():
                self.logger.warning("Device disappeared from system!")
                self.serial = None
                self.consecutive_failures += 1
                return None

            if self.serial.in_waiting > 0:
                line = self.serial.readline()
                decoded = line.decode('utf-8').strip()
                
                if not decoded:
                    return None
                
                self.logger.info(f"Raw data: {decoded}")
                self.last_successful_read = time.time()
                return decoded
            else:
                # Check if we haven't received data for too long (possible hang)
                if (self.last_successful_read and 
                    time.time() - self.last_successful_read > self.health_check_interval):
                    self.logger.warning("No data received for extended period, checking connection...")
                    # Try to write a harmless command or reset buffer
                    try:
                        self.serial.reset_input_buffer()
                        self.serial.reset_output_buffer()
                    except:
                        self.logger.warning("Buffer reset failed, reinitializing...")
                        self.serial = None
                        self.consecutive_failures += 1
                return None
                
        except serial.SerialException as e:
            self.logger.error(f"Serial error (disconnection?): {e}")
            self.serial = None
            self.consecutive_failures += 1
            return None
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            self.consecutive_failures += 1
            return None

    def parse_imet_data(self, data):
        """Parse iMet data string into structured format with data processing"""
        if not data:
            return None
            
        try:
            data_list = data.split(',')[1:]  # Remove first empty element
            
            if len(data_list) == len(self.PV_NAMES) - 1:  # -1 because we'll add timestamp
                # Process temperature values (divide by 100)
                try:
                    data_list[1] = str(float(data_list[1]) / 100)  # temp
                    data_list[3] = str(float(data_list[3]) / 100)  # hum_temp
                except (ValueError, IndexError) as e:
                    self.logger.error(f"Error processing temperature values: {e}")
                    return None
                
                # Adjust time by adding 2 hours
                try:
                    time_str = data_list[5]
                    time_obj = datetime.strptime(time_str, "%H:%M:%S")
                    adjusted_time = time_obj + timedelta(hours=2)
                    data_list[5] = adjusted_time.strftime("%H:%M:%S")
                except (ValueError, IndexError) as e:
                    self.logger.error(f"Error processing time: {e}")
                    # Continue without time adjustment
                
                # Add timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_list.append(current_time)
                
                return data_list
            else:
                self.logger.warning(f"Unexpected data format: {len(data_list)} fields, expected {len(self.PV_NAMES)-1}")
                return None
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None

    def run(self):
        """Main data collection loop with enhanced reconnection"""
        self.logger.info("Starting robust iMet data collection")
        
        with open('output/iMet_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.PV_NAMES)
            
            if not self.init_serial():
                self.logger.error("Failed initial connection. Will retry...")

            last_reconnect_attempt = 0
            
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Attempt reconnection if needed
                    if (self.serial is None and 
                        current_time - last_reconnect_attempt >= self.reconnect_delay):
                        self.logger.info("Attempting to reconnect...")
                        if self.init_serial():
                            self.logger.info("Reconnection successful!")
                        else:
                            self.logger.warning("Reconnection failed")
                        last_reconnect_attempt = current_time

                    # Only try to read if we have an active connection
                    if self.serial and self.serial.is_open:
                        raw_data = self.read_imet_data()
                        
                        if raw_data:
                            parsed_data = self.parse_imet_data(raw_data)
                            
                            if parsed_data:
                                writer.writerow(parsed_data)
                                csvfile.flush()
                                self.logger.info(f"Written: Pressure: {parsed_data[0]} hPa, Temp: {parsed_data[1]} °C")
                                self.consecutive_failures = 0

                    # Handle multiple failures
                    if self.consecutive_failures >= self.max_failures:
                        self.logger.warning(f"Multiple failures, will attempt reconnection in {self.reconnect_delay}s")
                        self.serial = None
                        self.consecutive_failures = 0
                        last_reconnect_attempt = current_time
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.consecutive_failures += 1
                    time.sleep(1)
        
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.logger.info("iMet data collection stopped")

def main():
    try:
        import pyudev
    except ImportError:
        print("ERROR: pyudev not installed. Install with: pip install pyudev")
        sys.exit(1)
    
    reader = RobustiMetReader()
    reader.run()

if __name__ == "__main__":
    main()