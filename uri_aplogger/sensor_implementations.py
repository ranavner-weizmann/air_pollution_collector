# sensor_implementations.py
"""
Sensor-specific implementations
"""

from generic_sensor import GenericSensor
from datetime import datetime, timedelta

class iMetSensor(GenericSensor):
    """iMet sensor implementation"""
    
    def parse_data(self, data):
        try:
            data = data.strip().lstrip(',')
            data_list = data.split(',')
            
            # Process temperatures (divide by 100)
            data_list[1] = float(data_list[1]) 
            data_list[1] /= 100
            data_list[3] = float(data_list[3]) 
            data_list[3] /= 100

            # Adjust time by 2 hours


            # --------------------------NEED TO VERIFY !!!!! ---------------------------------



            if len(data_list) > 5 and data_list[5] and ':' in data_list[5]:
                try:
                    time_obj = datetime.strptime(data_list[5], "%H:%M:%S")
                    data_list[5] = (time_obj + timedelta(hours=2)).strftime("%H:%M:%S")
                except ValueError:
                    pass
            
            # Add timestamp and remove first field (printed XQ)
            data_list = data_list[1:11]  # Take exactly 10 fields
            data_list.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            return data_list
        except Exception as e:
            self.logger.error(f"Parse error: {e}, data: {data}")
            return None

class POMSensor(GenericSensor):
    """POM sensor implementation - Fixed"""
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self.header_lines_skipped = 0
        self.max_header_lines = 10
        self.skip_first_data_row = True  # Flag to skip the first data row
    
    def parse_data(self, data):
        try:
            # Skip header lines
            if "Personal Ozone Monitor" in data or data.isdigit():
                self.header_lines_skipped += 1
                if self.header_lines_skipped <= 3:
                    self.logger.info(f"Skipping header: {data}")
                return None
            
            data_list = data.split(',')
            
            # Handle both data formats (11 fields = real-time, 12 fields = logged)
            if len(data_list) > 12:
                self.logger.warning(f"Unexpected data format: {len(data_list)} fields, data: {data}")
                return None
            
            # Skip the first data row (which contains weird characters)
            if self.skip_first_data_row:
                self.logger.info("Skipping first data row with weird characters")
                self.skip_first_data_row = False
                return None

            # Add timestamp as first column
            data_list.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return data_list
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}, data: {data}")
            return None

class TriSonicaSensor(GenericSensor):
    """TriSonica sensor implementation"""
    
    def parse_data(self, data):
        try:
            parts = data.strip().split()
            data_dict = {}
            
            # Parse key-value pairs
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    key = parts[i].strip()
                    value = parts[i + 1].strip()
                    data_dict[key] = value
            
            # Map to output fields in correct order
            parsed_data = [
                data_dict.get('S', ''),  # Wind Speed
                data_dict.get('D', ''),  # Wind Direction
                data_dict.get('U', ''),  # U Vector
                data_dict.get('V', ''),  # V Vector
                data_dict.get('W', ''),  # W Vector
                data_dict.get('T', ''),  # Temperature
                data_dict.get('H', ''),  # Relative Humidity
                data_dict.get('P', ''),  # Pressure
                data_dict.get('PI', ''), # Compass Heading
                data_dict.get('RO', ''), # Pitch
                data_dict.get('MD', '')  # Roll
            ]
            
            # Add timestamp as first column
            parsed_data.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Parse error: {e}, data: {data}")
            return None

# Factory function to create sensors
def create_sensor(sensor_type, name, config):
    """Factory function to create appropriate sensor instance"""
    sensor_classes = {
        'iMet': iMetSensor,
        'POM': POMSensor,
        'TriSonica': TriSonicaSensor,
        'Generic': GenericSensor  # Fallback
    }
    
    sensor_class = sensor_classes.get(sensor_type, GenericSensor)
    return sensor_class(name, config)