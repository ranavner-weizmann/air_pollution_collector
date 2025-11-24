import os
import time
import csv
import signal
from datetime import datetime
from pathlib import Path

class SensorMerger:
    def __init__(self, input_directory, output_file):
        self.input_directory = Path(input_directory)
        self.output_file = output_file
        self.sensor_files = {}
        self.running = True
        self.merged_headers = ['Timestamp']
        
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
                # Seek to the last known position
                f.seek(sensor_info['last_position'])
                
                lines = []
                while True:
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.strip())
                
                # Update the last position
                sensor_info['last_position'] = f.tell()
                
                return lines
        except Exception as e:
            print(f"Error reading from {sensor_name}: {e}")
            return []
    
    def parse_sensor_data(self, sensor_name, lines):
        """Parse CSV lines from a sensor"""
        data = []
        for line in lines:
            if line:  # Skip empty lines
                try:
                    # Parse CSV line
                    reader = csv.reader([line])
                    row = next(reader)
                    data.append(row)
                except Exception as e:
                    print(f"Error parsing line from {sensor_name}: {e}")
        return data
    
    def initialize_merged_headers(self):
        """Initialize merged headers from all sensor files"""
        # Reset merged headers
        self.merged_headers = ['Timestamp']
        
        # Read headers from each sensor file
        for sensor_name, sensor_info in self.sensor_files.items():
            headers = self.read_headers(sensor_info['path'])
            if headers:
                sensor_info['headers'] = headers
                # Add sensor-specific headers (prefixed with sensor name)
                for header in headers:
                    if header != 'Timestamp':  # Don't duplicate timestamp
                        prefixed_header = f"{sensor_name}_{header}"
                        self.merged_headers.append(prefixed_header)
        
        print(f"Merged headers: {self.merged_headers}")
    
    def merge_data(self, all_sensor_data):
        """Merge data from all sensors into a single row"""
        merged_row = [None] * len(self.merged_headers)
        merged_row[0] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp
        
        for sensor_name, sensor_data in all_sensor_data.items():
            if sensor_data:  # If we have new data from this sensor
                latest_data = sensor_data[-1]  # Take the most recent reading
                sensor_headers = self.sensor_files[sensor_name]['headers']
                
                # Map sensor data to merged columns
                for i, header in enumerate(sensor_headers):
                    if header != 'Timestamp':  # Skip timestamp from individual sensors
                        prefixed_header = f"{sensor_name}_{header}"
                        if prefixed_header in self.merged_headers:
                            col_index = self.merged_headers.index(prefixed_header)
                            if i < len(latest_data):
                                merged_row[col_index] = latest_data[i]
        
        return merged_row
    
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
        
        # Open output file
        with open(self.output_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(self.merged_headers)
            outfile.flush()
            
            print("Starting real-time sensor data merger...")
            
            while self.running:
                all_sensor_data = {}
                
                # Read new data from each sensor
                for sensor_name, sensor_info in self.sensor_files.items():
                    lines = self.follow_sensor(sensor_name, sensor_info)
                    if lines:
                        parsed_data = self.parse_sensor_data(sensor_name, lines)
                        if parsed_data:
                            all_sensor_data[sensor_name] = parsed_data
                
                # Merge data and write to output
                if all_sensor_data:
                    merged_row = self.merge_data(all_sensor_data)
                    writer.writerow(merged_row)
                    outfile.flush()
                    print(f"Merged data: {merged_row}")
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        print("Sensor merger stopped.")

def main():
    # Configuration
    INPUT_DIRECTORY = "/home/rsp/work/uri/output"  # Directory containing sensor CSV files
    OUTPUT_FILE = "/home/rsp/work/uri/output/merged_sensors.csv"  # Output merged file
    
    # Create and run the sensor merger
    merger = SensorMerger(INPUT_DIRECTORY, OUTPUT_FILE)
    merger.run()

if __name__ == "__main__":
    main()