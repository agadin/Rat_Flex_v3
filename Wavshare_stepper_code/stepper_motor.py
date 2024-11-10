import RPi.GPIO as GPIO
import time
from DRV8825 import DRV8825, setup_gpio
import os
import threading

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt'):
        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins, limit_pins=(self.limit_switch_1, self.limit_switch_2))
        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.calibration_file = calibration_file
        self.step_type = step_type
        self.stepdelay = stepdelay
        self.motor.SetMicroStep('softward', self.step_type)

        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

        # Initialize current angle
        self.current_angle = 0
        self._lock = threading.Lock()  # To safely update the current angle

    def load_calibration(self):
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as file:
                for line in file:
                    key, value = line.strip().split(': ')
                    if key == 'steps_per_revolution':
                        self.steps_per_revolution = int(value)
                    elif key == 'angle_to_step_ratio':
                        self.angle_to_step_ratio = float(value)
        else:
            print(f"Calibration file {self.calibration_file} not found. Please run calibrate() first.")

    def calibrate(self):
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
        self.angle_to_step_ratio = steps / 180.0

        with open(self.calibration_file, 'w') as file:
            file.write(f"steps_per_revolution: {self.steps_per_revolution}\n")
            file.write(f"angle_to_step_ratio: {self.angle_to_step_ratio}\n")


    def _update_angle(self, direction):
        """Updates the current angle based on a single step."""
        with self._lock:
            angle_change = 1 / self.angle_to_step_ratio
            if direction == 'forward':
                self.current_angle += angle_change
            else:
                self.current_angle -= angle_change

    def move_to_angle(self, target_angle):
        if self.angle_to_step_ratio is None:
            raise Exception("Motor not calibrated. Please run calibrate() first.")

        target_steps = int(target_angle * self.angle_to_step_ratio)
        current_steps = int(self.current_angle * self.angle_to_step_ratio)
        steps_to_move = abs(target_steps - current_steps)
        direction = 'forward' if target_steps > current_steps else 'backward'

        # Move one step at a time and update the current angle
        for _ in range(steps_to_move):
            self.motor.TurnStep(Dir=direction, steps=1, stepdelay=self.stepdelay)
            self._update_angle(direction)
            time.sleep(self.stepdelay)

    def get_current_angle(self):
        """Returns the current angle of the motor."""
        with self._lock:
            return self.current_angle

    def cleanup(self):
        self.motor.Stop()
        GPIO.cleanup()

    def stop(self):
        self.motor.Stop()


def main():
    try:
        motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6, step_type='fullstep', stepdelay=0.003)
        motor.calibrate()
        motor.move_to_angle(90)

        # Print current angle in a loop (for demonstration)
        while True:
            print(f"Current angle: {motor.get_current_angle()}")
            time.sleep(0.1)

    finally:
        motor.stop()
        motor.cleanup()


if __name__ == '__main__':
    main()
