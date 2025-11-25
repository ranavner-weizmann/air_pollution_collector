#!/usr/bin/env python3
"""
Master Sensor Controller
Manages multiple sensor data collection scripts with automatic recovery
"""

import multiprocessing
import time
import logging
import signal
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sensor_controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SensorController')

class SensorProcess:
    """Represents a managed sensor process"""
    
    def __init__(self, name, script_path, config=None):
        self.name = name
        self.script_path = script_path
        self.config = config or {}
        self.process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.last_restart = None
        self.is_running = False
        
    def start(self):
        """Start the sensor process"""
        try:
            if not os.path.exists(self.script_path):
                logger.error(f"Sensor script not found: {self.script_path}")
                return False
            
            # Create output directory if it doesn't exist
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
            # Start the process
            self.process = multiprocessing.Process(
                target=self._run_sensor_script,
                name=f"Sensor-{self.name}"
            )
            self.process.daemon = False  # Don't make it daemon so we can manage it properly
            self.process.start()
            self.is_running = True
            self.last_restart = datetime.now()
            
            logger.info(f"Started {self.name} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    def _run_sensor_script(self):
        """Run the sensor script in the current process context"""
        try:
            # Add current directory to Python path
            script_dir = os.path.dirname(os.path.abspath(self.script_path))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # Import and run the script
            module_name = os.path.basename(self.script_path).replace('.py', '')
            spec = __import__(module_name)
            
            # Find and run the main function
            if hasattr(spec, 'main'):
                spec.main()
            else:
                logger.error(f"No main function found in {self.script_path}")
                
        except Exception as e:
            logger.error(f"Error running {self.name}: {e}")
            raise
    
    def stop(self):
        """Stop the sensor process"""
        if self.process and self.process.is_alive():
            try:
                # Try graceful termination first
                self.process.terminate()
                self.process.join(timeout=5)
                
                # Force kill if still alive
                if self.process.is_alive():
                    self.process.kill()
                    self.process.join()
                    
                logger.info(f"Stopped {self.name}")
                
            except Exception as e:
                logger.error(f"Error stopping {self.name}: {e}")
                
            finally:
                self.process = None
                self.is_running = False
    
    def restart(self):
        """Restart the sensor process"""
        logger.info(f"Restarting {self.name} (restart #{self.restart_count + 1})")
        self.stop()
        time.sleep(2)  # Brief delay before restart
        success = self.start()
        
        if success:
            self.restart_count += 1
        else:
            logger.error(f"Failed to restart {self.name}")
            
        return success
    
    def is_alive(self):
        """Check if the process is alive"""
        return self.process and self.process.is_alive()
    
    def get_status(self):
        """Get status information"""
        status = {
            'name': self.name,
            'running': self.is_alive(),
            'pid': self.process.pid if self.process else None,
            'restart_count': self.restart_count,
            'last_restart': self.last_restart.isoformat() if self.last_restart else None,
            'script_path': self.script_path
        }
        
        # Add memory info if process is running
        if self.process and self.process.is_alive():
            try:
                process = psutil.Process(self.process.pid)
                status['memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 2)
                status['cpu_percent'] = round(process.cpu_percent(), 2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        return status

class SensorController:
    """Main controller for managing all sensor processes"""
    
    def __init__(self, config_file='sensor_config.json'):
        self.sensors = {}
        self.running = False
        self.health_check_interval = 30  # seconds
        self.config_file = config_file
        self.merger_process = None
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def load_config(self):
        """Load sensor configuration from JSON file"""
        default_config = {
            "sensors": {
                "iMet": {
                    "script": "iMet_safe.py",
                    "enabled": True,
                    "restart_delay": 5
                },
                "POM": {
                    "script": "pom_safe.py", 
                    "enabled": True,
                    "restart_delay": 5
                },
                "TriSonica": {
                    "script": "trisonica_safe.py",
                    "enabled": True, 
                    "restart_delay": 5
                },
                "Spectrometer": {
                    "script": "spectro.py",
                    "enabled": True,
                    "restart_delay": 5
                }
            },
            "merger": {
                "script": "merger.py",
                "enabled": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration file: {self.config_file}")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}, using defaults")
            return default_config
    
    def initialize_sensors(self):
        """Initialize all sensors from configuration"""
        config = self.load_config()
        
        # Initialize sensors
        for name, sensor_config in config['sensors'].items():
            if sensor_config.get('enabled', True):
                script_path = sensor_config['script']
                if not os.path.isabs(script_path):
                    script_path = os.path.join(os.getcwd(), script_path)
                
                self.sensors[name] = SensorProcess(name, script_path, sensor_config)
                logger.info(f"Initialized sensor: {name}")
        
        # Initialize merger if enabled
        if config['merger'].get('enabled', True):
            merger_script = config['merger']['script']
            if not os.path.isabs(merger_script):
                merger_script = os.path.join(os.getcwd(), merger_script)
            
            self.merger_process = SensorProcess("Merger", merger_script, config['merger'])
            logger.info("Initialized data merger")
    
    def start_all(self):
        """Start all sensors and the merger"""
        logger.info("Starting all sensor processes...")
        
        # Start sensors
        for sensor in self.sensors.values():
            if not sensor.start():
                logger.error(f"Failed to start {sensor.name}")
        
        # Start merger
        if self.merger_process:
            time.sleep(5)  # Wait a bit for sensors to initialize
            if not self.merger_process.start():
                logger.error("Failed to start merger process")
        
        self.running = True
        logger.info("All processes started")
    
    def stop_all(self):
        """Stop all sensors and the merger"""
        logger.info("Stopping all processes...")
        self.running = False
        
        # Stop merger first
        if self.merger_process:
            self.merger_process.stop()
        
        # Stop sensors
        for sensor in self.sensors.values():
            sensor.stop()
        
        logger.info("All processes stopped")
    
    def health_check(self):
        """Check health of all processes and restart failed ones"""
        for sensor in self.sensors.values():
            if not sensor.is_alive() and sensor.is_running:
                logger.warning(f"Sensor {sensor.name} is not running")
                if sensor.restart_count < sensor.max_restarts:
                    sensor.restart()
                else:
                    logger.error(f"Sensor {sensor.name} exceeded maximum restart attempts")
                    sensor.is_running = False
        
        # Check merger
        if self.merger_process and not self.merger_process.is_alive() and self.merger_process.is_running:
            logger.warning("Merger process is not running")
            if self.merger_process.restart_count < self.merger_process.max_restarts:
                self.merger_process.restart()
            else:
                logger.error("Merger exceeded maximum restart attempts")
                self.merger_process.is_running = False
    
    def get_status_report(self):
        """Generate a status report for all processes"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sensors': {},
            'merger': None
        }
        
        for name, sensor in self.sensors.items():
            report['sensors'][name] = sensor.get_status()
        
        if self.merger_process:
            report['merger'] = self.merger_process.get_status()
            
        return report
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def add_sensor(self, name, script_path, config=None):
        """Dynamically add a new sensor"""
        if name in self.sensors:
            logger.warning(f"Sensor {name} already exists, replacing")
        
        self.sensors[name] = SensorProcess(name, script_path, config or {})
        logger.info(f"Added new sensor: {name}")
        
        if self.running:
            self.sensors[name].start()
    
    def remove_sensor(self, name):
        """Remove a sensor"""
        if name in self.sensors:
            self.sensors[name].stop()
            del self.sensors[name]
            logger.info(f"Removed sensor: {name}")
        else:
            logger.warning(f"Sensor {name} not found")
    
    def run(self):
        """Main controller loop"""
        self.initialize_sensors()
        self.start_all()
        
        logger.info("Sensor controller running. Press Ctrl+C to stop.")
        
        last_health_check = time.time()
        last_status_report = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                # Periodic health check
                if current_time - last_health_check >= self.health_check_interval:
                    self.health_check()
                    last_health_check = current_time
                
                # Periodic status reporting
                if current_time - last_status_report >= 60:  # Every minute
                    status = self.get_status_report()
                    logger.info("Status Report:")
                    for sensor_name, sensor_status in status['sensors'].items():
                        state = "RUNNING" if sensor_status['running'] else "STOPPED"
                        logger.info(f"  {sensor_name}: {state} (Restarts: {sensor_status['restart_count']})")
                    
                    if status['merger']:
                        state = "RUNNING" if status['merger']['running'] else "STOPPED"
                        logger.info(f"  Merger: {state} (Restarts: {status['merger']['restart_count']})")
                    
                    last_status_report = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop_all()

def main():
    """Main entry point"""
    controller = SensorController()
    controller.run()

if __name__ == "__main__":
    main()
