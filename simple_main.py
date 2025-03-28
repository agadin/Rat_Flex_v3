import streamlit as st
import socket
import os
import redis
import multiprocessing.shared_memory as sm
import numpy as np
import time
import struct
import pandas as pd
import struct
import mmap
import os
import csv
from collections import defaultdict

from PIL.ImageCms import Direction

# Define the same format and file path used for writing
fmt = 'i d d d'  # Example format: (int, int, float, double)
shm_file = "shared_memory.dat"
shm_size = struct.calcsize(fmt)


redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

shm_name = 'shared_data'
shm_size = struct.calcsize('i d d d')  # 4 bytes for int, 3 doubles (8 bytes each)
fmt = 'i d d d'  # Format for packing (stop_flag, step_count, current_angle, current_force)

# Create shared memory block
try:
    shm = sm.SharedMemory(name=shm_name)
except FileNotFoundError:
    print("Shared memory not found. Creating new shared memory block.")
    redis_client.set("shared_memory_error", 1)
    time.sleep(1)
    shm = sm.SharedMemory(name=shm_name)


def send_protocol_path(protocol_path):
    server_address = ('localhost', 8765)  # Server's address and port
    try:
        # Create a TCP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # Connect the client to the server
            client_socket.connect(server_address)

            # Send the protocol path to the server
            client_socket.sendall(protocol_path.encode('utf-8'))

    except Exception as e:
        print(f"Error: {e}")

def run_protocol(protocol_path):
    redis_client.set('protocol_trigger', protocol_path)
    print(f"Triggered protocol: {protocol_path}")

def read_shared_memory_old(new_stop_flag=0):
    with open(shm_file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), shm_size, access=mmap.ACCESS_WRITE)
        try:
            # Read the entire data block using unpack_from
            stop_flag, index, current_angle, force = struct.unpack_from(fmt, mm, 0)

            # Print the unpacked values
            print(f"Before update:")
            print(f"Stop Flag: {stop_flag}")
            print(f"Index: {index}")
            print(f"Current Angle: {current_angle}")
            print(f"Force: {force}")
            if new_stop_flag != stop_flag:
                struct.pack_into('i', mm, 0, new_stop_flag)

                # Read again to confirm the update
                stop_flag, index, current_angle, force = struct.unpack_from(fmt, mm, 0)
        except struct.error as e:
            print(f"Error: {e}")
            index, current_angle, force = 0, 0, 0
            return index, current_angle, force

    return index, current_angle, force

def read_shared_memory():
    try:
        data = bytes(shm.buf[:struct.calcsize(fmt)])
        stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)
        return step_count, current_angle, current_force
    except FileNotFoundError:
        return None

def send_data_to_shared_memory(stop_flag=1):
    step_count, current_angle, current_force =read_shared_memory()
    try:
        packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)
        shm.buf[:len(packed_data)] = packed_data
    except Exception as e:
        print(f"Error: {e}")

import bisect

def preprocess_data(calibration_data):
    """
    Preprocess the calibration data to allow fast nearest neighbor lookups.
    """
    preprocessed = {}
    for direction, angles_forces in calibration_data.items():
        sorted_angles = sorted(angles_forces.keys())
        preprocessed[direction] = {
            'angles': sorted_angles,
            'forces': {angle: angles_forces[angle] for angle in sorted_angles}
        }
    return preprocessed

def get_closest_binary(preprocessed_data, angle):
    """
    Use binary search to find the closest angle and its force.
    """
    angles = preprocessed_data['angles']
    idx = bisect.bisect_left(angles, angle)
    if idx == 0:
        closest_angle = angles[0]
    elif idx == len(angles):
        closest_angle = angles[-1]
    else:
        before = angles[idx - 1]
        after = angles[idx]
        closest_angle = before if abs(before - angle) <= abs(after - angle) else after
    return preprocessed_data['forces'][closest_angle]

def find_closest_force_optimized(preprocessed_data, target_angle, direction):
    """
    Optimized version of find_closest_force using binary search.
    """
    if direction == 'forward':
        return get_closest_binary(preprocessed_data['forward'], target_angle)
    else:
        return get_closest_binary(preprocessed_data['backward'], target_angle)

