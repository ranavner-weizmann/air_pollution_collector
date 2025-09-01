#!/bin/python3
from os import chdir
import re
import argparse


"""
Parses pv names from ../db folder

"""


import os
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db_folder", help="db folder path")
    parser.add_argument("device_name", help="device name")
    args = parser.parse_args()
    device_name = args.device_name

    db_path = os.path.join(args.db_folder, device_name + ".db")
    try:
        with open(db_path) as f:
            pv_list = []
            pattern = re.compile(rf"\"{device_name}:(.*)\"")
            for line in f.readlines():
                pv_name = pattern.search(line)
                if pv_name:
                    pv_list.append(pv_name[1])
            print(pv_list)
    except FileNotFoundError:
        print(f"Device <{device_name}> wasn't found")


