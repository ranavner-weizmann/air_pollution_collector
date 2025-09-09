# run.py — run the POM sensor and stream data to a CSV

import argparse
import csv
import os
import signal
import sys
import logging
import time
from datetime import datetime, timezone

from sensors.pom import Pom
from sensors.sensor import Sensor


# add sensors/ folder to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENSORS_DIR = os.path.join(BASE_DIR, "sensors")
sys.path.append(SENSORS_DIR)

RUNNING = True
LOG_FORMAT = "%(asctime)s %(filename)s: %(message)s"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def on_signal(signum, frame):
    global RUNNING
    RUNNING = False

def main():
    parser = argparse.ArgumentParser(description="Run POM and log to CSV")
    parser.add_argument("--demo", action="store_true", help="use Pom demo mode")
    parser.add_argument("--outdir", default="./logs", help="folder for CSV + log files")
    args = parser.parse_args()

    # prepare logging folder with run start timestamp
    os.makedirs(args.outdir, exist_ok=True)
    run_stamp = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    logging_folder = os.path.realpath(os.path.join(args.outdir, f"logs_{run_stamp}"))
    os.makedirs(logging_folder, exist_ok=True)

    # path for main log
    main_log_path = os.path.join(logging_folder, f"main_log_{run_stamp}.txt")

    # create the txt config file that Sensor expects
    cfg_path = os.path.join(SENSORS_DIR, "main_log_path.txt")
    with open(cfg_path, "w") as f:
        f.write(main_log_path + "\n")
        f.write(LOG_FORMAT)

    # configure logging
    logging.basicConfig(filename=main_log_path, format=LOG_FORMAT, level=logging.INFO)
    logging.info("Starting run.py")

    # prepare CSV
    csv_path = os.path.join(logging_folder, f"pom_{run_stamp}.csv")
    fieldnames = ["timestamp", *Pom.PV_NAMES, "num_samples"]
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader(); csv_file.flush()

    # create sensor instance
    sensor = Pom(
        name="pom",
        location="drone",
        device_name="pom",
        demo_mode=args.demo,
        is_device=False,           # no EPICS for standalone run
        sampling_time=1.0,
        vitality_cooldown=0.1,
        to_avarage=True,
    )

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    try:
        while RUNNING:
            data = sensor.request_data()
            if data:
                row = {"timestamp": utc_now()}
                for k in Pom.PV_NAMES:
                    row[k] = data.get(k, "")
                row["num_samples"] = data.get("num_samples", "")
                writer.writerow(row)
                csv_file.flush()
            time.sleep(sensor.vitality_cooldown)
    finally:
        sensor.close()
        csv_file.close()
        print(f"CSV written to: {csv_path}")
        print(f"Main log: {main_log_path}")

if __name__ == "__main__":
    main()
