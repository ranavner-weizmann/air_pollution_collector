import serial
import time
import serial.tools.list_ports
import subprocess
import os

def list_serial_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
    return [port.device for port in ports]

def reset_usb():
    """Try to reset USB devices"""
    try:
        print("Attempting USB reset...")
        # List USB devices
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        print("USB devices:")
        print(result.stdout)
        
        # Try to reset using usb_modeswitch if available
        subprocess.run(['sudo', 'usb_modeswitch', '-v', '0x1234', '-p', '0x5678', '-R'], 
                      capture_output=True)
        time.sleep(3)
    except Exception as e:
        print(f"USB reset failed: {e}")

def try_serial_connection(port, baudrate):
    """Try to connect with minimal settings"""
    try:
        print(f"Trying {port} at {baudrate} baud...")
        
        # Minimal serial connection - no DTR/RTS control
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2,
            write_timeout=2,
            # Disable all flow control
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        )
        
        print(f"Connected to {port}!")
        
        # Don't send any data initially - just listen
        time.sleep(1)
        
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"Received: {data}")
        else:
            print("No initial data received")
            
        ser.close()
        return True
        
    except Exception as e:
        print(f"Failed: {e}")
        return False

# Main debug sequence
print("=== POM Serial Debugger ===")

# List ports before any connection
print("\n1. Initial port scan:")
ports = list_serial_ports()

if not ports:
    print("No serial ports found!")
    exit(1)

# Try each available port
baud_rates = [9600, 19200, 38400, 57600, 115200]

for port in ports:
    print(f"\n--- Testing {port} ---")
    
    for baud in baud_rates:
        if try_serial_connection(port, baud):
            print(f"SUCCESS: {port} works at {baud} baud!")
            break
        else:
            # List ports again to see if device disappeared
            current_ports = list_serial_ports()
            if port not in current_ports:
                print(f"WARNING: {port} disappeared after connection attempt!")
                reset_usb()
                time.sleep(5)
                break
    else:
        print(f"All baud rates failed for {port}")

print("\nDebugging complete.")