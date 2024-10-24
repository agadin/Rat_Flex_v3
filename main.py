# test_stepper_motor.py
from Wavshare_stepper_code.stepper_motor import StepperMotor
import time

def test_stepper_motor():
    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6)

    try:
        print("Starting calibration...")
        motor.calibrate()
        print("Calibration complete.")

        print("Turning 100 steps to the left...")
        motor.motor.TurnStep(Dir='backward', steps=100, stepdelay=0.01)
        print("Turned 100 steps to the left.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        motor.cleanup()
        print("Motor cleanup complete.")

if __name__ == '__main__':
    test_stepper_motor()