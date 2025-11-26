# Updated pom_safe.py - Fixed version (only creates file when connected)
import serial
import csv
import signal
import sys
import time
from datetime import datetime
import pyudev
import logging
from pathlib import Path

class RobustPOMReader:
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
        self.max_failures = 5
        self.reconnect_delay = 5
        self.last_successful_read = None
        self.health_check_interval = 30
        self.header_lines_skipped = 0
        self.max_header_lines = 10
        self.csv_file = None
        self.writer = None
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_logging(self):
        formatter = logging.Formatter(fmt=f"%(asctime)s POM: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger = logging.getLogger('POM')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def signal_handler(self, sig, frame):
        self.logger.info("Stopping POM data collection...")
        self.running = False
        self.close_files()

    def close_files(self):
        """Close CSV file if open"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.writer = None

    def init_csv_file(self):
        """Initialize CSV file only when we have a working connection"""
        try:
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
            self.csv_file = open('output/pom_data.csv', 'w', newline='')
            self.writer = csv.writer(self.csv_file)
            self.writer.writerow(self.PV_NAMES)
            self.csv_file.flush()
            self.logger.info("CSV file initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV file: {e}")
            return False

    # ... (rest of the methods remain the same as your original pom_safe.py)

    def run(self):
        """Main data collection loop"""
        self.logger.info("Starting robust POM data collection")
        
        if not self.init_serial():
            self.logger.error("Failed initial connection. Will retry...")
            self.close_files()

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
                        # Reinitialize CSV file on successful reconnection
                        if not self.csv_file:
                            self.init_csv_file()
                    else:
                        self.logger.warning("Reconnection failed")
                        self.close_files()  # Close file if reconnection fails
                    last_reconnect_attempt = current_time

                # Only try to read if we have an active connection
                if self.serial and self.serial.is_open:
                    raw_data = self.read_pom_data()
                    
                    if raw_data:
                        parsed_data = self.parse_pom_data(raw_data)
                        
                        if parsed_data and self.csv_file:
                            self.writer.writerow(parsed_data)
                            self.csv_file.flush()
                            self.logger.info(f"Written: Ozone: {parsed_data[1]} ppb, Temp: {parsed_data[2]} K")
                            self.consecutive_failures = 0

                # Handle multiple failures
                if self.consecutive_failures >= self.max_failures:
                    self.logger.warning(f"Multiple failures, will attempt reconnection in {self.reconnect_delay}s")
                    self.serial = None
                    self.consecutive_failures = 0
                    last_reconnect_attempt = current_time
                    self.close_files()  # Close file on too many failures
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.consecutive_failures += 1
                time.sleep(1)
        
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.close_files()
        self.logger.info("POM data collection stopped")

def main():
    try:
        import pyudev
    except ImportError:
        print("ERROR: pyudev not installed. Install with: pip install pyudev")
        sys.exit(1)
    
    reader = RobustPOMReader()
    reader.run()

if __name__ == "__main__":
    main()