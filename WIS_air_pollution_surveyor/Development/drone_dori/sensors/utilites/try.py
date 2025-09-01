## Sending RST to serial port connection
import serial

def send_rst(serial_port):
    # Open the serial port
    ser = serial.Serial(serial_port)

    # Set the DTR state to send RST
    ser.setDTR(False)  # Set DTR to low
    ser.setDTR(True)   # Set DTR to high

    # Close the serial port
    ser.close()

# Specify the serial port you want to use
serial_port = '/dev/ttyACM0'  # Replace with the appropriate port for your system

# Call the function to send the RST signal
send_rst(serial_port)





