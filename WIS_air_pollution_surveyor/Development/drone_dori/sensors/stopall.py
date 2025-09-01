#!/home/pi/evia/venv/bin/python
import sys
import psutil

def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
    except psutil.NoSuchProcess:
        print("No process found with PID:", pid)
    

    with open("/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/is_on.txt", "w") as f:
        f.write("Off")
    with open("/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/boot_log.txt", "a") as f:
        f.write("Terminating ./runall and writing off to is_on.txt")
    
    print("Finished")

def main():
    if len(sys.argv) != 2:
        print("Usage: python stopall.py <PID>")
        sys.exit(1)

    pid = int(sys.argv[1])
    kill_process_tree(pid)

if __name__ == "__main__":
    main()
