#!/usr/bin/env python3
import usb.core
import usb.util
import time
import struct

print("=== OceanSR6 Bulk Endpoint Communication ===")

VENDOR_ID = 0x0999
PRODUCT_ID = 0x1005

# Find device
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    print("Device not found")
    exit()

print(f"Found: {dev.manufacturer} - {dev.product} (Serial: {dev.serial_number})")

try:
    # Detach kernel driver if needed
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
        print("Detached kernel driver")
    
    # Set configuration
    dev.set_configuration()
    print("Configuration set")
    
    # We have 4 bulk endpoints:
    # EP 0x01 OUT - Send commands
    # EP 0x81 IN  - Receive data  
    # EP 0x02 OUT - Send commands
    # EP 0x82 IN  - Receive data
    
    print("\nTesting bulk endpoints...")
    
    # Try common Ocean Optics commands
    commands = [
        b'\x01',  # Get serial number
        b'\x02',  # Get spectrum
        b'\x03',  # Set integration time
        b'\x04',  # Get integration time
        b'\xFE\x00',  # Request spectrum (legacy)
        b'\x09',  # Get device info
    ]
    
    for cmd in commands:
        print(f"\nTrying command: {cmd.hex()}")
        
        # Try sending to both OUT endpoints
        for ep_out in [0x01, 0x02]:
            try:
                print(f"  Sending to EP 0x{ep_out:02x}...")
                written = dev.write(ep_out, cmd, timeout=1000)
                print(f"    Sent {written} bytes")
                
                # Try receiving from both IN endpoints
                for ep_in in [0x81, 0x82]:
                    try:
                        print(f"    Reading from EP 0x{ep_in:02x}...")
                        data = dev.read(ep_in, 512, timeout=1000)
                        if data:
                            print(f"      Received {len(data)} bytes: {data[:20]}...")
                            break
                    except usb.core.USBError as e:
                        print(f"      Read failed: {e}")
                
            except usb.core.USBError as e:
                print(f"    Write failed: {e}")
    
except Exception as e:
    print(f"Error: {e}")