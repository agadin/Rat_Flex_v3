import multiprocessing.shared_memory as shared_memory
import multiprocessing
import numpy as np
from Wavshare_stepper_code.DRV8825 import DRV8825, setup_gpio
import RPi.GPIO as GPIO
import time
import os
import json
from database_websocket_client import DatabaseWebSocketClient
import redis
from force_sensor import ForceSensor
import struct
import multiprocessing.shared_memory as sm


class StepperMotor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StepperMotor, cls).__new__(cls)
        return cls._instance

    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt'):
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

        GPIO.setmode(GPIO.BCM)
        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

        # Initialize shared memory
        shm_size = struct.calcsize('i d d d')
        self.smh = sm.SharedMemory(create=True, name='test', size=shm_size)

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
            print(f"Calibration file {self.calibration_file} not found. Please run calibrate() first.")

    def calibrate(self):
        self.current_direction = 'calibrating'
        self.current_state = 'calibrating'
        self.redis_client.set("current_state", self.current_direction)
        self.redis_client.set("current_direction", self.current_state)

        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
        while GPIO.input(self.limit_switch_1):
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)

        steps = 0
        while GPIO.input(self.limit_switch_2):
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)
            steps += 1

        self.steps_per_revolution = steps
        self.step_to_angle_ratio = steps / 180

        with open(self.calibration_file, 'w') as file:
            file.write(f"steps_per_revolution: {self.steps_per_revolution}\n")
            file.write(f"step_to_angle_ratio: {self.step_to_angle_ratio}\n")

        self.redis_client.set("current_direction", "idle")
        self.redis_client.set("step_to_angle_ratio", self.step_to_angle_ratio)
        self.move_to_angle(90)

    def move_to_angle(self, angle):
        if self.step_to_angle_ratio is None:
            raise Exception("Motor not calibrated. Please run calibrate() first.")

        self.current_state = "moving"
        self.current_direction = "forward" if angle > self.current_angle else "backward"

        steps = int(abs(angle - self.current_angle) * self.step_to_angle_ratio)
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

        counter = 0
        angle_increment = 1 / self.step_to_angle_ratio
        angle_increment = angle_increment if self.current_direction == 'forward' else -angle_increment
        batch_size = 100
        fmt = 'i d d d'
        for i in range(steps):
            self.motor.TurnStep(Dir=self.current_direction, steps=1, stepdelay=self.stepdelay)
            self.current_angle += angle_increment


            stop_flag = 0
            packed_data = struct.pack(fmt, stop_flag, i, self.current_angle, float(self.ForceSensor.read_force()))

            # Write packed data to shared memory
            self.smh.buf[:len(packed_data)] = packed_data

        self.current_state = "idle"
        self.current_direction = "idle"
        self.redis_client.set("current_state", self.current_state)
        self.redis_client.set("current_direction", self.current_direction)

    def cleanup(self):
        self.motor.Stop()
        GPIO.cleanup()
        self.shm.close()
        self.shm.unlink()

    def stop(self):
        self.motor.Stop()
        self.update_db(motor_state='stopped', current_direction='idle')