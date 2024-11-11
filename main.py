from Wavshare_stepper_code.stepper_motor import StepperMotor
import time
import threading
import queue
import streamlit as st
import sqlite3
from database import init_db, DATABASE_PATH

# Command queue to manage motor actions
command_queue = queue.Queue()

# Function to continuously process commands in a separate thread
def motor_worker(motor):
    while True:
        command = command_queue.get()  # Block until a new command is available
        if command == "calibrate":
            motor.calibrate()
        elif command.startswith("move"):
            # Extract angle from the command
            angle = int(command.split(":")[1])
            motor.move_to_angle(angle)
        elif command == "stop":
            motor.stop()
            break
        time.sleep(0.1)

def get_current_state_from_db(db_file="stepper_motor.db"):
    conn = sqlite3.connect(db_file, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT current_angle, current_direction, motor_state, angle_to_step_ratio FROM motor_state WHERE id = 1;")
    result = cursor.fetchone()

    conn.close()

    if result:
        current_angle, current_direction, motor_state, angle_to_step_ratio = result
        return {
            'current_angle': current_angle,
            'current_direction': current_direction,
            'motor_state': motor_state,
            'angle_to_step_ratio': angle_to_step_ratio
        }
    else:
        return None

# Function to display the current angle
def display_current_state():
    while True:
        current_state = get_current_state_from_db()  # Fetch the current state from the database
        if current_state:
            st.write(f"Current Angle: {current_state['current_angle']}°")
            st.write(f"Current Direction: {current_state['current_direction']}")
            st.write(f"Motor State: {current_state['motor_state']}")
            st.write(f"Angle to Step Ratio: {current_state['angle_to_step_ratio']}")
        time.sleep(1)  # Update every second

def main():
    # Initialize the stepper motor
    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6, step_type='fullstep', stepdelay=0.003)

    # Initialize the database
    init_db()
    # Start the motor worker thread
    motor_thread = threading.Thread(target=motor_worker, args=(motor,), daemon=True)
    motor_thread.start()

    # Streamlit user interface
    st.title("Stepper Motor Control Panel")

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

    # Continuously display the current angle
    display_current_state()

    # Wait for the motor thread to finish
    motor_thread.join()

if __name__ == '__main__':
    main()