def read_calibration_data(file_path):
    """
    Reads calibration data from a CSV file and formats it for quick lookups.

    Args:
        file_path (str): Path to the calibration CSV file.

    Returns:
        dict: A nested dictionary where the outer keys are directions (forward/backward),
              the inner keys are angles, and the values are corresponding forces.
    """
    calibration_data = defaultdict(dict)

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            angle = float(row['angle'])
            force = float(row['force'])
            direction = row['direction'].strip().lower()

            calibration_data[direction][angle] = force

    return calibration_data

if __name__ == "__main__":
    st.title("Stepper Motor Control")

    # List protocol files in the protocols folder
    protocol_folder = './protocols'
    protocol_files = [f for f in os.listdir(protocol_folder) if os.path.isfile(os.path.join(protocol_folder, f))]

    # Dropdown to select a protocol
    selected_protocol = st.selectbox("Select a protocol", protocol_files)

    # Button to run the selected protocol
    if st.button("Run Protocol"):
        protocol_path = os.path.join(protocol_folder, selected_protocol)
        run_protocol(protocol_path)
        st.write(f"Running protocol: {selected_protocol}")

    # Display shared memory data
    st.subheader("Shared Memory Data")
    shared_memory_placeholder = st.empty()
    average_time = None
    average_time_placeholder = st.empty()

    # Initialize lists to store data for plotting
    time_data = []
    angle_data = []
    force_data = []
    dot_time_data = []
    dot_angle_data = []
    dot_force_data = []

    start_time = time.time()
    if st.button("Stop", key="stop_button"):
        send_data_to_shared_memory()
    # Set up Streamlit's interval behavior
    preprocessed_data = None
    while True:
        shared_data = read_shared_memory()
        current_direction=redis_client.get("current_direction")
        calibration = redis_client.get("Calibrated")
        if calibration == "1":
            redis_client.set("Calibrated", 0)
            file_path = 'calibration.csv'
            calibration_data = read_calibration_data(file_path)
            preprocessed_data = preprocess_data(calibration_data)
            print("Calibration data loaded.")
        if current_direction is None:
            current_direction = 'forward'
        if average_time is not None:
            average_time_placeholder.write(f"Average Time: {average_time}")
        if shared_data is not None:
            step_count, current_angle, current_force = shared_data
            current_time = time.time() - start_time

            if preprocessed_data is not None:
                zeroed_force_calc= find_closest_force_optimized(preprocessed_data, current_angle, current_direction)
                time.sleep(0.01)  # Small delay to mimic the effect of the print statement
            else:
                zeroed_force_calc=0

            zeroed_force= current_force- zeroed_force_calc
            # Append data to lists
            time_data.append(current_time)
            angle_data.append(current_angle)
            force_data.append(zeroed_force)

            # Add to dot data as well
            dot_time_data.append(current_time)
            dot_angle_data.append(current_angle)
            dot_force_data.append(zeroed_force)

            # Update the shared memory display
            shared_memory_placeholder.write(
                f"Step Count: {step_count}, Current Angle: {current_angle}, Current Force: {current_force}, Target: {zeroed_force_calc}, Current Zero Force: {zeroed_force}, Current Direction: {current_direction}")

            # add button to stop

            if False:
                # Create a DataFrame for the line chart
                plot_data = pd.DataFrame({
                    'Time': time_data,
                    'Angle': angle_data,
                    'Force': force_data
                })

                # Display the line chart
                st.subheader("Angle and Force over Time (Line Plot)")
                st.line_chart(plot_data.set_index('Time'))

                # Display the dot plot
                st.subheader("Angle and Force over Time (Dot Plot)")

                # Use Streamlit's scatter_chart for dot plot
                # Pass a unique key to each button to avoid Streamlit errors
                if st.button("Clear Dot Plot", key="clear_dot_plot_button"):
                    dot_time_data.clear()
                    dot_angle_data.clear()
                    dot_force_data.clear()

                if dot_time_data:
                    # Prepare data for scatter chart
                    scatter_data = pd.DataFrame({
                        'Time': dot_time_data,
                        'Angle': dot_angle_data,
                        'Force': dot_force_data
                    })

                    # Display the scatter chart
                    st.scatter_chart(scatter_data.set_index('Time'))

        else:
            shared_memory_placeholder.write("Shared memory not available.")

        time.sleep(0.1)
