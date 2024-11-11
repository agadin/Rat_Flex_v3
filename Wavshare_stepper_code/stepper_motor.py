from Wavshare_stepper_code.DRV8825 import DRV8825, setup_gpio
import RPi.GPIO as GPIO
import time
import os
import json
import websocket

class StepperMotor:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_switch_1, limit_switch_2, step_type='fullstep', stepdelay=0.0015, calibration_file='calibration.txt'):
        self.limit_switch_1 = limit_switch_1
        self.limit_switch_2 = limit_switch_2
        self.motor = DRV8825(dir_pin=dir_pin, step_pin=step_pin, enable_pin=enable_pin, mode_pins=mode_pins, limit_pins=(self.limit_switch_1, self.limit_switch_2))
        self.steps_per_revolution = None
        self.angle_to_step_ratio = None
        self.current_angle = 0
        self.calibration_file = calibration_file
        self.step_type = step_type
        self.stepdelay = stepdelay
        self.current_state = "idle"
        self.current_direction = "idle"
        self.motor.SetMicroStep('software', self.step_type)

        setup_gpio(self.limit_switch_1, self.limit_switch_2)
        self.load_calibration()

        # Initialize WebSocket client
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://localhost:8765")  # Adjust the WebSocket server URL

    def send_db_command(self, command, data=None):
        """Send a command to the WebSocket database server."""
        message = {
            "command": command,
            "data": data or {}
        }
        self.ws.send(json.dumps(message))
        response = json.loads(self.ws.recv())
        return response

    def update_db(self, current_direction=None, current_angle=None, angle_to_step_ratio=None, motor_state=None):
        """Update the motor state in the database using WebSocket."""
        data = {}
        if current_direction is not None:
            data["current_direction"] = current_direction
        if current_angle is not None:
            data["current_angle"] = current_angle
        if angle_to_step_ratio is not None:
            data["angle_to_step_ratio"] = angle_to_step_ratio
        if motor_state is not None:
            data["current_state"] = motor_state

        self.send_db_command("update_motor_state", data)

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
        self.update_db(current_direction=self.current_direction)

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

        # Update the database with calibration data
        self.update_db(current_direction='idle', angle_to_step_ratio=self.angle_to_step_ratio)
        self.move_to_angle(90)

    def move_to_angle(self, angle):
        """Move the motor to a specified angle using WebSocket-based database updates."""
        if self.angle_to_step_ratio is None:
            raise Exception("Motor not calibrated. Please run calibrate() first.")

        # Determine the direction and set the motor state
        self.current_state = "moving"
        self.current_direction = "forward" if angle > self.current_angle else "backward"
        self.send_db_command("update_motor_state", {
            "current_state": self.current_state,
            "current_direction": self.current_direction
        })

        # Calculate the number of steps and the direction
        steps = int(abs(angle - self.current_angle) * self.angle_to_step_ratio)
        step_dir = 'forward' if angle > self.current_angle else 'backward'

        # Start moving the motor step by step
        for _ in range(steps):
            # Check if a stop flag has been set
            stop_flag_response = self.send_db_command("read_stop_motor")
            stop_flag = stop_flag_response.get("stop_flag", 0)
            if stop_flag == 1:
                print("Move stopped externally.")
                break

            # Perform the motor step
            self.motor.TurnStep(Dir=step_dir, steps=1, stepdelay=self.stepdelay)

            # Update the current angle based on the step direction
            self.current_angle += (1 / self.angle_to_step_ratio) * (1 if step_dir == 'forward' else -1)

            # Update the current angle in the database
            self.send_db_command("update_motor_state", {"current_angle": self.current_angle})
            time.sleep(self.stepdelay)

        # Set the motor state back to idle
        self.current_state = "idle"
        self.current_direction = "idle"
        self.send_db_command("update_motor_state", {
            "current_state": self.current_state,
            "current_direction": self.current_direction
        })

    def cleanup(self):
        self.motor.Stop()
        GPIO.cleanup()

    def stop(self):
        self.motor.Stop()
        self.update_db(motor_state='stopped', current_direction='idle')

