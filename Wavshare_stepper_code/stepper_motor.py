import sqlite3
import time
import RPi.GPIO as GPIO
from DRV8825 import DRV8825, setup_gpio
from database import init_db, DATABASE_PATH
import os

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt'):
        init_db()  # Initialize the database
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.motor = DRV8825(dir_pin, step_pin, enable_pin, mode_pins, (self.limit_switch_1, self.limit_switch_2))
        self.step_type = step_type
        self.stepdelay = stepdelay
        self.calibration_file = calibration_file

        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.current_angle = 0
        self.current_state = "idle"
        self.current_direction = "idle"
        self.calibration_detected = False

        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

    def load_calibration(self):
        """Load calibration data from the calibration file."""
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as file:
                for line in file:
                    key, value = line.strip().split(': ')
                    if key == 'steps_per_revolution':
                        self.steps_per_revolution = int(value)
                    elif key == 'angle_to_step_ratio':
                        self.angle_to_step_ratio = float(value)
            self.calibration_detected = True
            self.update_db(calibration_detected=1, angle_to_step_ratio=self.angle_to_step_ratio)
        else:
            print("Calibration file not found. Please run calibrate().")
            self.update_db(calibration_detected=0)

    def update_db(self, **kwargs):
        """Update the database with the current state of the motor."""
        for key, value in kwargs.items():
            self.cursor.execute(f"UPDATE motor_state SET {key} = ? WHERE id = 1;", (value,))
        self.conn.commit()

    def check_stop_flag(self):
        """Check if the stop flag has been set in the database."""
        self.cursor.execute("SELECT stop_flag FROM motor_state WHERE id = 1;")
        return self.cursor.fetchone()[0] == 1

    def calibrate(self):
        """Calibrate the motor using limit switches."""
        self.current_state = "calibrating"
        self.update_db(current_state=self.current_state)

        # Rotate clockwise until the first limit switch is pressed
        self.current_direction = "forward"
        self.update_db(current_direction=self.current_direction)
        self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
        while GPIO.input(self.limit_switch_1):
            if self.check_stop_flag():
                print("Calibration stopped externally.")
                self.current_state = "idle"
                self.current_direction = "idle"
                self.update_db(current_state=self.current_state, current_direction=self.current_direction)
                return
            self.motor.TurnStep(Dir='forward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)

        # Rotate counter-clockwise until the second limit switch is pressed
        steps = 0
        self.current_direction = "backward"
        self.update_db(current_direction=self.current_direction)
        while GPIO.input(self.limit_switch_2):
            if self.check_stop_flag():
                print("Calibration stopped externally.")
                self.current_state = "idle"
                self.current_direction = "idle"
                self.update_db(current_state=self.current_state, current_direction=self.current_direction)
                return
            self.motor.TurnStep(Dir='backward', steps=1, stepdelay=self.stepdelay)
            time.sleep(self.stepdelay)
            steps += 1

        # Store calibration results
        self.steps_per_revolution = steps
        self.angle_to_step_ratio = steps / 180.0
        self.calibration_detected = True
        self.update_db(calibration_detected=1, angle_to_step_ratio=self.angle_to_step_ratio)

        # Save calibration data to file
        with open(self.calibration_file, 'w') as file:
            file.write(f"steps_per_revolution: {self.steps_per_revolution}\n")
            file.write(f"angle_to_step_ratio: {self.angle_to_step_ratio}\n")

        # Update the state and move to 90 degrees
        self.current_state = "idle"
        self.current_direction = "idle"
        self.update_db(current_state=self.current_state, current_direction=self.current_direction)
        print("Calibration completed successfully.")
        self.move_to_angle(90)

    def move_to_angle(self, angle):
        """Move the motor to a specified angle."""
        if self.angle_to_step_ratio is None:
            raise Exception("Motor not calibrated. Please run calibrate() first.")

        self.current_state = "moving"
        self.current_direction = "forward" if angle > self.current_angle else "backward"
        self.update_db(current_state=self.current_state, current_direction=self.current_direction)

        steps = int(abs(angle - self.current_angle) * self.angle_to_step_ratio)
        step_dir = 'forward' if angle > self.current_angle else 'backward'

        for _ in range(steps):
            if self.check_stop_flag():
                print("Move stopped externally.")
                break
            self.motor.TurnStep(Dir=step_dir, steps=1, stepdelay=self.stepdelay)
            self.current_angle += (1 / self.angle_to_step_ratio) * (1 if step_dir == 'forward' else -1)
            self.update_db(current_angle=self.current_angle)
            time.sleep(self.stepdelay)

        self.current_state = "idle"
        self.current_direction = "idle"
        self.update_db(current_state=self.current_state, current_direction=self.current_direction)

    def stop(self):
        """Stop the motor and update the database state."""
        self.motor.Stop()
        self.update_db(current_state="idle", current_direction="idle")

    def cleanup(self):
        """Clean up GPIO and close the database connection."""
        self.motor.Stop()
        GPIO.cleanup()
        self.conn.close()

