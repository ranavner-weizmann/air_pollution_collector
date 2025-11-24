import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer, list_devices

print("=== Ocean Optics Spectrometer ===")

# List available devices
devices = list_devices()
print(f"Found {len(devices)} devices")

if not devices:
    print("No spectrometers found. Please check:")
    print("1. Is the spectrometer connected?")
    print("2. Try running with: sudo python spectro.py")
    print("3. Install pyusb: pip install pyusb")
    exit()

# Connect to the first available device
try:
    spec = Spectrometer(devices[0])
    print(f"✓ Connected to: {spec.model}")
    print(f"  Serial number: {spec.serial_number}")
    
    # Get device capabilities
    print(f"  Min integration time: {spec.min_integration_time_micros} μs")
    print(f"  Max integration time: {spec.max_integration_time_micros} μs")
    
    # Set integration time (100ms)
    integration_time = 100000
    spec.integration_time_micros(integration_time)
    print(f"  Integration time set to: {integration_time} μs")
    
    # Get wavelengths (fixed for the device)
    wavelengths = spec.wavelengths()
    print(f"  Wavelength range: {wavelengths[0]:.1f} - {wavelengths[-1]:.1f} nm")
    print(f"  Number of pixels: {len(wavelengths)}")
    
    # Take a measurement
    print("\nTaking measurement...")
    intensities = spec.intensities()
    
    # Basic analysis
    max_intensity = max(intensities)
    max_idx = intensities.argmax()
    peak_wavelength = wavelengths[max_idx]
    
    print(f"✓ Measurement successful!")
    print(f"  Maximum intensity: {max_intensity:.2f}")
    print(f"  Peak wavelength: {peak_wavelength:.2f} nm")
    
    # Show sample data
    print("\nSample data (first 10 points):")
    for i in range(min(10, len(wavelengths))):
        print(f"  {wavelengths[i]:.1f} nm: {intensities[i]:.2f}")
    
    # Close the device
    spec.close()
    print("\n✓ Spectrometer closed properly")
    
except Exception as e:
    print(f"✗ Error: {e}")