from mecom import MeCom, ResponseException, WrongChecksum
from mecom.exceptions import UnknownParameter
import pyudev
from sensor import Sensor


class MeerstetterSensor(object):
        """
        Controlling TEC devices via serial.
        """

        

        def _tearDown(self):
            self.session().stop()

        def __init__(self, idSerial, channel=1, command_table=None, metype='TEC', baudrate=57600,
                     null_value=-999., null_unit='N/A'):
            self.channel = channel
            self.idSerial = idSerial
            self.metype = metype
            self.baudrate = baudrate
            self.port = self.get_port()
            if self.port == None:
                return Sensor.FAIL
            self.command_table = command_table
            self.queries = command_table.keys() if command_table else {}
            self._session = None
            self._connect()
            self.null_value = null_value; self.null_unit = null_unit

        def _connect(self):
            self.port = self.get_port()
            # open session
            self._session = MeCom(serialport=self.port, metype=self.metype, baudrate=self.baudrate)
            # get device address
            self.address = self._session.identify()

        def get_port(self):
            device_list = pyudev.Context().list_devices()
            for device in device_list.match_subsystem("tty"):
                if device.get("ID_SERIAL") == self.idSerial:
                    return device.device_node
            return None

        def session(self):
            if self._session is None:
                self._connect()
            return self._session

        def get_data(self) -> dict:
            try:
                data = {}
                for description in self.queries:
                    id, unit = self.command_table[description]
                    try:
                        value = self.session().get_parameter(parameter_id=id, address=self.address, parameter_instance=self.channel)
                        data.update({description: (value, unit)})
                    except UnknownParameter as ex: # when looking for a value that doesn't exist
                        data.update({description: (self.null_value, self.null_unit)})
                    except (ResponseException, WrongChecksum) as ex:
                        self.session().stop()
                        self._session = None
                return data
            except Exception as err:
                # the atual error we want to fix - error(5, 'Input/output error')
                self._connect()
                return None