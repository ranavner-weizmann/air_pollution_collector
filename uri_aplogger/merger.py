import os
import time
import csv
import signal
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class SensorMerger:
    def __init__(self, input_directory, output_file):
        self.input_directory = Path(input_directory)
        self.output_file = output_file
        self.sensor_files = {}
        self.running = True
        self.merged_headers = ['Timestamp']
        self.last_known_data = {}  # Store last known good values for each sensor
        self.current_second_data = {}  # Data for current second
        self.current_second = None
        self.merge_interval = 1.0  # Merge every second
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        print("\nStopping sensor merger...")
        self.running = False
        
    def discover_sensor_files(self):
        """Discover all sensor data files in the directory"""
        sensor_files = {}
        for file_path in self.input_directory.glob('*_data.csv'):
            sensor_name = file_path.stem.replace('_data', '')
            sensor_files[sensor_name] = {
                'path': file_path,
                'last_position': 0,
                'headers': []
            }
            print(f"Discovered sensor: {sensor_name}")
        return sensor_files
    
    def reset_file_positions(self):
        """Reset all file positions to end of file (only read new data)"""
        for sensor_name, sensor_info in self.sensor_files.items():
            try:
                file_size = os.path.getsize(sensor_info['path'])
                sensor_info['last_position'] = file_size
                print(f"Reset {sensor_name} position to end of file")
            except Exception as e:
                print(f"Error resetting position for {sensor_name}: {e}")
                sensor_info['last_position'] = 0
    
    def read_headers(self, file_path):
        """Read headers from a sensor CSV file"""
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                return headers
        except Exception as e:
            print(f"Error reading headers from {file_path}: {e}")
            return []
    
    def follow_sensor(self, sensor_name, sensor_info):
        """Read new lines from a sensor file (similar to tail -f)"""
        try:
            with open(sensor_info['path'], 'r') as f:
                f.seek(sensor_info['last_position'])
                
                lines = []
                while True:
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.strip())
                
                sensor_info['last_position'] = f.tell()
                return lines
        except Exception as e:
            print(f"Error reading from {sensor_name}: {e}")
            return []
    
    def parse_sensor_data(self, sensor_name, lines):
        """Parse CSV lines from a sensor and extract the most recent valid data"""
        most_recent_data = None
        
        for line in reversed(lines):  # Process from most recent to oldest
            if line and not line.startswith(','):  # Skip empty lines and placeholders
                try:
                    reader = csv.reader([line])
                    row = next(reader)
                    
                    # Skip header rows or obviously invalid data
                    if not row or any(header in str(cell).lower() for cell in row for header in ['pressure', 'temp', 'wind', 'speed', 'timestamp'] if len(str(cell)) > 3):
                        continue
                    
                    # Extract data based on sensor type with proper validation
                    sensor_data = []
                    if sensor_name == 'pom' and len(row) >= 13:
                        # POM data: Log_Number through Timestamp (13 columns)
                        # We want all columns except the last one (Timestamp)
                        sensor_data = row[:-1]  # All except timestamp
                    elif sensor_name == 'spectro' and len(row) >= 5:
                        # Spectro data: timestamp, peak_wavelength, max_intensity, total_points, status
                        sensor_data = row[1:4]  # Only the measurement values
                    elif sensor_name == 'iMet' and len(row) >= 11:
                        # iMet data: pressure through Timestamp (11 columns)
                        sensor_data = row[:-1]  # All except timestamp
                    elif sensor_name == 'trisonica' and len(row) >= 12:
                        # TriSonica data: Wind_Speed through Timestamp (12 columns)
                        sensor_data = row[:-1]  # All except timestamp
                    
                    if sensor_data and self.is_valid_data(sensor_name, sensor_data):
                        most_recent_data = sensor_data
                        break  # Use the most recent valid data
                        
                except Exception as e:
                    print(f"Error parsing {sensor_name} data: {e}")
                    continue
        
        return most_recent_data
    
    def is_valid_data(self, sensor_name, data):
        """Check if sensor data is valid (not empty or placeholder)"""
        if not data:
            return False
            
        # Check if data contains actual values (not just empty strings or placeholders)
        valid_count = sum(1 for item in data if item and str(item).strip() and str(item) != 'XQ')
        
        # Different validation rules for different sensors
        if sensor_name == 'iMet':
            return valid_count >= 3  # At least pressure, temp, etc.
        elif sensor_name == 'spectro':
            return valid_count >= 2  # At least wavelength and intensity
        elif sensor_name == 'pom':
            # POM should have at least ozone, temperature, and pressure values
            return valid_count >= 3  
        elif sensor_name == 'trisonica':
            return valid_count >= 3  # At least wind speed, direction, etc.
            
        return valid_count > 0
    
    def initialize_merged_headers(self):
        """Initialize merged headers from all sensor files"""
        self.merged_headers = ['Timestamp']
        
        for sensor_name, sensor_info in self.sensor_files.items():
            headers = self.read_headers(sensor_info['path'])
            if headers:
                sensor_info['headers'] = headers
                # For POM, we need to handle the special case where headers might be missing
                if sensor_name == 'pom' and not headers:
                    # Use default POM headers if file is empty
                    pom_headers = [
                        'Log_Number', 'Ozone_ppb', 'Cell_Temperature_K', 'Cell_Pressure_torr',
                        'Photodiode_Voltage_V', 'Power_Supply_V', 'Latitude', 'Longitude',
                        'Altitude_m', 'GPS_Quality', 'Date', 'Time', 'Timestamp'
                    ]
                    sensor_info['headers'] = pom_headers
                    headers = pom_headers
                
                for header in headers:
                    if header != 'Timestamp':
                        prefixed_header = f"{sensor_name}_{header}"
                        self.merged_headers.append(prefixed_header)
        
        print(f"Merged headers: {self.merged_headers}")
    
    def update_current_second_data(self):
        """Update data for the current second using all available sensors"""
        current_time = datetime.now()
        current_second_key = current_time.replace(microsecond=0)
        
        # If we've moved to a new second, prepare to merge
        if self.current_second != current_second_key:
            # If we have data from the previous second, merge it
            if self.current_second_data:
                self.merge_and_write_data()
            
            # Start fresh for the new second
            self.current_second = current_second_key
            self.current_second_data = {}
        
        # Read new data from all sensors
        all_sensor_data = {}
        for sensor_name, sensor_info in self.sensor_files.items():
            lines = self.follow_sensor(sensor_name, sensor_info)
            if lines:
                parsed_data = self.parse_sensor_data(sensor_name, lines)
                if parsed_data:
                    all_sensor_data[sensor_name] = parsed_data
                    print(f"Found new data for {sensor_name}: {parsed_data}")
        
        # Update current second data with any new readings
        for sensor_name, data in all_sensor_data.items():
            self.current_second_data[sensor_name] = data
            self.last_known_data[sensor_name] = data  # Update last known good values
    
    def merge_and_write_data(self):
        """Merge all data for the completed second and write to output"""
        if not self.current_second_data:
            print("No data to merge for current second")
            return
        
        merged_row = [None] * len(self.merged_headers)
        merged_row[0] = self.current_second.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Merging data for {self.current_second}: {list(self.current_second_data.keys())}")
        
        # Use the most recent data for each sensor from the completed second
        for sensor_name, data in self.current_second_data.items():
            if sensor_name not in self.sensor_files:
                continue
                
            sensor_headers = self.sensor_files[sensor_name]['headers']
            for i, header in enumerate(sensor_headers):
                if header != 'Timestamp':
                    prefixed_header = f"{sensor_name}_{header}"
                    if prefixed_header in self.merged_headers:
                        col_index = self.merged_headers.index(prefixed_header)
                        if i < len(data):
                            merged_row[col_index] = data[i]
                            print(f"  Set {prefixed_header} = {data[i]}")
        
        # Fill in missing sensors with their last known good values
        for sensor_name in self.sensor_files:
            if sensor_name not in self.current_second_data and sensor_name in self.last_known_data:
                sensor_headers = self.sensor_files[sensor_name]['headers']
                data = self.last_known_data[sensor_name]
                for i, header in enumerate(sensor_headers):
                    if header != 'Timestamp':
                        prefixed_header = f"{sensor_name}_{header}"
                        if prefixed_header in self.merged_headers:
                            col_index = self.merged_headers.index(prefixed_header)
                            if i < len(data):
                                # Only fill if the column is currently empty
                                if merged_row[col_index] is None:
                                    merged_row[col_index] = data[i]
                                    print(f"  Filled {prefixed_header} = {data[i]} (last known)")
        
        # Write the merged row
        try:
            with open(self.output_file, 'a', newline='') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(merged_row)
                outfile.flush()
                print(f"Successfully merged data: {[x if x else 'None' for x in merged_row[:5]]}...")
        except Exception as e:
            print(f"Error writing merged data: {e}")
    
    def run(self):
        """Main loop that merges sensor data in real time"""
        print(f"Monitoring directory: {self.input_directory}")
        print(f"Output file: {self.output_file}")
        
        # Discover sensor files
        self.sensor_files = self.discover_sensor_files()
        if not self.sensor_files:
            print("No sensor files found!")
            return
        
        # Initialize headers
        self.initialize_merged_headers()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else None, exist_ok=True)
        
        # Initialize output file with headers
        with open(self.output_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(self.merged_headers)
            outfile.flush()
            
        print("Starting real-time sensor data merger...")
        
        # Reset file positions initially (read from beginning to capture existing data)
        for sensor_name, sensor_info in self.sensor_files.items():
            sensor_info['last_position'] = 0
        
        last_merge_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Always update data (reads new lines from sensors)
            self.update_current_second_data()
            
            # Force merge every second if we have data
            if current_time - last_merge_time >= self.merge_interval:
                if self.current_second_data:
                    self.merge_and_write_data()
                    # Reset current second data but keep tracking time
                    self.current_second_data = {}
                last_merge_time = current_time
            
            time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        # Final merge before exiting
        if self.current_second_data:
            self.merge_and_write_data()
        
        print("Sensor merger stopped.")

def main():
    INPUT_DIRECTORY = "output"
    OUTPUT_FILE = "output/merged_sensors.csv"
    
    merger = SensorMerger(INPUT_DIRECTORY, OUTPUT_FILE)
    merger.run()

if __name__ == "__main__":
    main()
