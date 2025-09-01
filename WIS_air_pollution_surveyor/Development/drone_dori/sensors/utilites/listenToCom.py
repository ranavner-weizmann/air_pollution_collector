import serial
import csv

def read_from_serial(port, baud_rate=115200):
    ser = serial.Serial(port, baud_rate)
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                yield line
    except KeyboardInterrupt:
        ser.close()

def main():
    com_port = "COM14"  # Change this to your COM port
    output_file = "serial_data.csv"

    with open(output_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Timestamp", "Data"])  # Writing header

        for data_line in read_from_serial(com_port):
            # Assuming the data has a timestamp or any identifier in the beginning
            csv_writer.writerow([data_line])

if __name__ == "__main__":
    main()
