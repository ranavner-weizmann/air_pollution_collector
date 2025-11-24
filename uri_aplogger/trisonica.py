import serial
import csv
import signal
import sys
import time
from datetime import datetime
import pyudev
import logging

class RobustTriSonicaReader:
    IDENTIFIERS = {
        "ID_VENDOR_ID": "10c4",
        "ID_MODEL_ID": "ea60",
        "ID_VENDOR": "Silicon Labs",
        "ID_MODEL": "CP210x UART Bridge"
    }
    
    PV_NAMES = [
        'Wind_Speed',        # (m/s)
        'Wind_Direction',    # (degrees)
        'U_Vector',          # (m/s)
        'V_Vector',          # (m/s)
        'W_Vector',          # (m/s)
        'Temperature',       # (degrees C)
        'Relative_Humidity', # (%)
        'Pressure',          # (kPa)
        'Compass_Heading',   # (degrees)
        'Pitch',             # (degrees)
        'Roll',              # (degrees)
        'Timestamp'          # (YYYY-MM-DD HH:MM:SS)
    ]

    def __init__(self):
        self.running = True
        self.serial = None
        self.port = None
        self.consecutive_failures = 0
        self.max_failures = 10
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        """Setup logging"""
        formatter = logging.Formatter(fmt=f"%(asctime)s TriSonica: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('TriSonica')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.logger.info("Stopping TriSonica data collection...")
        self.running = False

    def find_trisonica_port(self):
        """Find TriSonica port using device identifiers"""
        try:
            self.logger.info("Searching for TriSonica device...")
            context = pyudev.Context()
            
            for device in context.list_devices(subsystem='tty'):
                # Check if this device matches our identifiers
                vendor_id = device.get('ID_VENDOR_ID')
                model_id = device.get('ID_MODEL_ID')
                vendor = device.get('ID_VENDOR')
                model = device.get('ID_MODEL')
                
                # Debug: Print all devices for verification
                if vendor_id and model_id:
                    self.logger.debug(f"Found device: {device.device_node} - {vendor} - {model} ({vendor_id}:{model_id})")
                
                # Match against our identifiers
                matches_vendor_id = vendor_id == self.IDENTIFIERS["ID_VENDOR_ID"]
                matches_model_id = model_id == self.IDENTIFIERS["ID_MODEL_ID"]
                
                if matches_vendor_id and matches_model_id:
                    port = device.device_node
                    self.logger.info(f"Found TriSonica at port: {port}")
                    self.logger.info(f"Device info: {vendor} - {model}")
                    return port
                
            self.logger.warning("TriSonica device not found in device list")
            self.logger.warning("Available devices:")
            for device in context.list_devices(subsystem='tty'):
                vendor_id = device.get('ID_VENDOR_ID')
                model_id = device.get('ID_MODEL_ID')
                if vendor_id and model_id:
                    self.logger.warning(f"  {device.device_node}: {vendor_id}:{model_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding TriSonica port: {e}")
            return None

    def init_serial(self):
        """Initialize serial connection to TriSonica"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            
        self.port = self.find_trisonica_port()
        if not self.port:
            self.logger.error("Cannot find TriSonica device")
            return False
            
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=115200,
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
            self.logger.info(f"Connected to TriSonica on {self.port}")
            self.consecutive_failures = 0  # Reset failures on successful connection
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.serial = None
            self.consecutive_failures += 1
            return False

    def read_trisonica_data(self):
        """Read data from TriSonica"""
        if not self.serial or not self.serial.is_open:
            if not self.init_serial():
                return None

        try:
            if self.serial.in_waiting > 0:
                line = self.serial.readline()
                decoded = line.decode('utf-8').strip()
                
                # Skip empty data
                if not decoded:
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

    def parse_trisonica_data(self, data):
        """Parse TriSonica data string into structured format"""
        if not data:
            return None
            
        try:
            parts = data.strip().split()
            data_dict = {}
            
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    key = parts[i]
                    value = parts[i + 1]
                    
                    try:
                        if value.startswith('-') and len(value) > 1:
                            float_value = float(value)
                        else:
                            float_value = float(value)
                        data_dict[key] = float_value
                    except ValueError:
                        data_dict[key] = value
            
            parsed_data = [
                data_dict.get('S', ''),
                data_dict.get('D', ''),
                data_dict.get('U', ''),
                data_dict.get('V', ''),
                data_dict.get('W', ''),
                data_dict.get('T', ''),
                data_dict.get('H', ''),
                data_dict.get('P', ''),
                data_dict.get('PI', ''),
                data_dict.get('RO', ''),
                data_dict.get('MD', '')
            ]
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None

    def run(self):
        """Main data collection loop"""
        self.logger.info("Starting robust TriSonica data collection")
        
        # Initialize CSV file
        with open('output/trisonica_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.PV_NAMES)
            
            # Initialize serial connection
            if not self.init_serial():
                self.logger.error("Failed to initialize TriSonica. Exiting.")
                return

            while self.running:
                try:
                    # Read data from TriSonica
                    raw_data = self.read_trisonica_data()
                    
                    if raw_data:
                        parsed_data = self.parse_trisonica_data(raw_data)
                        
                        if parsed_data:
                            # Add timestamp
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            parsed_data.append(current_time)
                            
                            # Write to CSV
                            writer.writerow(parsed_data)
                            csvfile.flush()
                            
                            self.logger.info(f"Written: Wind Speed: {parsed_data[0]} m/s, Temp: {parsed_data[5]} °C")
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
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.01)
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error in main loop: {e}")
                    self.consecutive_failures += 1
                    time.sleep(1)
        
        # Cleanup
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.logger.info("TriSonica data collection stopped")

def main():
    # Check if pyudev is available
    try:
        import pyudev
    except ImportError:
        print("ERROR: pyudev not installed. Install with: pip install pyudev")
        sys.exit(1)
    
    reader = RobustTriSonicaReader()
    reader.run()

if __name__ == "__main__":
    main()