# force_sensor.py
import serial

class ForceSensor:
    def __init__(self, port='/dev/ttyS0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

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
                return response
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

# Example usage:
# sensor = ForceSensor('COM3')
# sensor.open_connection()
# print(sensor.read_force())
# sensor.close_connection()