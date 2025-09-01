from sensor import Sensor
from meerstetterSensor import MeerstetterSensor

    
class Ldd(Sensor):

    IDENTIFIERS_1 = {"ID_VENDOR": "0403", "ID_MODEL": "6015", "ID_SERIAL": "FTDI_FT230X_Basic_UART_DQ00ONRH"}
    IDENTIFIERS_2 = {"ID_VENDOR": "0403", "ID_MODEL": "6015", "ID_SERIAL": "FTDI_FT230X_Basic_UART_DQ01F1MH"}
    PV_NAMES = ['laserDiodeCurrent', 'laserDiodeVoltage', 'anodeVoltage', 'cathodeVoltage', 'laserPower', 'externalTemperatureMeasurement', 'photodiodeInput', 'objectTemperature', 'sinkTemperature', 'targetObjectTemperature', 'temperatureStable', 'lddErrorNumber', 'lddErrorInstance', 'lddErrorParameter', 'deviceTemperature', 'temperatureLDDriver']
    
    COMMAND_TABLE = {
        "laserDiodeCurrent": [1100, "A"],                   #MeCom_LDD_Mon_LaserDiodeCurrentActual
        "laserDiodeVoltage": [1101, "V"],                   #MeCom_LDD_Mon_LaserDiodeVoltageActual
        "anodeVoltage": [1104, "V"],                        #MeCom_LDD_Mon_AnodeVoltage
        "cathodeVoltage": [1105, "V"],                      #MeCom_LDD_Mon_CathodeVoltage
        "laserPower": [1600, "W"],                          #MeCom_LDD_Mon_LaserPower
        "externalTemperatureMeasurement": [1200, "degC"],   #MeCom_LDD_Mon_LaserDiodeTemperature
        "deviceTemperature": [1065, "degC"],   
        "temperatureLDDriver": [1066, "degC"],   
        "photodiodeInput": [1501, "A"],                     #MeCom_LDD_Mon_PhotoDiode
        "lddErrorNumber": [105, ""],                        #MeCom_COM_ErrorNumber
        "lddErrorInstance": [106, ""],                      #MeCom_COM_ErrorInstance
        "lddErrorParameter": [107, ""],                     #MeCom_COM_ErrorParameter
        "objectTemperature": [1000, "degC"],
        "sinkTemperature": [1001, "degC"],
        "targetObjectTemperature": [1010, "degC"],   
        "temperatureStable": [1050, ""],
    }
            
    def init_sensor(self, modelNumber = 1):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "baudrate": 9600,
            "port": self.port,
            "timeout": 2
        }
        match modelNumber:
            case 1:
                self.IDENTIFIERS = self.IDENTIFIERS_1
            case 2:
                self.IDENTIFIERS = self.IDENTIFIERS_2
        try:
            self.mc = MeerstetterSensor(self.IDENTIFIERS["ID_SERIAL"], command_table=self.COMMAND_TABLE, metype='LDD-1321', baudrate=self.serial_opts["baudrate"])
            return super().init_sensor()
        except Exception as err:
            return Sensor.FAIL

    
    def measure_once(self) -> dict:
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        try:
            data = self.mc.get_data()
        except :
            return None
        try:
            d = {}
            if not data:
                return None
            for key in data.keys():
                d[key] = data[key][0]
            return d
        except:
            return None
        
        
        
    
    