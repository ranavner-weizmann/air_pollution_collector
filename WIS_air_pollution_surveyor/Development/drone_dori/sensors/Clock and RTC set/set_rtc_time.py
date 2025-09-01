import subprocess
import sys


def main(args):
    if len(args) != 3:
        print("Usage {args[0]} <fqbn of the ardunio> <arduino + rtc dev file>")
    
    fqbn = args[1]
    port = args[2]


    output = subprocess.run(["arduino-cli", "-h"], capture_output=True, text=True, shell=True)
    assert ("not found" not in output.stdout), "arduino-cli not installed. Needed for compilation"
    
    output = subprocess.run(f"arduino-cli compile --fqbn {fqbn} ./setRTC", capture_output = True, text=True, shell=True)
    assert("Error" not in output.stdout), "Compilation failed"
    print("Compilation done")


    output = subprocess.run(f"arduino-cli upload -p {port} --fqbn {fqbn} ./setRTC", capture_output=True, text=True, shell=True)
    print(output.returncode)
    assert("Error" not in output.stdout), "Upload failed"
    print("Upload done")



if __name__ == '__main__':
    main(sys.argv)