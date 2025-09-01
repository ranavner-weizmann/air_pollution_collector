from sensor import Sensor
import serial

class ThermacoupleGroove(Sensor):
    #==============replace identifiers====================#
    IDENTIFIERS = {"ID_VENDOR": "2341", "ID_MODEL": "0043", "ID_SERIAL": "Arduino__www.arduino.cc__0043_9513832383835121B0B1"}
    #==============replace identifiers====================#
    PV_NAMES = ['temperature']
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
        line = self.serial.readline().decode()
        print(f"Initializing ThermacoupleGroove sensor, trying to read redundent line about version. what I actually read {line}")
        return sensorInitResult
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        try:
            line = self.serial.readline().decode()
            data_received = line.split(',')
            EXPECTED_LINE_PARAMETERS_AMOUNT = 1
            ACTUAL_LINE_PARAMETERS_AMOUNT = len(data_received)
            if (ACTUAL_LINE_PARAMETERS_AMOUNT != EXPECTED_LINE_PARAMETERS_AMOUNT):
                raise serial.SerialException(f"ThermocoupleGroove, expected {EXPECTED_LINE_PARAMETERS_AMOUNT} parameters in serail read, but got {ACTUAL_LINE_PARAMETERS_AMOUNT}")
            measures = {}
            measures["temperature"] = float(data_received[0])
            return measures
        except (IndexError, ValueError):
            return None
