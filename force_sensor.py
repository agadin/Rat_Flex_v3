# force_sensor.py
import serial

class ForceSensor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.open_connection()

    def open_connection(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Opened Port {self.port}")
        except Exception as e:
            print(f"Could not open Port {self.port}")
            print(e)
            self.ser = None

    def read_force(self):
        if self.ser:
            try:
                self.ser.write(b'W\r')
                response = self.ser.readline().decode('utf-8').strip()
                force_out=float(response)-1 #add idle calibration value
                return force_out
            except Exception as e:
                print(f"Error reading from Port {self.port}")
                print(e)
                return None
        else:
            print("Serial connection not open")
            return None

    def close_connection(self):
        if self.ser:
            self.ser.close()
            print(f"Closed Port {self.port}")

import time


def test_force_sensor():
    # from force_sensor import ForceSensor
    sensor = ForceSensor('/dev/ttyUSB0')  # Adjust the port if necessary
    sensor.open_connection()

    try:
        while True:
            force_value = sensor.read_force()
            if force_value is not None:
                print(f"Force Value: {force_value}")
            else:
                print("Failed to read force value")
            time.sleep(1)  # Wait for 1 second before reading again
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        sensor.close_connection()

if __name__ == '__main__':
    test_force_sensor()