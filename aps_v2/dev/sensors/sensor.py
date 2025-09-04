"""
Sensors base class.
Programmers: Nitzan Yizhar
Date 06/07/2023

"""
# import epics
import logging
import serial
import time
from sys import exit
import pyudev
from random import random
from collections import Counter
import numpy as np
import sys
import select



class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



class Sensor:
    """Base class for the sensors

    Attributes
    ----------
    name : str
            The name of the sensor
    port : str
        Device port of the sensor
    location : str
        Location of the device. (i.e. drone, ground ...)
    device_name : str
        name of device holding the sensor's PVs
    demo_mode: bool
            Boolean if the sensor should produce random data
    is_device: bool
        Boolean if the there is a epics device running to update
    pv_update_rate: int
        Time interval to update the pvs
    serial_opts : dict
        Serial port options


    Methods
    -------
    init_sensor() -> None
        Opens the connection to the serial port of the sensor
    close() -> None
        Closes the connection to the serial port of the sensor
    request_data() -> dict
        Reads a measurement from the sensor
    """

    class SensorFailure(Exception):
        """
        Exception returned in case of any sensor failure.
        """
        pass

    OK = 1
    FAIL = -1
    CONNECTION_TIMEOUT = 5
    IDENTIFIERS = None
    PV_NAMES = None
    Nan = -999

    def __init__(self, name: str, location: str, device_name: str, demo_mode: bool = False, is_device: bool = False, sampling_time: float = 1, vitality_cooldown: float = 0.1, to_avarage: bool = True):
        """
        Parameters
        ----------
        name : str
            The name of the sensor
        location : str
            Location of the device. (i.e. drone, ground ...)
        device_name : str
            name of the device that hold the PVs
        demo_mode: bool
            Boolean if the sensor should produce random data
        is_device: bool
            Boolean if the there is a epics device running to update
        pv_update_rate: int
            Time interval to update the pvs
        serial_opts : dict
            Serial port options
        sampling_time: float
            Time to take measures and avaraging them
        vitality_cooldown: float
            Time to sleep after measuring data
        to_avarage: bool
            Define if need to avarage or just sample once
        """
        self.name = name
        self.port = "/dev/" + self.name
        self.location = location
        self.device_name = device_name
        self.demo_mode = demo_mode
        self.is_device = is_device
        self.serial_opts = None
        self.com_running = False
        self.disconnect_time = -1
        self.last_reconnect_try_time = -1
        self.serial = None
        self.sampling_time = sampling_time
        self.vitality_cooldown = vitality_cooldown
        self.to_avarage = to_avarage

        formatter = logging.Formatter(fmt=f"%(asctime)s {name}: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        log_path, format = None, None
        with open("/home/rsp/air_pollution_collector/aps_v2/dev/sensors/main_log_path.txt", "r") as f:
            log_path = f.readline().strip()
            format = f.readline()

        logging.basicConfig(filename=log_path, format=format, level=logging.INFO)

        self.logger = logging.getLogger()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)




        # if self.is_device:
            # Creating sensor PVs
            # self.pv_list = [epics.PV(f"{self.name}:{pv}") for pv in self.PV_NAMES]


        # Just for the inital startup
        # Not sure what we want to happen here if this fails
        self.verify_connection()

        # if not self.verify_connection():
        #     return Sensor.FAIL


    def init_port(self):
        """
        initializes the port for the device
        """
        try:
            self.logger.info(f"Fetching port for {self.name} from device list")
            '''
            This give you a list of all the devices connected.
            it identifies the device by the vendor id, model_id and serial id
            both vendor id and model id can be found with lsusb in the format of
            xxxx:yyyy
            Another way to find these fields is if you know the /dev/... you can do
            udevadm info -d /dev/... and it will show you all the fields you can use
            '''
            device_list = pyudev.Context().list_devices()
            for device in device_list.match_subsystem("tty"):
                device_vendor = device.get("ID_VENDOR_ID")
                device_model = device.get("ID_MODEL_ID")
                device_serial = device.get("ID_SERIAL")
                found_vendor =  device_vendor == self.IDENTIFIERS["ID_VENDOR"]
                found_model =  device_model == self.IDENTIFIERS["ID_MODEL"].lower()
                found_serial =  device_serial == self.IDENTIFIERS["ID_SERIAL"]
                if found_vendor and found_model and found_serial:
                    self.port = str(device.device_node)
                    self.logger.info(f"Found {self.name} at port {self.port}")
                    return Sensor.OK

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except Exception as e:
            self.logger.error(f"Error while fetching port for {self.name}" + str(e))

        return Sensor.FAIL


    def serial_failure(self):
        '''
        use this function in case of any serial failure.
        It sets some of the fields required for the reconnection flow
        and closes the serial
        '''
        self.logger.error(f"Serial exception occured: {self.name} disconnected")
        ## In case of failure we want to update the pv to all be Sensor.Nan so we will see it in the server
        # self.update_pv({})

        
        fail_time = time.time()
        self.com_running = False
        self.disconnect_time = fail_time
        self.close()
        self.serial = None


    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """

        if self.demo_mode:
            self.logger.info(bcolors.WARNING +
                         bcolors.BOLD + f"{self.name} starting on demo mode" + bcolors.ENDC)
            return Sensor.OK


        # Fetching port from devices list
        if self.init_port() == Sensor.FAIL:
            return Sensor.FAIL

        self.serial_opts["port"] = self.port

        self.logger.info(f'openning serial port to {self.name} via {self.port}')
        try:
            self.serial = serial.Serial(**self.serial_opts)
            self.logger.info(f"timeout is {self.serial.timeout}")

        except serial.SerialException as e:
            self.logger.error("Failed opening serial port with " + self.name)
            self.logger.error(e)
            self.serial_failure()
            return Sensor.FAIL

        self.logger.info(f"Instantiated {self.name} via port {self.port}")
        return Sensor.OK


    def close(self):
        """
        Closes the connection to the serial port of the sensor
        """
        self.logger.info(f"\x1b[31;20m{self.name} exiting.\x1b[0m")
        if self.serial is not None:
            self.logger.info(f'\x1b[31;20mClosing serial connection with {self.name} at port {self.port}\x1b[0m')
            self.serial.close()

    def request_data(self) -> dict:
        """
        Request data from the sensor
        """

        # Checking if sensor is in demo mode
        if self.demo_mode:
            return self.demo_data()

        # Checking if there is connection with device
        if not self.verify_connection():
            return None

        try:
            data = self.measure()
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except serial.SerialException:
            self.serial_failure()
            return None
        
        except Exception as e:
            self.logger.error(f"Something happend while measuring {self.name}: " + str(e))
            return None
    

        # Maybe will want to return fake data here if it was None or maybe a dictionary of na...
        if data is None:
            pass

        return data

    def verify_connection(self):
        '''
        Verifies if there is a connection with the device.
        '''
        # There is an active connection
        if self.com_running:
            return True

        '''
        No active connection. We will retry to reconnect if CONNECTION_TIMEOUT has passed
        since last reconnect try.
        '''
        current_time  = time.time()
        # Might need to check if last_reconnect_try_time is > -1 (i think is ok either way)
        if current_time - self.last_reconnect_try_time > self.CONNECTION_TIMEOUT:
            if self.init_sensor() == Sensor.OK:
                self.com_running = True
                self.disconnect_time = -1
                self.last_reconnect_try_time = -1
                return True
            else:
                self.last_reconnect_try_time = current_time
                self.logger.error(f"{self.name} is not connected.")
                return False

        return False

    def demo_data(self):
        """
        Returns a demo data dictionary

        Returns
        -------
        dict - holding demo data
        """

        '''
        TODO: This does not fully work with all sensors because some epics records
        doesn't accepnt ints
        '''
        return {pv : str(random()) for pv in self.PV_NAMES}

    def measure_once(self) -> dict:
        """
        Reads a measurement once from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        raise NotImplementedError()
    
    def measure(self) -> dict:
        """
        Sampling until sampling_time is over and than avaraging the data
        Numbers and lists will be avaraged
        Strings and bools will be chosen as a democracy, the most "votes" wins
        
        Returns:
            dict: holding data measured and avaraged from the sensor
        """
        
        measures = []
        if self.device_name == "spectrometer" and self.first == True:
            measures = [self.measure_once()]
        
        elif not self.to_avarage:
            measures =[self.measure_once()]

        else:
            end_time = int(time.time()) + self.sampling_time
            while time.time() < end_time:
                try:
                    cur_data = self.measure_once()
                except Exception as err:
                    self.logger.error(str(err))
                    continue
                
                if cur_data: #if data is given
                    measures.append(cur_data)
                    
        if len(measures) == 0:
            self.logger.error(f"{self.name} didn't provide data")
            return None

        out_dict = {}

        num_measures = -1
        for key in self.PV_NAMES:
            if key == "num_samples":
                continue 
            data_type = None
            for measure in measures:
                if key in measure.keys():
                    data_type = type(measure[key])
                    break
            if data_type is None:
                return None
            
            elif data_type in [int, float, np.float64]: #data is number
                cnt = 0.0
                total = 0
                for measure in measures:
                    if key in measure.keys():
                        total += measure[key]
                        cnt += 1.0
                out_dict[key] = total / cnt
                num_measures = max(num_measures, cnt)
            
            elif data_type is str: #data is a string
                s = []
                cnt = 0
                for measure in measures:
                    if key in measure.keys(): 
                        cnt += 1.0
                        s.append(measure[key])
                most_common_string = Counter(s).most_common(1)[0][0]
                out_dict[key] = most_common_string
                num_measures = max(num_measures, cnt)
                
            elif data_type is bool: #data type is boolean
                t_cnt , f_cnt = 0, 0
                cnt = 0
                for measure in measures:
                    if key in measure.keys():
                        if measure[key]:
                            t_cnt += 1
                        else:
                            f_cnt += 1
                        cnt += 1
                if t_cnt >= f_cnt:
                    out_dict[key] = True
                else:
                    out_dict[key] = False
                    
                num_measures = max(num_measures, cnt)
            
            elif data_type is list:
                max_length = max(len(measure[key]) for measure in measures)
                sums = np.zeros(max_length)
                counts = np.zeros(max_length)
                for measure in measures:
                    for i, val in enumerate(measure[key]):
                        sums[i] += val
                        counts[i] += 1.0
                means = np.divide(sums, counts, out = np.zeros_like(sums), where=counts!=0)
                out_dict[key] = means.tolist()                        
            else:
                print("data type unknown")
                return None 
        
        out_dict["num_samples"] = num_measures
        return out_dict

    def update_pv(self, data: dict):
        """
        Updates the pv associated with the sensor.

        Paramters
        ----------
        data - A dictionary containing data to update in form of pv_name: value
        """
        if not self.is_device:
            return
        
        if data == None:
            return

        try:
            for pv_name, pv in zip(self.PV_NAMES, self.pv_list):
                pv.put(data.get(pv_name, str(Sensor.Nan)))

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except Exception as e:
            self.logger.error(f"{self.name}: Epics error with pv {pv_name}: " + str(e))
        
    def try_read_message(self) -> "None | str":
        ready, _, _ = select.select([sys.stdin], [], [], 0.0)
        if ready:
            message = sys.stdin.readline().strip()
            return message
        else:
            return None
    def send_message_to_device(self, message: str) -> None:
        raise NotImplementedError








