import streamlit as st
import socket
import asyncio
import os


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
    send_protocol_path(protocol_path)

# List protocol files in the protocols folder
protocol_folder = './protocols'
protocol_files = [f for f in os.listdir(protocol_folder) if os.path.isfile(os.path.join(protocol_folder, f))]

st.title("Stepper Motor Control")

# Dropdown to select a protocol
selected_protocol = st.selectbox("Select a protocol", protocol_files)

# Button to run the selected protocol
if st.button("Run Protocol"):
    protocol_path = os.path.join(protocol_folder, selected_protocol)
    run_protocol(protocol_path)
    st.write(f"Running protocol: {selected_protocol}")