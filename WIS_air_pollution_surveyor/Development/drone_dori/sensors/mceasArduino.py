from sensor import Sensor
import serial
from time import sleep

class MceasArduino(Sensor):
    #==============replace identifiers====================#
    IDENTIFIERS = {"ID_VENDOR": "2341", "ID_MODEL": "0058", "ID_SERIAL": "Arduino_LLC_Arduino_Nano_Every_04A1675F514E4650414B2020FF0E3A5B"}
    #==============replace identifiers====================#
    PV_NAMES = ['temperature', 'humidity', 'laserDiodeCurrent', 'laserDiodeVoltage', 'anodeVoltage', 'cathodeVoltage', 'laserPower', 'laserDiodeTemperature', 'basePlateTemperature', 'photodiodeInput', 'lddErrorNumber', 'lddErrorInstance', 'lddErrorParameter', 'lddObjectTemperature', 'lddSinkTemperature', 'lddTargetObjectTemperature', 'lddTemperatureStable', 'tecObjectTemp1', 'tecTargetTemp1', 'tecErrorNumber1', 'tecErrorInstance1', 'tecErrorParameter1', 'tecObjectTemp2', 'tecTargetTemp2', 'tecErrorNumber2', 'tecErrorInstance2', 'tecErrorParameter2', "pressureRaw", "pressureFormulated"]
    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "port": self.port,
            "baudrate": 115200,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
            "timeout": 1     
        }
        sensorInitResult = super().init_sensor()
        return sensorInitResult
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        
        data_dict = {}
        try:
            line = self.serial.readline()
       
        except serial.SerialException as e:
            self.logger.error(f"{self.name} serial expection: " + str(e))
            self.serial_failure()
            return None
        
        decoded_list = line.decode('utf-8').split(',')
        EXPECTED_LINE_PARAMETERS_AMOUNT = len(self.PV_NAMES)
        ACTUAL_LINE_PARAMETERS_AMOUNT = len(decoded_list)
        #-1 is to remove the count if num_smaples
        if ACTUAL_LINE_PARAMETERS_AMOUNT is not EXPECTED_LINE_PARAMETERS_AMOUNT - 1:
            raise serial.SerialException(f"mceasArduino, expected {EXPECTED_LINE_PARAMETERS_AMOUNT} parameters in serail read, but got {ACTUAL_LINE_PARAMETERS_AMOUNT}")
        
        for i in range(len(decoded_list)):
            try:
                data_dict[self.PV_NAMES[i]]=float(decoded_list[i])
            except (ValueError, IndexError) as err:
                data_dict[self.PV_NAMES[i]]=0
                self.logger.error(str(err))
        if data_dict == {}:
            return None
        
        return data_dict
    def send_message_to_device(self, message: bytes) -> None:
        self.serial.write(message)
        sleep(0.5)
