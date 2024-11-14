import streamlit as st
import socket
import os
import redis
import multiprocessing.shared_memory as sm
import numpy as np
import time
import struct
import matplotlib.pyplot as plt

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

shm_name = 'shared_data'
shm_size = struct.calcsize('i d d d')  # 4 bytes for int, 3 doubles (8 bytes each)
fmt = 'i d d d'  # Format for packing (stop_flag, step_count, current_angle, current_force)

# Create shared memory block
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

            # Optionally, you can wait for a response from the server
            # response = client_socket.recv(1024).decode('utf-8')
            # print(f"Server response: {response}")

    except Exception as e:
        print(f"Error: {e}")

def run_protocol(protocol_path):
    redis_client.set('protocol_trigger', protocol_path)
    print(f"Triggered protocol: {protocol_path}")

def read_shared_memory():
    try:
        data = bytes(shm.buf[:struct.calcsize(fmt)])
        stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)
        return step_count, current_angle, current_force
    except FileNotFoundError:
        return None

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
    plot_placeholder=st.empty()
    # Initialize lists to store data for plotting
    time_data = []
    angle_data = []
    force_data = []

    start_time = time.time()

    while True:
        shared_data = read_shared_memory()
        if shared_data is not None:
            step_count, current_angle, current_force = shared_data
            current_time = time.time() - start_time

            # Append data to lists
            time_data.append(current_time)
            angle_data.append(current_angle)
            force_data.append(current_force)

            shared_memory_placeholder.write(
                f"Step Count: {step_count}, Current Angle: {current_angle}, Current Force: {current_force}")

            # Plot the data
            plt.figure(figsize=(10, 5))
            plt.plot(time_data, angle_data, label='Angle')
            plt.plot(time_data, force_data, label='Force')
            plt.xlabel('Time (s)')
            plt.ylabel('Value')
            plt.title('Angle and Force over Time')
            plt.legend()
            plt.grid(True)
            plot_placeholder.pyplot(plt)
        else:
            shared_memory_placeholder.write("Shared memory not available.")
        time.sleep(0.1)