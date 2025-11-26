import serial
import csv
import signal
import sys
import time
from datetime import datetime
import pyudev
import logging
from pathlib import Path

class RobustTriSonicaReader:
    IDENTIFIERS = {
        "ID_VENDOR_ID": "10c4",
        "ID_MODEL_ID": "ea60",
        "ID_VENDOR": "Silicon Labs",
        "ID_MODEL": "CP210x UART Bridge"
    }
    
    PV_NAMES = [
        'Wind_Speed', 'Wind_Direction', 'U_Vector', 'V_Vector', 'W_Vector',
        'Temperature', 'Relative_Humidity', 'Pressure', 'Compass_Heading',
        'Pitch', 'Roll', 'Timestamp'
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
        formatter = logging.Formatter(fmt=f"%(asctime)s TriSonica: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger = logging.getLogger('TriSonica')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def signal_handler(self, sig, frame):
        self.logger.info("Stopping TriSonica data collection...")
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

    def find_trisonica_port(self):
        """Find TriSonica port using device identifiers"""
        try:
            self.logger.info("Searching for TriSonica device...")
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
                    self.logger.info(f"Found TriSonica at port: {port}")
                    return port
                
            self.logger.warning("TriSonica device not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding TriSonica port: {e}")
            return None

    def init_serial(self):
        """Initialize serial connection to TriSonica with health check"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except:
                pass
            
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
            time.sleep(2)
            
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
            
            self.logger.info(f"Connected to TriSonica on {self.port}")
            self.consecutive_failures = 0
            self.last_successful_read = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            self.serial = None
            self.consecutive_failures += 1
            return False

    def read_trisonica_data(self):
        """Read data from TriSonica with connection health monitoring"""
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
        """Main data collection loop with enhanced reconnection"""
        self.logger.info("Starting robust TriSonica data collection")
        
        # Ensure output directory exists
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        with open('output/trisonica_data.csv', 'w', newline='') as csvfile:
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
                        raw_data = self.read_trisonica_data()
                        
                        if raw_data:
                            parsed_data = self.parse_trisonica_data(raw_data)
                            
                            if parsed_data:
                                # Use system timestamp instead of device timestamp
                                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                parsed_data.append(current_time_str)
                                writer.writerow(parsed_data)
                                csvfile.flush()
                                self.logger.info(f"Written: Wind Speed: {parsed_data[0]} m/s, Time: {current_time_str}")
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
        self.logger.info("TriSonica data collection stopped")

def main():
    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    try:
        import pyudev
    except ImportError:
        print("ERROR: pyudev not installed. Install with: pip install pyudev")
        sys.exit(1)
    
    reader = RobustTriSonicaReader()
    reader.run()

if __name__ == "__main__":
    main()