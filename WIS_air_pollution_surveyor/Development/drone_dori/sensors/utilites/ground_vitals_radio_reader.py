import pickle
import serial
import csv
import time
import sys

CNT_NO_DATA = 0
LIMIT_NO_DATA = 10

def write_to_csv(data, filePath):
    print(data)
    with open(filePath, 'a+', newline='') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([data])
    print(f'Received and saved: {data}')

def main():   
    if len(sys.argv) != 3:
        print("Usage: python ground_vitals_radio_reader.py <path_to_csv> <number_com>")
        sys.exit(1)

    filePath = sys.argv[1]
    # Set up the serial connection
    global CNT_NO_DATA
    global LIMIT_NO_DATA
    ser = serial.Serial('COM11', 9600, timeout=1)
    ser.flush()

    try:
        while True:
            if not ser:
                ser = serial.Serial('COM11', 9600, timeout=1)
                ser.flush()
            if ser.in_waiting > 0:
                data = b""
                data += ser.read(ser.inWaiting())
                while ser.in_waiting > 0:
                    data += ser.read(ser.inWaiting())

                try:
                    dict = pickle.loads(data)
                    line = str(dict)

                    # Check if the line is not empty before writing to the CSV
                    if line:
                        write_to_csv(line, filePath)
                    else:
                        print('Received empty data. Nothing saved.')
                except (pickle.UnpicklingError, EOFError):
                    print("Got curropted data, couldn't pickle bytes.")

            else:
                CNT_NO_DATA += 1
                if CNT_NO_DATA > LIMIT_NO_DATA:
                    ser.flush()
                    ser = None
                    CNT_NO_DATA = 0
                print("Didn't receive data, sleeping")
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted. Closing serial connection and exiting.")
        ser.close()

if __name__ == "__main__":
    main()
