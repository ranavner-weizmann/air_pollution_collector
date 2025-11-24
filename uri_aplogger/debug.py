
import serial

ser = serial.Serial(
        port='/dev/ttyUSB0',  # Update to correct port
        baudrate=19200,       
        parity=serial.PARITY_NONE,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
print("Serial connected")

while True:
    line = ser.readline()
    if line:
        print(line.decode('utf-8').strip())