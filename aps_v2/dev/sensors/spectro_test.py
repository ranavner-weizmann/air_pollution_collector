import seabreeze.spectrometers as sb
import matplotlib.pyplot as plt

# List connected devices
devices = sb.list_devices()
print(f'devices found: {devices}')


if not devices:
    raise RuntimeError("No spectrometer found!")

# Use the first one found

spec = sb.Spectrometer(devices[0])

# Read wavelengths and intensities
wavelengths = spec.wavelengths()
intensities = spec.intensities()

# Plot the spectrum
plt.figure(figsize=(8, 5))
plt.plot(wavelengths, intensities)
plt.title("Spectrometer Reading")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Intensity (counts)")
plt.grid(True)
plt.show()

# Close connection
spec.close()