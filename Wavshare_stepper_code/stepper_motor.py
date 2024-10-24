# stepper_motor.py
import RPi.GPIO as GPIO
import time
from DRV8825 import DRV8825

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, calibration_file='calibration.txt'):
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins)
        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.calibration_file = calibration_file

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.limit_switch_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.limit_switch_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def calibrate(self):
        # Rotate clockwise until the first limit switch is pressed
        self.motor.SetMicroStep('softward', 'fullstep')
        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=0.01)
        while GPIO.input(self.limit_switch_1):
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=0.01)

        # Rotate counter-clockwise until the second limit switch is pressed
        steps = 0
        while GPIO.input(self.limit_switch_2):
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=0.01)
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
            raise Exception("Motor not calibrated. Please run calibrate() first.")

        steps = int(angle * self.angle_to_step_ratio)
        self.motor.TurnStep(Dir='forward', steps=steps, stepdelay=0.01)

    def cleanup(self):
        GPIO.cleanup()
        self.motor.Stop()

# main.py
# from stepper_motor import StepperMotor

# def main():
#    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6)
 #   motor.calibrate()
  #  motor.move_to_angle(45)  # Example: move to 45 degrees
   # motor.cleanup()

#if __name__ == '__main__':
 #   main()