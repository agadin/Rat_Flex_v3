import streamlit as st
import socket
import asyncio
import os
import subprocess
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)



def run_protocol(protocol_path):
    #redis_client.set('protocol_trigger', protocol_path)
    python_path= 'base/bin/python'
    result = subprocess.run([python_path, 'protocol_runner.py', protocol_path], capture_output=True, text=True)

    if result.returncode == 0:
        print("Script ran successfully")
        print(result.stdout)  # If you want to capture and print output from the script
    else:
        print("Error running script")
        print(result.stderr)  # If you want to capture and print error output



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