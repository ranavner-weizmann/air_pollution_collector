# -*- coding: utf-8 -*-
"""
OPC Sensor class
Programmer: Nitzan Yizhar and Lior Segev
Date 06/07/2023
Based on code by Daniel Jarvis

"""

import struct
import time
import serial
from sensor import Sensor

wait = 100e-06

class Opc(Sensor):
    IDENTIFIERS = {"ID_VENDOR": "04d8", "ID_MODEL": "ffee", "ID_SERIAL": "Devantech_Ltd._USB-ISS._00059129"}
    PV_NAMES = ["period", "Flowrate", "pm1", "pm2dot5", "pm10", "bins", "laser_status"]
    



    def __init__(self, name: str, location: str, device_name: str, sampling_time = 1, demo_mode: bool = False, is_device: bool = False):
        """
        Parameters
        ----------
        name : str
            The name of the sensor
        location : str
            Location of the device. (i.e. drone, ground ...)
        device_name : str
            name of the epics device that hold the PVs
        pv_update_rate: int
            Time interval to update the pvs
        pv_names: list
            List of PV names corresponding for this sensor
        demo_mode: bool
            Boolean if the sensor should produce random data
        is_device: bool
            Boolean if the there is a epics device running to update
        """
        self.comm = False
        self.laser_status = False
        self.fan_status = False
        super().__init__(name=name, location=location, device_name=device_name, demo_mode=demo_mode, is_device=is_device, sampling_time=sampling_time)


    def init_sensor(self):
        """
        Opens the connection to the serial port of the sensor
        """
        self.serial_opts = {
            "port": self.port,
            "baudrate": 9600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 1
        }

        # wait for opc to boot
        time.sleep(2)

        if super().init_sensor() == Sensor.FAIL:
            self.comm = False
            # self.logger.info('communication failed - check USB connection to raspberry PI host')
            return Sensor.FAIL

        if self.demo_mode:
            return Sensor.OK

        # print("Init:")
        try:
            time.sleep(1)
            self.serial.write(bytearray([0x5a, 0x01]))
            nl = self.serial.read(3)
            time.sleep(wait)
            self.serial.write(bytearray([0x5a, 0x03]))
            nl = self.serial.read(9)
            time.sleep(wait)

            # spi conncetion
            self.serial.write(bytearray([0x5a, 0x02, 0x92, 0x07]))
            nl = self.serial.read(2)
            time.sleep(wait)
            
            # turn on Lazer and Fan for the correct operation of the OPC
            self.laz_ctrl(True)
            self.fan_ctrl(True)
        except serial.SerialException:
            self.serial_failure()
            return Sensor.FAIL

        return Sensor.OK

    def init_opc(self):
        self.init_sensor()

    def close_opc(self):
        self.close()
    
    def measure_once(self):
        """
        Reads a measurement from the sensor

        Returns
        -------
        dict - holding data measured from the sensor
        """
        data = self.read_data()
        if data is not None:
            data = {
                "period": data["period"],
                "Flowrate": data["FlowRate"],
                "pm1": data["pm1"],
                "pm2dot5": data["pm2.5"],
                "pm10": data["pm10"],
                "bins": [data[f"Bin{i}"] for i in range(24)],
                "laser_status": data["laser_status"],
                ## SHOULD WE ADD THE COMM, LASER AND FAN STATUS
            }
        return data


    def gain_ctrl(self, ctrl_flag=False):
        '''
        setting Gain to HIGH or LOW will automatically remove autogain option
        The instrument will have to be reset for the autogain option to return to its active state
        '''
        T = 0
        while True:
            self.serial.write(bytearray([0x61, 0x03]))
            nl = self.serial.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if ctrl_flag:
                    # GAIN HIGH
                    self.logger.info("Request to toggle GAIN to HIGH")
                    self.serial.write(bytearray([0x61, 0x09]))
                    nl = self.serial.read(2)
                    self.fan_status = True
                    self.logger.info("Gain is HIGH")
                    time.sleep(2)
                    return 0  # success
                else:
                    self.logger.info("Request to toggle GAIN to LOW")
                    self.serial.write(bytearray([0x61, 0x08]))
                    nl = self.serial.read(2)
                    self.fan_status = False
                    self.logger.info("Gain is Low")
                    time.sleep(2)
                    return 0  # success
            elif T > 20:
                self.logger.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)
   

    def fan_ctrl(self, ctrl_flag=False):
        '''
        opc fan control by sending true to turn it on and false to turn it off
        '''
        T = 0
        while True:
            self.serial.write(bytearray([0x61, 0x03]))
            nl = self.serial.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if ctrl_flag:
                    # fan on
                    self.logger.info("Request Fan to turn ON")
                    self.serial.write(bytearray([0x61, 0x03]))
                    nl = self.serial.read(2)
                    self.fan_status = True
                    self.logger.info("Fan ON")
                    time.sleep(2)
                    return 0  # success
                else:
                    self.logger.info("Request Fan to turn OFF")
                    self.serial.write(bytearray([0x61, 0x02]))
                    nl = self.serial.read(2)
                    self.fan_status = False
                    self.logger.info("Fan OFF")
                    time.sleep(2)
                    return 0  # success
            elif T > 20:
                self.logger.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)

    def interpret_status_data(self, ans):

        status_data = {}
        status_data['Fan_ON'] = True if ans[0]==1 else False
        status_data['LaserDAC_ON'] = True if ans[1]==1 else False
        status_data['FanDACval'] = ans[2]
        status_data['LaserDACval'] = ans[3]
        status_data['LaserSwitch'] = True if ans[4]==1 else False
        status_data['Gain_HIGH'] = True if (ans[5] & 0x1) == 1 else False
        status_data['AutoGain'] = True if (ans[5] & 0x2) == 2 else False
        return status_data
        

    def read_status(self):
        '''
        reading the status of the following parameters - each parameter is 8 bit unsigned
        Fan_ON
        LaserDAC_ON
        FanDACval
        LaserDACval
        LaserSwitch
        Gain and AutoGain Toggle Settings bit0 is Gain (High/Low), bit1 is AutoGain (On/Off)
        '''
        T = 0  # attemt varaible
        while True:
            # self.logger.info("Request status from OPC")

            # request the hist data set
            self.serial.write([0x61, 0x13])
            # time.sleep(wait*10)
            nl = self.serial.read(2)
            T = T + 1
            if nl == (b'\xff\xf3' or b'\xf3\xff'):
                for i in range(6):  # Send bytes one at a time
                    self.serial.write([0x61, 0x01])
                    time.sleep(0.000001)

                time.sleep(wait)  # delay
                ans = bytearray(self.serial.readall())
                ans = self.rightbytes(ans)  # get the wanted data bytes
                data = self.interpret_status_data(ans)
                # self.logger.info("Read all data from the OPC")
                return data
            if T > 20:
                self.logger.info("Reset SPI")
                time.sleep(wait)  # time for spi buffer to reset
                self.init_opc()
                return -999  # error data was not read from the OPC
            else:
                time.sleep(wait * 10)  # wait 1e-05 before next commn

    
    # Lazer on   0x07 is SPI byte following 0x03 to turn laser ON.
    def laz_ctrl(self, laser_flag=False):
        '''
        opc fan control by sending true to turn it on and false to turn it off
        '''

        T = 0  # Triese counter
        while True:
            self.serial.write(bytearray([0x61, 0x03]))
            nl = self.serial.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if laser_flag:
                    # Lazer on
                    self.logger.info("Request laser to turn ON")
                    self.serial.write(bytearray([0x61, 0x07]))
                    nl = self.serial.read(2)
                    time.sleep(wait)
                    self.laser_status = True
                    self.logger.info("Laser is ON")
                    return 0  # 0 error means success
                else:
                    # Lazer off
                    self.logger.info("Request laser to turn OFF")
                    self.serial.write(bytearray([0x61, 0x06]))
                    nl = self.serial.read(2)
                    time.sleep(wait)
                    self.laser_status = False
                    self.logger.info("Laser is OFF")
                    return 0  # 0 error means success
            elif T > 20:
                self.logger.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)  # wait 1e-05 before next commnad

    def rightbytes(self, response):
        '''
        Get ride of the 0x61 byeste responce from the hist data,
        returning just the wanted data
        '''
        hist_response = []
        for j, k in enumerate(response):
            # Each of the 86 bytes we expect to be returned is prefixed
            # by 0xFF.
            if ((j + 1) % 2) == 0:  # Throw away 0th, 2nd, 4th, 6th bytes, etc.
                hist_response.append(k)
        return hist_response

    def RHcon(self, ans):
        '''
        ans is  combine_bytes(ans[52],ans[53])
        '''
        RH = 100 * (ans / (2**16 - 1))
        return RH

    def Tempcon(self, ans):
        '''
        ans is  combine_bytes(ans[52],ans[53])
        '''
        Temp = -45 + 175 * (ans / (2**16 - 1))
        return Temp

    def combine_bytes(self, LSB, MSB):
        return (MSB << 8) | LSB

    def Histdata(self, ans):
        '''
        function to read all the hist data, to break up the getHist
        '''
        # self.logger.info("size of ans: " + str(len(ans)))
        data = {}
        data['Bin0'] = self.combine_bytes(ans[0], ans[1])
        data['Bin1'] = self.combine_bytes(ans[2], ans[3])
        data['Bin2'] = self.combine_bytes(ans[4], ans[5])
        data['Bin3'] = self.combine_bytes(ans[6], ans[7])
        data['Bin4'] = self.combine_bytes(ans[8], ans[9])
        data['Bin5'] = self.combine_bytes(ans[10], ans[11])
        data['Bin6'] = self.combine_bytes(ans[12], ans[13])
        data['Bin7'] = self.combine_bytes(ans[14], ans[15])
        data['Bin8'] = self.combine_bytes(ans[16], ans[17])
        data['Bin9'] = self.combine_bytes(ans[18], ans[19])
        data['Bin10'] = self.combine_bytes(ans[20], ans[21])
        data['Bin11'] = self.combine_bytes(ans[22], ans[23])
        data['Bin12'] = self.combine_bytes(ans[24], ans[25])
        data['Bin13'] = self.combine_bytes(ans[26], ans[27])
        data['Bin14'] = self.combine_bytes(ans[28], ans[29])
        data['Bin15'] = self.combine_bytes(ans[30], ans[31])
        data['Bin16'] = self.combine_bytes(ans[32], ans[33])
        data['Bin17'] = self.combine_bytes(ans[34], ans[35])
        data['Bin18'] = self.combine_bytes(ans[36], ans[37])
        data['Bin19'] = self.combine_bytes(ans[38], ans[39])
        data['Bin20'] = self.combine_bytes(ans[40], ans[41])
        data['Bin21'] = self.combine_bytes(ans[42], ans[43])
        data['Bin22'] = self.combine_bytes(ans[44], ans[45])
        data['Bin23'] = self.combine_bytes(ans[46], ans[47])
        data['bin1MToF'] = ans[48] # MToF is a an 8 bit unigned integer that represents the mean amount of time that particles sized in the stated bin took to cross the OPC laser beam, each value is 1/3 * us
        data['bin3MToF'] = ans[49]
        data['bin5MToF'] = ans[50]
        data['bin7MTof'] = ans[51]
        #data['MTof'] = struct.unpack('f', bytes(
        #    ans[48:52]))[0]  # MTof is in 1/3 us, value of 10=3.33us
        data['period'] = self.combine_bytes(ans[52], ans[53]) # histogram sampling time in 100 * s
        data['FlowRate'] = self.combine_bytes(ans[54], ans[55]) # sample flowrate (SFR) in 100 * ml/s
        data['OPC-T'] = self.Tempcon(self.combine_bytes(ans[56], ans[57])) # temperature in celcius
        data['OPC-RH'] = self.RHcon(self.combine_bytes(ans[58], ans[59])) # relative humidity in percent
        data['pm1'] = struct.unpack('f', bytes(ans[60:64]))[0] # particulate matter in microgram/m^3
        data['pm2.5'] = struct.unpack('f', bytes(ans[64:68]))[0] # particulate matter in microgram/m^3
        data['pm10'] = struct.unpack('f', bytes(ans[68:72]))[0] # particulate matter in microgram/m^3
        data['Check'] = self.combine_bytes(ans[84], ans[85]) # checksum
        data['comm'] = self.comm
        data['laser_status'] = self.combine_bytes(ans[82], ans[83]) # laser status is a 16bit unsigned integer
        data['fan_rev_count'] = self.combine_bytes(ans[80], ans[81]) # fan rev count in a 16 bit unsigned integer

        return (data)

    # get hist data
    def read_data(self):
        """
        Reads data from the OPC

        Returns
        -------
        dict - holding data read from the OPC
        """
        try:
            T = 0  # attemt varaible
            while True:
                # self.logger.info("Request data from OPC")

                # request the hist data set
                self.serial.write([0x61, 0x30])
                # time.sleep(wait*10)
                nl = self.serial.read(2)
                T = T + 1
                if nl == (b'\xff\xf3' or b'\xf3\xff'):
                    for i in range(86):  # Send bytes one at a time
                        self.serial.write([0x61, 0x01])
                        time.sleep(0.000001)

                    time.sleep(wait)  # delay
                    ans = bytearray(self.serial.readall())
                    ans = self.rightbytes(ans)  # get the wanted data bytes
                    data = self.Histdata(ans)
                    # self.logger.info("Read all data from the OPC")
                    return data
                if T > 20:
                    self.logger.info("Reset SPI")
                    time.sleep(wait)  # time for spi buffer to reset
                    self.init_opc()
                    return None  # error data was not read from the OPC
                else:
                    time.sleep(wait * 10)  # wait 1e-05 before next commn\
        except serial.SerialException:
                self.serial_failure()
                return None


    
    
    





    



    








    
    
    






