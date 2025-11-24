#!/usr/bin/env python3
import usb.core
import usb.util

print("=== Manual USB Access Test ===")

# OceanSR6 specific vendor/product ID
VENDOR_ID = 0x0999
PRODUCT_ID = 0x1005

# Find the device
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    print("✗ USB device not found with pyusb")
else:
    print("✓ USB device found with pyusb!")
    print(f"  Device: {dev}")
    print(f"  Manufacturer: {dev.manufacturer}")
    print(f"  Product: {dev.product}")
    
    # Try to set configuration
    try:
        dev.set_configuration()
        print("✓ Configuration set successfully")
        
        # Try to read a descriptor
        cfg = dev.get_active_configuration()
        print(f"✓ Active configuration: {cfg}")
        
    except usb.core.USBError as e:
        print(f"✗ USB Error: {e}")
        print("This is a permission/access issue")