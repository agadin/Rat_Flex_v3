from Wavshare_stepper_code.stepper_motor import StepperMotor
import time
import threading
import streamlit as st



def display_current_angle(motor):
    """Continuously update the current angle in the Streamlit UI."""
    # Create a Streamlit empty container for updating the angle
    angle_display = st.empty()

    while motor.current_state != "idle":
        # Fetch current angle from the database
        motor.cursor.execute("SELECT current_angle FROM motor_state WHERE id = 1;")
        current_angle = motor.cursor.fetchone()[0]

        # Update the angle in the Streamlit app
        angle_display.metric("Current Angle", f"{current_angle:.2f} degrees")
        time.sleep(1)


def motor_operations(motor, angle=None):
    """Perform calibration and move motor to a specified angle."""
    # Perform calibration if triggered
    if st.session_state.calibrate:
        motor.calibrate()
        st.session_state.calibrate = False  # Reset calibration flag

    # Move motor to the requested angle if provided
    if angle is not None:
        motor.move_to_angle(angle)

    # After finishing the task, mark the motor state as idle
    motor.update_motor_state("idle")


def main():
    # Initialize the stepper motor
    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5,
                         limit_switch_2=6, step_type='fullstep', stepdelay=0.003)

    # Start the Streamlit app
    st.title("Stepper Motor Control Panel")

    # Initialize session state variables if they are not present
    if 'calibrate' not in st.session_state:
        st.session_state.calibrate = False

    if 'angle' not in st.session_state:
        st.session_state.angle = 0

    # Show the current angle and control options
    angle_display = st.empty()
    with angle_display:
        st.metric("Current Angle", f"{st.session_state.angle} degrees")

    # Buttons for calibration and moving to a specified angle
    if st.button("Calibrate Motor"):
        st.session_state.calibrate = True
        st.write("Calibration in progress...")

    # Input for specifying the angle
    angle_input = st.number_input("Enter target angle", min_value=0, max_value=180, value=90, step=1)

    if st.button("Move Motor to Angle"):
        st.session_state.angle = angle_input
        motor_operations(motor, angle=st.session_state.angle)
        st.write(f"Motor moved to {st.session_state.angle} degrees")

    # Start the motor operations in a separate thread
    motor_thread = threading.Thread(target=motor_operations, args=(motor, st.session_state.angle))
    motor_thread.start()

    # Wait for the motor operations to finish
    motor_thread.join()

    # Stop the motor and clean up after task completion
    motor.stop()
    motor.cleanup()


if __name__ == '__main__':
    main()
