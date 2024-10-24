# test_force_sensor.py
import time
from force_sensor import ForceSensor

def test_force_sensor():
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