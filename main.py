from Wavshare_stepper_code.stepper_motor import StepperMotor
import time
import queue
import streamlit as st
import asyncio
from database_websocket_client import DatabaseWebSocketClient
import redis
# Command queue to manage motor actions
command_queue = queue.Queue()

# Function to continuously process commands in a separate thread
async def motor_worker(motor, redis_client):
    while True:
        command = command_queue.get()  # Block until a new command is available
        if command == "calibrate":
            await motor.calibrate()
        elif command.startswith("move"):
            # Extract angle from the command
            angle = int(command.split(":")[1])
            await motor.move_to_angle(angle)
        await asyncio.sleep(0.1)

def get_current_state_from_db(db_client):
    """Fetch the current state of the motor from the WebSocket-based MySQL database."""
    response = False #await db_client.send_db_command("get_motor_state")
    if response and "data" in response:
        data = response["data"]
        return {
            'current_angle': data.get("current_angle", 0),
            'current_direction': data.get("current_direction", "idle"),
            'motor_state': data.get("current_state", "idle"),
            'angle_to_step_ratio': data.get("angle_to_step_ratio", 1.0)
        }
    else:
        return None

# Function to display the current angle
async def display_current_state(redis_client):
    # Create placeholders for the values to update dynamically
    angle_placeholder = st.empty()
    direction_placeholder = st.empty()
    motor_state_placeholder = st.empty()
    ratio_placeholder = st.empty()
    current_state = {
        'current_angle': 0,
        'current_direction': 'idle',
        'current_state': 'idle',
        'angle_to_step_ratio': 1.0
    }
    while True:
        # current_state = await get_current_state_from_db(db_client)  # Fetch the current state from the database
        current_direction = redis_client.get("current_direction")
        if current_direction is not None:
            current_state['current_direction'] = current_direction
        else:
            current_state['current_direction'] = 'unknown'

        current_angle = redis_client.get("current_angle")
        if current_angle is not None:
            current_state['current_angle'] = current_angle
        else:
            current_state['current_angle'] = 0

        current_state_value = redis_client.get("current_state")
        if current_state_value is not None:
            current_state['current_state'] = current_state_value
        else:
            current_state['current_state'] = 'unknown'

        angle_to_step_ratio = redis_client.get("angle_to_step_ratio")
        if angle_to_step_ratio is not None:
            current_state['angle_to_step_ratio'] = angle_to_step_ratio
        else:
            current_state['angle_to_step_ratio'] = 1.0

        if current_state:
            # Update the placeholders with the new values
            angle_placeholder.metric("Current Angle", f"{current_state['current_angle']}°")
            direction_placeholder.metric("Current Direction", current_state['current_direction'])
            motor_state_placeholder.metric("Motor State", current_state['current_state'])
            ratio_placeholder.metric("Angle to Step Ratio", current_state['angle_to_step_ratio'])

        time.sleep(1)  # Update every second

def test_websocket_connection(db_client):
    """Test the WebSocket connection."""
    # TODO: add a check for mySQL connection

    try:
        response = db_client.send_db_command("get_motor_state")
        if response and response.get("status") == "success":
            return "WebSocket connection successful!"
        else:
            return "WebSocket connection failed: Unexpected response."
    except Exception as e:
        return f"WebSocket connection failed: {e}"

async def main():
    # Initialize the WebSocket client
    db_client = DatabaseWebSocketClient()
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    # Initialize the stepper motor
    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6, step_type='fullstep', stepdelay=0.003)

    # Start the motor worker coroutine
    motor_worker_task = asyncio.create_task(motor_worker(motor, db_client))

    # Streamlit user interface
    st.title("Stepper Motor Control Panel")

    # Test WebSocket Connection Dropdown
    debug_option = st.selectbox("Debug: Test WebSocket Connection", ["Select an option", "Test WebSocket Connection"])

    if debug_option == "Test WebSocket Connection":
        connection_status = redis_client.ping()
        st.write(connection_status)

    if 'calibrate' not in st.session_state:
        st.session_state.calibrate = False
    if 'angle' not in st.session_state:
        st.session_state.angle = 0

    # Display the current angle
    angle_display = st.empty()
    with angle_display:
        st.metric("Current Angle", f"{st.session_state.angle} degrees")

    # Buttons for calibration and moving to a specified angle
    if st.button("Calibrate Motor"):
        command_queue.put("calibrate")  # Send calibration command to the motor worker
        st.write("Calibration in progress...")

    angle_input = st.number_input("Enter target angle", min_value=0, max_value=180, value=90, step=1)
    if st.button("Move Motor to Angle"):
        command_queue.put(f"move:{angle_input}")  # Send move command to the motor worker
        st.write(f"Motor moved to {angle_input} degrees")

    # Add Stop Motor button
    if st.button("Stop Motor"):
        redis_client.set("stop_flag", 1)
        st.write("Motor stopped.")

    # Continuously display the current angle
    await display_current_state(redis_client)

    # Wait for the motor worker task to finish
    await motor_worker_task

    # Close the WebSocket connection when done
    # await db_client.close()

if __name__ == '__main__':
    asyncio.run(main())
