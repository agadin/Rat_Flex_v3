import multiprocessing.shared_memory as shared_memory
import multiprocessing
import numpy as np
from Wavshare_stepper_code.DRV8825 import DRV8825, setup_gpio
import time
import os
import json
from database_websocket_client import DatabaseWebSocketClient
import redis
from force_sensor import ForceSensor
import struct
import multiprocessing.shared_memory as sm
import mmap
import os
import csv


#what if I run DRV8825.py and force_sensor.py in their own thread? maybe make two different modes?


class StepperMotor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StepperMotor, cls).__new__(cls)
        return cls._instance

    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt', csv_name='data.csv'):
        self.target_force = None
        self.step_number = None
        self.current_run_data = None
        self.current_force = None
        if not hasattr(self, 'initialized'):  # Ensure __init__ is only called once
            self.dir_pin = dir_pin
            self.step_pin = step_pin
            self.enable_pin = enable_pin
            self.mode_pins = mode_pins
            self.limit_switch_1 = limit_switch_1
            self.limit_switch_2 = limit_switch_2
            self.step_type = step_type
            self.stepdelay = stepdelay
            self.initialized = True
            self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins,
                                 limit_pins=(self.limit_switch_1, self.limit_switch_2))

        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.steps_per_revolution = None
        self.step_to_angle_ratio = None
        self.current_angle = 0
        self.calibration_file = calibration_file
        self.step_type = step_type
        self.stepdelay = stepdelay
        self.current_state = "idle"
        self.current_direction = "idle"
        self.motor.SetMicroStep('software', self.step_type)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.ForceSensor = ForceSensor()
        self.csv_name = csv_name
        self.shm = None
        shm_name = 'shared_data'
        self.fmt = 'i d d d'
        self.shm_size = struct.calcsize(self.fmt)

        # Attach to the existing shared memory
        # Create a memory-mapped file
        self.shm_file = "shared_memory.dat"
        with open(self.shm_file, "wb") as f:
            f.write(b'\x00' * self.shm_size)

        shm_name = 'shared_data'
          # Format for unpacking (stop_flag, step_count, current_angle, current_force)

        # Attach to the existing shared memory
        self.create_shared_memory()



    def create_shared_memory(self):
        try:
            if hasattr(self, 'shm') and self.shm is not None:
                self.shm.close()
                self.shm.unlink()
        except Exception as e:
            print(f"Error: {e}")

        shm_name = 'shared_data'
        shm_size = struct.calcsize('i d d d')  # 4 bytes for int, 3 doubles (8 bytes each)
        self.shm = sm.SharedMemory(create=True, name=shm_name, size=shm_size)

    def load_calibration(self):
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as file:
                for line in file:
                    key, value = line.strip().split(': ')
                    if key == 'steps_per_revolution':
                        self.steps_per_revolution = int(value)
                    elif key == 'step_to_angle_ratio':
                        self.step_to_angle_ratio = float(value)
                    else:
                        self.steps_per_revolution = None
                        self.step_to_angle_ratio = None

        else:
            print(f"Calibration file {self.calibration_file} not found. Please run calibrate() first.")

    def read_first_value_in_last_row(self, save_csv=None):
        if save_csv is None:
            save_csv= self.csv_name
        with open(save_csv, 'r', newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            rows = list(csvreader)
            if rows:
                last_row = rows[-1]
                if last_row:
                    return float(last_row[0])
        return float(0)

    def current_protocol_step(self, step_number):
        self.step_number = step_number

    def return_current_protocol_step(self):
        return self.step_number

    def angle_force_calibration(self, target, direction):
        with open(self.calibration_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            # Variables to track the closest match
            closest_angle = None
            closest_force = None
            min_angle_diff = float('inf')

            for row in reader:
                # Ensure the row direction matches the specified direction
                if row['direction'] == direction:
                    angle = float(row['angle'])
                    force = float(row['force'])
                    angle_diff = abs(angle - target)

                    # Update the closest match if the angle difference is smaller
                    if angle_diff < min_angle_diff:
                        min_angle_diff = angle_diff
                        closest_angle = angle
                        closest_force = force

            # Return the closest force
            if closest_angle is not None:
                return closest_force
            else:
                raise ValueError(f"No matching data found for direction '{direction}'.")


    def calibrate(self):
        self.current_direction = 'calibrating'
        self.current_state = 'calibrating'
        self.current_angle = 0
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
        while self.motor.limit_switch_1_state:
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)

        steps = 0
        while self.motor.limit_switch_2_state:
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)
            steps += 1

        self.steps_per_revolution = steps
        self.step_to_angle_ratio = steps / 180

        if not os.path.exists(self.calibration_file) or os.stat(self.calibration_file).st_size == 0:
            with open(self.calibration_file, 'w') as file:
                # Write the header to the file
                file.write("time,angle,force,state,direction,step\n")

        # zero out force at each angle
        self.move_to_angle(170, 'calibrate')
        time.sleep(0.5)
        self.move_to_angle(10, 'calibrate')

        self.redis_client.set("current_direction", "idle")
        self.redis_client.set("step_to_angle_ratio", self.step_to_angle_ratio)

        self.move_to_angle(90)

    def move_to_angle(self, angle, target_file=None):
        if self.step_to_angle_ratio is None:
            raise Exception("Motor not calibrated. Please run calibrate() first.")
        if target_file is not None:
            save_csv=self.calibration_file
        else:
            save_csv= self.csv_name

        self.current_state = "moving"
        self.current_direction = "forward" if angle > self.current_angle else "backward"

        steps = int(abs(angle - self.current_angle) * self.step_to_angle_ratio)
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

        counter = 0
        angle_increment = 1 / self.step_to_angle_ratio
        angle_increment = angle_increment if self.current_direction == 'forward' else -angle_increment
        batch_size = 100
        fmt = self.fmt
        total_time = 0
        iterations = steps
        stop_flag = 0
        temp_data = []
        data = bytes(self.shm.buf[:struct.calcsize(self.fmt)])
        for i in range(steps):
            # start_time = time.time()
            stop_flag, temp1, temp2, temp3 = struct.unpack(self.fmt, data)
            if stop_flag == 1:
                self.redis_client.set("current_state", "idle")
                self.redis_client.set("current_direction", "idle")
                self.redis_client.set("stop_flag", 0)
                stop_flag = 0
                print("Stopping motor button")
                break
            self.motor.TurnStep(Dir=self.current_direction, steps=1, stepdelay=self.stepdelay)
            self.current_angle += angle_increment
            self.current_force= self.ForceSensor.read_force()
            try:
                # Pack the data
                #packed_data = struct.pack(self.fmt, stop_flag, i, self.current_angle, float(self.ForceSensor.read_force()))

                # Write packed data to the memory-mapped file
                #self.mm.seek(0)
                # self.mm.write(packed_data)
                temp_data.append([i, self.current_angle, float(self.current_force)])
                packed_data = struct.pack(self.fmt, stop_flag, i, self.current_angle, float(self.current_force))

                # Write packed data to shared memory
                self.shm.buf[:len(packed_data)] = packed_data
            except Exception as e:
                print(f"Error: {e}")


            # end_time = time.time()
            # total_time += (end_time - start_time)

        # After all data has been appended, update the first column with time values
        start_time = self.read_first_value_in_last_row(save_csv)
        current_time = float(start_time)
        for row in temp_data:
            row[0] = current_time
            current_time += 0.03

        # Add two columns to the end of temp_data filled with current_state and current_direction
        for row in temp_data:
            row.append(self.current_state)
            row.append(self.current_direction)
            row.append(self.step_number)

        with open(save_csv, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write the data
            csvwriter.writerows(temp_data)
        self.current_run_data= temp_data
        
        
        # average_time = total_time / iterations
        # self.redis_client.set("average_time", average_time)
        self.current_state = "idle"
        self.current_direction = "idle"
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

    def move_until_force(self, direction, target_force, angle_limit_min=0, angle_limit_max=180):
        temp_data = []
        if direction not in [0, 180]:
            raise ValueError("Direction must be either 0 or 180 degrees")

        self.current_direction = 'backward' if direction == 0 else 'forward'
        self.current_state = "moving"
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

        angle_increment = 1 / self.step_to_angle_ratio
        angle_increment = angle_increment if self.current_direction == 'forward' else -angle_increment
        data = bytes(self.shm.buf[:struct.calcsize(self.fmt)])
        self.target_force = float(target_force)
        i=0
        while True:
            i += 1
            stop_flag, temp1, temp2, temp3 = struct.unpack(self.fmt, data)
            if stop_flag == 1:
                self.redis_client.set("current_state", "idle")
                self.redis_client.set("current_direction", "idle")
                self.redis_client.set("stop_flag", 0)
                print("Stopping motor button")
                break
            self.motor.TurnStep(Dir=self.current_direction, steps=1, stepdelay=self.stepdelay)
            self.current_angle += angle_increment
            self.current_force = float(self.ForceSensor.read_force())
            try:
                # Pack the data
                # packed_data = struct.pack(self.fmt, stop_flag, i, self.current_angle, float(self.ForceSensor.read_force()))

                # Write packed data to the memory-mapped file
                # self.mm.seek(0)
                # self.mm.write(packed_data)
                temp_data.append([i, self.current_angle, float(self.current_force)])
                packed_data = struct.pack(self.fmt, stop_flag, i, self.current_angle, float(self.current_force))

                # Write packed data to shared memory
                self.shm.buf[:len(packed_data)] = packed_data
            except Exception as e:
                print(f"Error: {e}")

            if i > 10 and \
                    abs(self.current_force) >= self.target_force and \
                    ((self.current_direction == 'backward' and self.current_force < 0) or
                     (self.current_direction == 'forward' and self.current_force > 0)) and \
                    (self.current_angle <= angle_limit_min and self.current_direction == 'backward') and \
                    (self.current_angle >= angle_limit_max and self.current_direction == 'forward'):
                break

        self.current_state = "idle"
        self.current_direction = "idle"
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

    def return_force(self):
        return self.ForceSensor.read_force()

    def cleanup(self):
        self.motor.Stop()
        self.motor.cleanup()
        self.shm.close()
        self.shm.unlink()

    def stop(self):
        self.motor.Stop()
        self.current_state = "idle"
        self.current_direction = "idle"
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)