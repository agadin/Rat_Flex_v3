import sys
import redis
import time
from Wavshare_stepper_code.stepper_motor import StepperMotor
import socket
import csv
import tkinter as tk
import customtkinter as ctk
import os
import shutil
from datetime import datetime


csv_name='data.csv'
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
motor = None

def create_folder_with_files(provided_name=None, special=False):
    # Create the folder
    try:
        animal_id = redis_client.get("animal_ID")
        if animal_id is None:
            animal_id = "0000"
    except redis.RedisError:
        animal_id = "0000"

    timestamp = datetime.now().strftime("%Y%m%d")
    trial_number = 1

    original_folder_name = f"{timestamp}_{animal_id}_{trial_number:02d}"

    folder_name= original_folder_name

    if os.path.exists(original_folder_name):
        while os.path.exists(folder_name):
            trial_number += 1
            folder_name = f"{original_folder_name}_{animal_id}_{trial_number:02d}"
    else:
        folder_name = original_folder_name

    # create the folder
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        print(f"Error: Folder '{folder_name}' already exists.")
        redis_client.set("Error_code","10")
    # Copy and rename `calibrate.txt`
    # copy everything into folder

    if os.path.exists('calibration.txt'):
        if provided_name is not None:
            shutil.copy('calibration.txt', os.path.join(folder_name, f"{provided_name}.txt"))
        else:
            shutil.copy('calibration.txt', os.path.join(folder_name, 'calibration.txt'))

    else:
        print("Error: `calibration.txt` not found.")

    with open('data.csv', 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        data = [row for row in reader]
        total_time = data[-1][0]
        redis_client.set("total_time", total_time)
        total_steps = data[-1][6]
        redis_client.set("total_steps", total_steps)

    # Copy and rename `data.csv`
    data_csv_path = 'data.csv'
    renamed_csv_path = os.path.join(folder_name, f"{folder_name}.csv")
    if os.path.exists(data_csv_path):
        shutil.copy(data_csv_path, renamed_csv_path)
    else:
        print("Error: `data.csv` not found.")


    # Create and save `information.txt` with the current date
    info_path = os.path.join(folder_name, 'information.txt')
    with open(info_path, 'w') as info_file:
        current_date = datetime.now().strftime("%Y-%m-%d")
        info_file.write(f"Created on: {current_date}\n")
        info_file.write(f"Total time: {total_time}\n")
        info_file.write(f"Total steps: {total_steps}\n")

    redis_client.set("data_saved", "1")
    return True


def string_to_value_checker(string_input, type_s="int"):
    try:
        # Try to convert the input directly to an integer or float
        if type_s == "float":
            return float(string_input)
        else:
            return int(string_input)
    except ValueError:
        # Check for open parenthesis to handle special calculations
        if string_input.startswith("(") and string_input.endswith(")"):
            inner_expr = string_input[1:-1]  # Extract content inside parentheses
            # Define angle_value from Redis
            angle_value = redis_client.get("angle_value")
            if angle_value is None:
                raise ValueError("Variable 'angle_value' not found in Redis.")
            angle_value = float(angle_value)  # Convert to float for calculations

            # Replace 'angle_value' with its value in the expression
            expr_with_value = inner_expr.replace("angle_value", str(angle_value))
            try:
                # Evaluate the expression and return the result
                result = eval(expr_with_value)
                if type_s == "float":
                    return float(result)
                else:
                    return int(result)
            except Exception as e:
                raise ValueError(f"Invalid expression in input: {string_input}. Error: {e}")
        # If no parentheses, check if it's a variable and look up in Redis
        angle_value = redis_client.get(string_input)
        if angle_value is None:
            raise ValueError(f"Variable '{string_input}' not found in Redis.")
        try:
            if type_s == "float":
                return float(angle_value)
            else:
                return int(float(angle_value))
        except ValueError:
            raise ValueError(f"Value for '{string_input}' in Redis is not a valid number.")
import csv


def variable_saver(variable_name, user_input):
    with open('variables.txt', 'a') as file:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        file.write(f"{current_time}, {variable_name}, {user_input}\n")

def calculate_metric(metric, protocol_step):
    with open('data.csv', 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        data = [row for row in reader if int(row[6]) == protocol_step]

    if not data:
        raise ValueError(f"No data found for protocol step {protocol_step}")

    if metric == "min_force":
        return min(float(row[2]) for row in data)
    elif metric == "max_force":
        return max(float(row[2]) for row in data)
    elif metric == "final_force":
        return float(data[-1][2])
    elif metric == "final_angle":
        return float(data[-1][1])
    elif metric == "max_angle":
        return max(float(row[1]) for row in data)
    elif metric == "min_angle":
        return min(float(row[1]) for row in data)
    elif metric == "final_time":
        return float(data[-1][0])
    elif metric == "start_time":
        return float(data[0][0])
    elif metric == "total_time":
        return float(data[-1][0]) - float(data[0][0])
    else:
        raise ValueError(f"Unknown metric: {metric}")

def process_protocol(protocol_path):
    protocol_filename = os.path.basename(protocol_path)
    redis_client.set("current_protocol_out", protocol_filename)
    with open(protocol_path, 'r') as file:
        commands = file.readlines()
        step_number = 0
        data_saved = False
        folder_name = f"data_{time.strftime('%Y%m%d_%H%M%S')}"

    for command in commands:
        command = command.strip()
        if not command:
            continue
        step_number += 1
        motor.current_protocol_step(step_number)
        redis_client.set("current_step", command)
        stop_flag = redis_client.get("stop_flag")
        if stop_flag == "1":
            print("Protocol stopped.")
            break
        if command.startswith("Move_to_angle"):
            # current command: Move_to_angle:90,metric,variable_name
            parts = command.split(":")[1].split(",")
            angle_input = parts[0].strip()
            angle = string_to_value_checker(angle_input)
            move_to_angle(angle)
            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    metric = str(parts[i].strip())
                    variable_name = str(parts[i + 1].strip()) if i + 1 < len(parts) else metric
                    metric_value = calculate_metric(metric, step_number)
                    variable_saver(variable_name, metric_value)
                    redis_client.set(variable_name, metric_value)
        elif command.startswith("Move_to_force"):
            params = command.split(":")[1].split(",")

            # Required parameters
            direction = params[0].strip()
            max_force = string_to_value_checker(params[1].strip(), "float")

            # Initialize optional parameters
            min_angle, max_angle = 0, 180
            metrics = []  # List to hold multiple metric, variable_name pairs

            # Parse remaining parameters
            index = 2
            while index < len(params):
                param = params[index].strip()
                if param.replace('.', '', 1).isdigit():  # Check if it's a number (min_angle or max_angle)
                    if min_angle == 0:  # First number -> min_angle
                        min_angle = string_to_value_checker(param)
                    else:  # Second number -> max_angle
                        max_angle = string_to_value_checker(param)
                else:  # Assume it's part of metric-variable_name pairs
                    if index + 1 < len(params):  # Ensure there's a variable_name following
                        metric = param
                        variable_name = params[index + 1].strip()
                        metrics.append((metric, variable_name))
                        index += 1  # Skip the next parameter since it's part of the pair
                    else:
                        raise ValueError("Metric without corresponding variable_name")
                index += 1

            # Execute the command
            print(f"Moving to force: {max_force} in direction: {direction}")
            move_to_force(direction, max_force, min_angle, max_angle)

            if metrics:
                for metric, variable_name in metrics:
                    metric_value = calculate_metric(metric, step_number)
                    variable_saver(variable_name, metric_value)
                    redis_client.set(variable_name, metric_value)
        elif command.startswith("Load_calibration"):
            # command format: Load_calibration: path/to/calibration.txt
            file_path = command.split(":")[1].strip()
            #check file_path if it does not have calibration.txt then add it
            if not file_path.endswith("calibration.txt"):
                file_path = file_path + "calibration.txt"
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Calibration file not found: {file_path}")
            motor.load_calibration(file_path)
        elif command.startswith("Save_as"):
            folder_name = command.split(":")[1].strip()
        elif command.startswith("calibrate"):
            data_saved = True
            motor.calibrate()
        elif command.startswith("wait"):
            wait_time = int(command.split(":")[1])
            wait(wait_time)
        elif command.startswith("Wait_for_user_input"):
            wait_for_user_input(command)
        elif command.startswith("End"):
            end_loop()
            break

        if not data_saved:
            # Set the name to the current date and time
            data_saved = create_folder_with_files(folder_name)




    # end_all_commands()
    redis_client.set("current_protocol_out", "")
# Add save as file name ability

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


def move_to_force(direction, max_force, min_angle=0, max_angle=180):
    global motor
    motor.move_until_force(int(direction),max_force, min_angle, max_angle)
    time.sleep(1)  # Simulate the action


def move_until_force_or_angle(force, angle):
    print(f"Moving until force: {force} or angle: {angle}")
    time.sleep(1)  # Simulate the action


def wait(wait_time):
    print(f"Waiting for {wait_time} seconds")
    current_csv_time= motor.read_first_value_in_last_row()
    timestep= 0.03
    end_time = time.time() + wait_time
    temp_data = []
    # open data.csv and read direction from last row if it exists and file was edited in the past 30 seconds
    idle_force= motor.return_idle_force()
    while time.time() < end_time:
        start_time = time.time()
        raw_force = motor.ForceSensor.read_force()
        current_force = raw_force - idle_force
        current_csv_time = current_csv_time + timestep
        temp_data.append([current_csv_time, motor.current_angle, current_force, raw_force, motor.current_state, motor.current_direction, motor.return_current_protocol_step()])
        elapsed_time = time.time() - start_time
        sleep_time = max(timestep - elapsed_time, 0)
        time.sleep(sleep_time)

    with open(csv_name, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(temp_data)

def end_loop():
    global motor
    motor.cleanup()
    print("Ending Protocol")


def wait_for_user_input(command):
    parts = command.split(":")[1].split(",")
    popup_name = parts[0].strip()
    variable_name = parts[1].strip()
    response_type = parts[2].strip()

    def on_submit():
        user_input = entry.get()
        try:
            if response_type == "int":
                user_input = int(user_input)
            elif response_type == "float":
                user_input = float(user_input)
            elif response_type == "string":
                user_input = str(user_input)
            else:
                raise ValueError("Invalid response type")

            redis_client.set(variable_name, user_input)
            redis_client.set("user_input", "")  # Clear the user input after processing
            variable_saver(variable_name, user_input)
            popup.destroy()
        except ValueError:
            error_label.config(text=f"Invalid input type. Expected {response_type}.")

    popup = ctk.CTk()
    popup.title(popup_name)

    label= ctk.CTkLabel(popup, text=f"Enter {response_type} value:")
    label.pack(pady=10)

    entry = ctk.CTkEntry(popup)
    entry.pack(pady=5)

    submit_button = ctk.CTkButton(popup, text="Submit", command=on_submit)
    submit_button.pack(pady=5)

    error_label = ctk.CTkLabel(popup, text="", fg_color="red")
    error_label.pack(pady=5)

    popup.mainloop()

def start_server():
    global motor
    if motor is None:
        motor = StepperMotor(
            dir_pin=13,
            step_pin=19,
            enable_pin=12,
            mode_pins=(16, 17, 20),
            limit_switch_1=6,
            limit_switch_2=5,
            step_type='halfstep',
            stepdelay=0.0015,
            calibration_file='calibration.csv',
            csv_name=csv_name

        )
        while True:
            # Check for a value in the Redis key
            protocol_path = redis_client.get("protocol_trigger")
            print(f"Checking for protocol trigger: {protocol_path}")
            shared_memory_error=redis_client.get("shared_memory_error")
            redis_client.set("calibration_Level",motor.check_if_calibrated())

            if shared_memory_error == "1":
                print("Shared memory error detected. Recreating shared memory.")
                redis_client.set("shared_memory_error", 0)
                motor.create_shared_memory()
            if protocol_path:
                redis_client.set("protocol_trigger", "")  # Clear the trigger after processing
                print(f"Found protocol path: {protocol_path}")
                process_protocol(protocol_path)
            redis_client.set("current_protocol_out", "")
            time.sleep(1)  # Wait for 1 second before checking again


if __name__ == "__main__":
    start_server()