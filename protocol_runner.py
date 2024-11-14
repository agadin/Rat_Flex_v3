import sys
import redis
import time
from Wavshare_stepper_code.stepper_motor import StepperMotor
import socket

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Define motor as a global variabl
motor = None

def process_protocol(protocol_path):
    with open(protocol_path, 'r') as file:
        commands = file.readlines()

    for command in commands:
        command = command.strip()
        if not command:
            continue

        redis_client.set("current_step", command)
        stop_flag = redis_client.get("stop_flag")
        if stop_flag == "1":
            print("Protocol stopped.")
            break

        if command.startswith("Move_to_angle"):
            angle = int(command.split(":")[1])
            move_to_angle(angle)
        elif command.startswith("Move_to_force"):
            force = float(command.split(":")[1])
            move_to_force(force)
        elif command.startswith("calibrate"):
            motor.calibrate()
        elif command.startswith("Move until force or angle"):
            params = command.split(":")[1].split(",")
            force = float(params[0])
            angle = int(params[1])
            move_until_force_or_angle(force, angle)
        elif command.startswith("wait"):
            wait_time = int(command.split(":")[1])
            wait(wait_time)
        elif command.startswith("Wait for user input"):
            wait_for_user_input()

    # end_all_commands()

def calibrate():
    motor.calibrate()

def end_all_commands():
    global motor
    motor.cleanup()
    redis_client.set("current_step", "")
    redis_client.set("stop_flag", "0")


def move_to_angle(angle):
    global motor
    print(f"Moving to angle: {angle}")
    motor.move_to_angle(angle)


def move_to_force(force):
    print(f"Moving to force: {force}")
    time.sleep(1)  # Simulate the action


def move_until_force_or_angle(force, angle):
    print(f"Moving until force: {force} or angle: {angle}")
    time.sleep(1)  # Simulate the action


def wait(wait_time):
    print(f"Waiting for {wait_time} seconds")
    time.sleep(wait_time)


def wait_for_user_input():
    print("Waiting for user input")
    while True:
        user_input = redis_client.get("user_input")
        if user_input == "continue":
            break
        time.sleep(1)

def start_server():
    global motor
    host = 'localhost'
    port = 12345
    if motor is None:
        motor = StepperMotor(
            dir_pin=13,
            step_pin=19,
            enable_pin=12,
            mode_pins=(16, 17, 20),
            limit_switch_1=5,
            limit_switch_2=6,
            step_type='fullstep',
            stepdelay=0.0015
        )
        # Connect to Redis server
        while True:
            # Check for a value in the Redis key
            protocol_path = redis_client.get("protocol_trigger")
            print(f"Checking for protocol trigger: {protocol_path}")
            if protocol_path:
                print(f"Found protocol path: {protocol_path}")
                process_protocol(protocol_path)
                redis_client.set("protocol_trigger", "")  # Clear the trigger after processing
            time.sleep(1)  # Wait for 1 second before checking again

if __name__ == "__main__":
    start_server()