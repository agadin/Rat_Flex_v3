import streamlit as st
import websockets
import asyncio

async def send_command(command):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(command)

def calibrate():
    asyncio.run(send_command("calibrate"))

def move_to_angle(angle):
    command = f"Move_to_angle:{angle}"
    asyncio.run(send_command(command))

st.title("Stepper Motor Control")

if st.button("Calibrate"):
    calibrate()
    st.write("Calibration command sent.")

angle = st.number_input("Enter angle to move to:", min_value=0, max_value=360, step=1)
if st.button("Move to Angle"):
    move_to_angle(angle)
    st.write(f"Move to angle {angle} command sent.")