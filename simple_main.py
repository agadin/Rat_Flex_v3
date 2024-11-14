import streamlit as st
import websockets
import asyncio
import os

async def send_command(command):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(command)

def run_protocol(protocol_path):
    asyncio.run(send_command(protocol_path))

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