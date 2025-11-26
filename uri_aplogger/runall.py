#!/usr/bin/env python3
"""
Master Sensor Controller - Debug Version
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
import subprocess
import threading

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sensor_controller_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SensorController')

class SensorProcess:
    def __init__(self, name, script_path, config=None):
        self.name = name
        self.script_path = script_path
        self.config = config or {}
        self.process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.last_restart = None
        self.is_running = False
        self.output_file = None
        self.full_stderr = []  # Store full stderr output
        
    def start(self):
        """Start the sensor process with full error capture"""
        try:
            if not os.path.exists(self.script_path):
                logger.error(f"Sensor script not found: {self.script_path}")
                return False
            
            # Create output directory if it doesn't exist
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
            self.output_file = self._get_output_file()
            
            env = os.environ.copy()
            env['PYTHONPATH'] = os.getcwd()
            
            logger.debug(f"Starting {self.name} with script: {self.script_path}")
            
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            self.is_running = True
            self.last_restart = datetime.now()
            self.full_stderr = []  # Reset stderr storage
            
            # Start thread to monitor output
            self._start_output_monitor()
            
            logger.info(f"Started {self.name} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    def _get_output_file(self):
        sensor_outputs = {
            'iMet': 'output/iMet_data.csv',
            'POM': 'output/pom_data.csv', 
            'TriSonica': 'output/trisonica_data.csv',
            'Spectrometer': 'output/spectro_data.csv',
            'Merger': 'output/merged_sensors.csv'
        }
        return sensor_outputs.get(self.name, f'output/{self.name.lower()}_data.csv')
    
    def _start_output_monitor(self):
        def monitor_output():
            while self.process and self.process.poll() is None:
                try:
                    # Read stdout
                    stdout_line = self.process.stdout.readline()
                    if stdout_line:
                        logger.info(f"{self.name}: {stdout_line.strip()}")
                    
                    # Read stderr  
                    stderr_line = self.process.stderr.readline()
                    if stderr_line:
                        self.full_stderr.append(stderr_line)  # Store for debugging
                        logger.error(f"{self.name} ERROR: {stderr_line.strip()}")
                        
                except Exception as e:
                    logger.error(f"Error monitoring {self.name} output: {e}")
                    break
            
            # Process has ended, read any remaining output
            try:
                if self.process:
                    remaining_stdout, remaining_stderr = self.process.communicate(timeout=1)
                    if remaining_stdout:
                        logger.info(f"{self.name} (final): {remaining_stdout.strip()}")
                    if remaining_stderr:
                        self.full_stderr.append(remaining_stderr)
                        logger.error(f"{self.name} ERROR (final): {remaining_stderr.strip()}")
            except:
                pass
        
        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()
    
    def get_full_error(self):
        """Get the complete error output"""
        return "".join(self.full_stderr)
    
    def stop(self):
        if not self.process:
            return
            
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {self.name}")
                self.process.kill()
                self.process.wait()
                
            logger.info(f"Stopped {self.name}")
            
        except Exception as e:
            logger.error(f"Error stopping {self.name}: {e}")
        finally:
            self.process = None
            self.is_running = False
    
    def restart(self):
        logger.info(f"Restarting {self.name} (restart #{self.restart_count + 1})")
        
        # Log full error before restarting
        full_error = self.get_full_error()
        if full_error:
            logger.error(f"Full error from {self.name} before restart:\n{full_error}")
        
        self.stop()
        time.sleep(3)
        success = self.start()
        
        if success:
            self.restart_count += 1
        else:
            logger.error(f"Failed to restart {self.name}")
            
        return success
    
    def is_alive(self):
        return self.process and self.process.poll() is None
    
    def get_status(self):
        status = {
            'name': self.name,
            'running': self.is_alive(),
            'pid': self.process.pid if self.process else None,
            'restart_count': self.restart_count,
            'exit_code': self.process.poll() if self.process else None,
            'script_path': self.script_path,
            'output_file': self.output_file
        }
        return status

class SensorController:
    def __init__(self, config_file='sensor_config.json'):
        self.sensors = {}
        self.running = False
        self.health_check_interval = 30
        self.config_file = config_file
        self.merger_process = None
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def load_config(self):
        default_config = {
            "sensors": {
                "iMet": {
                    "script": "iMet_safe.py",
                    "enabled": True,
                    "restart_delay": 5,
                    "startup_delay": 5
                },
                "POM": {
                    "script": "pom_safe.py", 
                    "enabled": True,
                    "restart_delay": 5,
                    "startup_delay": 2
                },
                "TriSonica": {
                    "script": "trisonica_safe.py",
                    "enabled": True, 
                    "restart_delay": 5,
                    "startup_delay": 5
                },
                "Spectrometer": {
                    "script": "spectro.py",
                    "enabled": True,
                    "restart_delay": 5,
                    "startup_delay": 2
                }
            },
            "merger": {
                "script": "merger.py",
                "enabled": True,
                "startup_delay": 15
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration file: {self.config_file}")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}, using defaults")
            return default_config
    
    def initialize_sensors(self):
        config = self.load_config()
        
        for name, sensor_config in config['sensors'].items():
            if sensor_config.get('enabled', True):
                script_path = sensor_config['script']
                if not os.path.isabs(script_path):
                    script_path = os.path.join(os.getcwd(), script_path)
                
                self.sensors[name] = SensorProcess(name, script_path, sensor_config)
                logger.info(f"Initialized sensor: {name}")
        
        if config['merger'].get('enabled', True):
            merger_script = config['merger']['script']
            if not os.path.isabs(merger_script):
                merger_script = os.path.join(os.getcwd(), merger_script)
            
            self.merger_process = SensorProcess("Merger", merger_script, config['merger'])
            logger.info("Initialized data merger")
    
    def test_sensor_script(self, sensor_name):
        """Test running a sensor script directly to see the error"""
        sensor = self.sensors[sensor_name]
        logger.info(f"Testing {sensor_name} script directly...")
        
        try:
            result = subprocess.run(
                [sys.executable, sensor.script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            logger.info(f"{sensor_name} test return code: {result.returncode}")
            if result.stdout:
                logger.info(f"{sensor_name} test stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"{sensor_name} test stderr:\n{result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.info(f"{sensor_name} test timed out (might be running normally)")
        except Exception as e:
            logger.error(f"{sensor_name} test error: {e}")
    
    def start_all(self):
        logger.info("Starting all sensor processes...")
        
        # Test problematic sensors first
        #if 'iMet' in self.sensors:
        #    self.test_sensor_script('iMet')
        
        #if 'TriSonica' in self.sensors:
        #    self.test_sensor_script('TriSonica')
        
        # Start sensors with longer delays for problematic ones
        for sensor_name, sensor in self.sensors.items():
            if not sensor.start():
                logger.error(f"Failed to start {sensor.name}")
            else:
                delay = sensor.config.get('startup_delay', 2)
                logger.info(f"Waiting {delay} seconds for {sensor.name} to initialize...")
                time.sleep(delay)
        
        # Start merger
        if self.merger_process:
            merger_delay = self.merger_process.config.get('startup_delay', 5)
            logger.info(f"Waiting {merger_delay} seconds before starting merger...")
            time.sleep(merger_delay)
            
            if not self.merger_process.start():
                logger.error("Failed to start merger process")
            else:
                logger.info("Merger process started")
        
        self.running = True
        logger.info("All processes started")
    
    def stop_all(self):
        logger.info("Stopping all processes...")
        self.running = False
        
        if self.merger_process:
            logger.info("Stopping merger process...")
            self.merger_process.stop()
        
        for sensor_name, sensor in self.sensors.items():
            logger.info(f"Stopping {sensor_name}...")
            sensor.stop()
        
        logger.info("All processes stopped")
    
    def health_check(self):
        for sensor_name, sensor in self.sensors.items():
            if not sensor.is_alive() and sensor.is_running:
                exit_code = sensor.process.poll() if sensor.process else 'N/A'
                logger.warning(f"Sensor {sensor_name} is not running (exit code: {exit_code})")
                
                # Log full error for debugging
                full_error = sensor.get_full_error()
                if full_error:
                    logger.error(f"Full error from {sensor_name}:\n{full_error}")
                
                if sensor.restart_count < sensor.max_restarts:
                    sensor.restart()
                else:
                    logger.error(f"Sensor {sensor_name} exceeded maximum restart attempts")
                    sensor.is_running = False
        
        if self.merger_process and not self.merger_process.is_alive() and self.merger_process.is_running:
            logger.warning("Merger process is not running")
            if self.merger_process.restart_count < self.merger_process.max_restarts:
                self.merger_process.restart()
            else:
                logger.error("Merger exceeded maximum restart attempts")
                self.merger_process.is_running = False
    
    def get_status_report(self):
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
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def run(self):
        self.initialize_sensors()
        self.start_all()
        
        logger.info("Sensor controller running. Press Ctrl+C to stop.")
        
        last_health_check = time.time()
        last_status_report = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                
                if current_time - last_health_check >= self.health_check_interval:
                    self.health_check()
                    last_health_check = current_time
                
                if current_time - last_status_report >= 60:
                    status = self.get_status_report()
                    logger.info("=== Status Report ===")
                    for sensor_name, sensor_status in status['sensors'].items():
                        state = "RUNNING" if sensor_status['running'] else "STOPPED"
                        exit_info = f"(Exit: {sensor_status.get('exit_code', 'N/A')})"
                        restart_info = f"(Restarts: {sensor_status['restart_count']})"
                        logger.info(f"  {sensor_name}: {state} {exit_info} {restart_info}")
                    
                    if status['merger']:
                        state = "RUNNING" if status['merger']['running'] else "STOPPED"
                        restart_info = f"(Restarts: {status['merger']['restart_count']})"
                        logger.info(f"  Merger: {state} {restart_info}")
                    
                    logger.info("=====================")
                    last_status_report = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop_all()

def main():
    controller = SensorController()
    controller.run()

if __name__ == "__main__":
    main()