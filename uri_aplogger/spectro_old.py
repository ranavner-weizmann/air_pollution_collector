# Updated spectro.py - Fixed version
import seabreeze
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb
import time
import csv
from datetime import datetime
import logging
import signal
import sys

class RobustOceanSR6Reader:
    def __init__(self):
        self.spec = None
        self.running = True
        self.consecutive_failures = 0
        self.max_failures = 3  # Reduced to fail faster
        self.reconnect_delay = 2  # Reduced reconnect delay
        self.last_successful_read = None
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            format='%(asctime)s OceanSR6: %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger()
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.logger.info("Stopping OceanSR6 data collection...")
        self.running = False
    
    def connect(self):
        """Connect to OceanSR6 with error handling"""
        try:
            devices = sb.list_devices()
            
            if not devices:
                self.logger.warning("No spectrometers found!")
                return False
            
            self.spec = sb.Spectrometer(devices[0])
            self.logger.info(f"Connected to: {self.spec.model}")
            
            # Set reasonable integration time
            self.spec.integration_time_micros(100000)  # 100ms
            self.logger.info("Integration time set to 100ms")
            
            self.consecutive_failures = 0
            self.last_successful_read = time.time()
            return True
            
        except Exception as e:
            self.logger.warning(f"Connection failed: {e}")
            self.consecutive_failures += 1
            return False
    
    def safe_get_spectrum(self):
        """Safely get spectrum with error recovery"""
        if not self.spec:
            return None
        
        try:
            wavelengths = self.spec.wavelengths()
            intensities = self.spec.intensities()
            
            # Validate data
            if len(wavelengths) == 0 or len(intensities) == 0:
                self.logger.warning("Empty spectrum data received")
                self.consecutive_failures += 1
                return None
            
            # Basic analysis
            max_intensity = max(intensities)
            peak_wavelength = wavelengths[intensities.argmax()]
            
            self.consecutive_failures = 0
            self.last_successful_read = time.time()
            
            return {
                'wavelengths': wavelengths,
                'intensities': intensities,
                'peak_wavelength': peak_wavelength,
                'max_intensity': max_intensity,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.warning(f"Measurement failed: {e}")
            self.consecutive_failures += 1
            self.spec = None  # Mark as disconnected
            return None
    
    def reconnect(self):
        """Attempt to reconnect to the spectrometer"""
        if self.consecutive_failures >= self.max_failures:
            self.logger.info(f"Too many failures, waiting {self.reconnect_delay}s before reconnect...")
            time.sleep(self.reconnect_delay)
        
        self.logger.info("Attempting to reconnect...")
        return self.connect()
    
    def continuous_reading(self, output_file=None):
        """Continuous data collection with full failsafes"""
        # Setup CSV file
        csv_file = None
        if output_file:
            try:
                csv_file = open(output_file, 'w', newline='')
                writer = csv.writer(csv_file)
                writer.writerow(['timestamp', 'peak_wavelength', 'max_intensity', 'total_points', 'status'])
                self.logger.info(f"Data logging to: {output_file}")
            except Exception as e:
                self.logger.error(f"Failed to create CSV file: {e}")
                csv_file = None
        
        self.logger.info("Starting continuous reading. Press Ctrl+C to stop.")
        
        measurement_count = 0
        last_connection_attempt = 0
        connection_attempt_interval = 10  # Try to reconnect every 10 seconds if disconnected
        
        try:
            while self.running:
                current_time = time.time()
                
                # If we don't have a connection, try to get one periodically
                if not self.spec:
                    if current_time - last_connection_attempt >= connection_attempt_interval:
                        if self.connect():
                            self.logger.info("Successfully reconnected to spectrometer")
                        last_connection_attempt = current_time
                    else:
                        # If no connection, just sleep and continue
                        time.sleep(1)
                        continue
                
                # Get spectrum if we have a connection
                spectrum = self.safe_get_spectrum()
                
                if spectrum:
                    measurement_count += 1
                    
                    # Log the measurement
                    self.logger.info(
                        f"Scan {measurement_count}: Peak {spectrum['peak_wavelength']:.1f} nm, "
                        f"Intensity {spectrum['max_intensity']:.0f}"
                    )
                    
                    # Save to CSV if requested
                    if csv_file:
                        try:
                            writer = csv.writer(csv_file)
                            writer.writerow([
                                spectrum['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f"),
                                f"{spectrum['peak_wavelength']:.4f}",
                                f"{spectrum['max_intensity']:.2f}",
                                len(spectrum['wavelengths']),
                                'success'
                            ])
                            csv_file.flush()
                        except Exception as e:
                            self.logger.error(f"CSV write failed: {e}")
                
                # If we have too many failures, disconnect and wait for reconnect
                if self.consecutive_failures >= self.max_failures:
                    self.logger.warning("Too many consecutive failures, will attempt recovery...")
                    self.spec = None
                    time.sleep(self.reconnect_delay)
                
                time.sleep(0.5)  # Reduced sleep time for more responsive behavior
                
        except KeyboardInterrupt:
            self.logger.info(f"Stopped by user after {measurement_count} measurements")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.close()
            if csv_file:
                csv_file.close()
    
    def close(self):
        """Safely close the spectrometer"""
        if self.spec:
            try:
                self.spec.close()
                self.logger.info("Spectrometer closed safely")
            except Exception as e:
                self.logger.error(f"Error closing spectrometer: {e}")
            finally:
                self.spec = None

def main():
    reader = RobustOceanSR6Reader()
    reader.continuous_reading(output_file='output/spectro_data.csv')

if __name__ == "__main__":
    main()