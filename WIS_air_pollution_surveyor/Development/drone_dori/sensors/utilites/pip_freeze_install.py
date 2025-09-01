import subprocess
import os

# Path to your virtual environment's activate script
venv_activate_script = '/home/pi/evia/venv/bin/activate'  # Replace with your venv path

# Path to your requirements.txt file
requirements_file = '/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/pip/requirements.txt'

# Activate the virtual environment
# activate_command = f'source {venv_activate_script}'
# subprocess.run(activate_command, shell=True, check=True)

# Read the requirements.txt file and parse package names and versions
with open(requirements_file, 'r') as file:
    lines = file.readlines()

for line in lines:
    # Remove any leading/trailing whitespace and split by '=='
    parts = line.strip().split('==')
    if len(parts) == 2:
        package_name, package_version = parts
        # Install the package with the specified version in the activated venv
        install_command = f'pip install {package_name}=={package_version}'
        subprocess.run(install_command, shell=True)
        print(f"Installed: {package_name}=={package_version}")
    else:
        print(f"Skipping invalid line: {line.strip()}")

# Deactivate the virtual environment when done
deactivate_command = 'deactivate'
subprocess.run(deactivate_command, shell=True, check=True)
