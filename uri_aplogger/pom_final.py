import serial
import csv
import signal
import sys
import time
from datetime import datetime
import pyudev
import logging

class RobustPOMReader:
    # POM device identifiers for Prolific USB-Serial adapter
    IDENTIFIERS = {
        "ID_VENDOR_ID": "067b",
        "ID_MODEL_ID": "23a3", 
        "ID_VENDOR": "Prolific Technology, Inc.",
        "ID_MODEL": "USB-Serial Controller"
    }
    
    PV_NAMES = [
        'Log_Number', 'Ozone_ppb', 'Cell_Temperature_K', 'Cell_Pressure_torr',
        'Photodiode_Voltage_V', 'Power_Supply_V', 'Latitude', 'Longitude',
        'Altitude_m', 'GPS_Quality', 'Date', 'Time', 'Timestamp'
    ]

    def __init__(self):
        self.running = True
        self.serial = None
        self.port = None
        self.consecutive_failures = 0
        self.max_failures = 10  # Increased failure threshold
        self.header_lines_skipped = 0
        self.max_header_lines = 10
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        """Setup logging similar to your original sensor class"""
        formatter = logging.Formatter(fmt=f"%(asctime)s POM: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('POM')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.logger.info("Stopping POM data collection...")
        self.running = False

    def find_pom_port(self):
        """Find POM port using device identifiers"""
        try:
            self.logger.info("Searching for POM device (Prolific USB-Serial adapter)...")
            context = pyudev.Context()
            
            for device in context.list_devices(subsystem='tty'):
                # Check if this device matches our POM identifiers
                vendor_id = device.get('ID_VENDOR_ID')
                model_id = device.get('ID_MODEL_ID')
                vendor = device.get('ID_VENDOR')
                model = device.get('ID_MODEL')
                
                # Match against our identifiers
                matches_vendor_id = vendor_id == self.IDENTIFIERS["ID_VENDOR_ID"]
                matches_model_id = model_id == self.IDENTIFIERS["ID_MODEL_ID"]
                
                if matches_vendor_id and matches_model_id:
                    port = device.device_node
                    self.logger.info(f"Found POM at port: {port}")
                    self.logger.info(f"Device info: {vendor} - {model}")
                    return port
                
            self.logger.warning("POM device not found in device list")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding POM port: {e}")
            return None

    def init_serial(self):
        """Initialize serial connection to POM"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            
        self.port = self.find_pom_port()
        if not self.port:
            self.logger.error("Cannot find POM device")
            return False
            
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=19200,
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                rtscts=False,
                dsrdtr=False
            )
            
            self.serial.reset_input_buffer()
            # Give the device time to initialize
            time.sleep(2)
            self.logger.info(f"Connected to POM on {self.port}")
            self.consecutive_failures = 0  # Reset failures on successful connection
            self.header_lines_skipped = 0  # Reset header skipping
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.serial = None
            self.consecutive_failures += 1
            return False

    def read_pom_data(self):
        """Read and parse data from POM"""
        if not self.serial or not self.serial.is_open:
            if not self.init_serial():
                return None

        try:
            if self.serial.in_waiting > 0:
                line = self.serial.readline()
                decoded = line.decode('utf-8').strip()
                
                # Skip header lines and empty data
                if not decoded:
                    return None
                    
                if "Personal Ozone Monitor" in decoded or decoded.isdigit():
                    self.header_lines_skipped += 1
                    if self.header_lines_skipped <= self.max_header_lines:
                        self.logger.info(f"Skipping header: {decoded}")
                    return None
                
                self.logger.info(f"Raw data: {decoded}")
                return decoded
            else:
                # No data available is normal, not a failure
                return None
                
        except serial.SerialException as e:
            self.logger.error(f"Serial error: {e}")
            self.serial = None
            self.consecutive_failures += 1
            return None
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            self.consecutive_failures += 1
            return None

    def parse_pom_data(self, data):
        """Parse POM data string into structured format"""
        if not data:
            return None
            
        try:
            data_list = data.split(',')
            
            # Handle both data formats
            if len(data_list) == 11:
                data_list = [''] + data_list  # Add empty log number for real-time data
            elif len(data_list) == 12:
                pass  # Logged data already has log number
            else:
                self.logger.warning(f"Unexpected data format: {len(data_list)} fields")
                return None
            
            # Add timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_list.append(current_time)
            
            return data_list
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None

    def run(self):
        """Main data collection loop"""
        self.logger.info("Starting robust POM data collection with Prolific adapter")
        
        # Initialize CSV file
        with open('output/pom_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.PV_NAMES)
            
            # Initialize serial connection
            if not self.init_serial():
                self.logger.error("Failed to initialize POM. Exiting.")
                return

            while self.running:
                try:
                    # Read data from POM
                    raw_data = self.read_pom_data()
                    
                    if raw_data:
                        parsed_data = self.parse_pom_data(raw_data)
                        
                        if parsed_data:
                            # Write to CSV
                            writer.writerow(parsed_data)
                            csvfile.flush()
                            
                            self.logger.info(f"Written: Ozone: {parsed_data[1]} ppb, Temp: {parsed_data[2]} K")
                            self.consecutive_failures = 0  # Reset failure counter
                        else:
                            # Parsing failure
                            self.consecutive_failures += 1
                    else:
                        # No data available - this is normal, don't count as failure
                        # Only count as failure if we haven't seen data for a while
                        if self.consecutive_failures > 0:
                            self.consecutive_failures += 1
                    
                    # If too many failures, try to reinitialize serial
                    if self.consecutive_failures >= self.max_failures:
                        self.logger.warning(f"Multiple failures ({self.consecutive_failures}), reinitializing serial...")
                        if not self.init_serial():
                            self.logger.error("Failed to reinitialize serial connection")
                        # Don't reset consecutive_failures here - let init_serial handle it
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.consecutive_failures += 1
                    time.sleep(1)
        
        # Cleanup
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.logger.info("POM data collection stopped")

def main():
    # Check if pyudev is available
    try:
        import pyudev
    except ImportError:
        print("ERROR: pyudev not installed. Install with: pip install pyudev")
        sys.exit(1)
    
    reader = RobustPOMReader()
    reader.run()

if __name__ == "__main__":
    main()