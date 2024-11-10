# stepper_motor.py
import RPi.GPIO as GPIO
import time
from DRV8825 import DRV8825, setup_gpio

import os

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015,  calibration_file='calibration.txt'):
        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins, limit_pins= (self.limit_switch_1 , self.limit_switch_2))
        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.calibration_file = calibration_file
        self.step_type = step_type
        self.stepdelay= stepdelay
        self.motor.SetMicroStep('softward', self.step_type)

        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

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
        # Rotate clockwise until the first limit switch is pressed
        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
        while GPIO.input(self.limit_switch_1):
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)

        # Rotate counter-clockwise until the second limit switch is pressed
        steps = 0
        while GPIO.input(self.limit_switch_2):
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=self.stepdelay)
            steps += 1

        self.steps_per_revolution = steps
        self.angle_to_step_ratio = steps / 180.0

        # Save calibration data to file
        with open(self.calibration_file, 'w') as file:
            file.write(f"steps_per_revolution: {self.steps_per_revolution}\n")
            file.write(f"angle_to_step_ratio: {self.angle_to_step_ratio}\n")

        # Move to 90 degrees
        self.move_to_angle(90)

    def move_to_angle(self, angle):
        if self.angle_to_step_ratio is None:
            self.angle_to_step_ratio = 1.0
            #raise Exception("Motor not calibrated. Please run calibrate() first.")

        steps = int(angle * self.angle_to_step_ratio)
        self.motor.TurnStep(Dir='forward', steps=steps, stepdelay=0.0015)

    def cleanup(self):
        self.motor.Stop()
        GPIO.cleanup()

    def stop(self):
        self.motor.Stop()


class SimpleStepperMotorController:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_pins):
        self.limit_switch_1 = limit_pins[0]
        self.limit_switch_2 = limit_pins[1]
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins, limit_pins= (self.limit_switch_1 , self.limit_switch_2))
        self.motor.SetMicroStep('softward', 'fullstep')

    def move_forward(self, steps=200, stepdelay=0.0015):
        self.motor.TurnStep(Dir='forward', steps=steps, stepdelay=stepdelay)
        time.sleep(0.5)

    def stop(self):
        self.motor.Stop()

def main():
    try:
        motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6)
        motor.calibrate()
        motor.move_to_angle(200)  # Move to 200 degrees
    finally:
        motor.stop()
        motor.cleanup()


if __name__ == '__main__':
    #controller = SimpleStepperMotorController(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_pins=(5, 6))
    # controller.move_forward()
    #controller.stop()
    main()


# main.py
# from stepper_motor import StepperMotor

# def main():
#    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6)
 #   motor.calibrate()
  #  motor.move_to_angle(45)  # Example: move to 45 degrees
   # motor.cleanup()

#if __name__ == '__main__':
 #   main()
