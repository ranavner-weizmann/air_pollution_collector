import pyudev
device_list = pyudev.Context().list_devices()
for device in device_list.match_subsystem("tty"):
    device_vendor = device.get("ID_VENDOR_ID")
    device_model = device.get("ID_MODEL_ID")
    device_serial = device.get("ID_SERIAL")
    print(device_vendor, device_model, device_serial)