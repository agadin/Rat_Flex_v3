
from Wavshare_stepper_code.DRV8825 import DRV8825, setup_gpio
from database import init_db, DATABASE_PATH
import RPi.GPIO as GPIO
import time
import os
import sqlite3

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt', db_file='motor_state.db'):
        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins, limit_pins=(self.limit_switch_1, self.limit_switch_2))
        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.calibration_file = calibration_file
        self.step_type = step_type
        self.stepdelay = stepdelay
        self.db_file = db_file
        self.motor.SetMicroStep('software', self.step_type)

        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

        # Initialize database connection and cursor (check if the database is initialized)
        init_db()


    def update_db(self, current_direction=None, current_angle=None, angle_to_step_ratio=None, motor_state=None):
        # Open a new database connection and cursor each time to avoid recursive issues
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        cursor = conn.cursor()

        try:
            if current_direction is not None:
                cursor.execute("UPDATE motor_state SET current_direction = ? WHERE id = 1;", (current_direction,))
            if current_angle is not None:
                cursor.execute("UPDATE motor_state SET current_angle = ? WHERE id = 1;", (current_angle,))
            if angle_to_step_ratio is not None:
                cursor.execute("UPDATE motor_state SET angle_to_step_ratio = ? WHERE id = 1;", (angle_to_step_ratio,))
            if motor_state is not None:
                cursor.execute("UPDATE motor_state SET motor_state = ? WHERE id = 1;", (motor_state,))

            # Commit the transaction
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

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
        self.current_direction = 'calibrating'
        self.update_db(current_direction=self.current_direction)  # Update the direction in the DB

        # Rotate clockwise until the first limit switch is pressed
        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
        while GPIO.input(self.limit_switch_1):
            print("Limit switch 1 status:", GPIO.input(self.limit_switch_1))
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)

        # Rotate counter-clockwise until the second limit switch is pressed
        steps = 0
        while GPIO.input(self.limit_switch_2):
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)
            steps += 1

        self.steps_per_revolution = steps
        self.angle_to_step_ratio = steps / 180.0

        # Save calibration data to file
        with open(self.calibration_file, 'w') as file:
            file.write(f"steps_per_revolution: {self.steps_per_revolution}\n")
            file.write(f"angle_to_step_ratio: {self.angle_to_step_ratio}\n")

        # Update the calibration and angle_to_step_ratio in the DB
        self.update_db(current_direction='idle', angle_to_step_ratio=self.angle_to_step_ratio)
        self.move_to_angle(90)

    def move_to_angle(self, angle):
        if self.angle_to_step_ratio is None:
            self.angle_to_step_ratio = 1.0
            # raise Exception("Motor not calibrated. Please run calibrate() first.")

        steps = int(angle * self.angle_to_step_ratio)
        self.current_direction = 'moving'
        self.update_db(current_direction=self.current_direction)  # Update the direction in the DB
        self.motor.TurnStep(Dir='forward', steps=steps, stepdelay=0.0015)

        # Update the angle in the database after moving
        self.update_db(current_angle=angle, motor_state='stopped', current_direction='idle')

    def cleanup(self):
        self.motor.Stop()
        GPIO.cleanup()

    def stop(self):
        self.motor.Stop()

