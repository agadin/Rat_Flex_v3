import time
import threading
from Wavshare_stepper_code.stepper_motor import StepperMotor

def display_current_angle(motor):
    """Continuously display the current angle of the motor."""
    while motor.current_state != "idle":
        # Fetch current angle from the database
        motor.cursor.execute("SELECT current_angle FROM motor_state WHERE id = 1;")
        current_angle = motor.cursor.fetchone()[0]
        print(f"Current Angle: {current_angle:.2f} degrees")
        time.sleep(1)

def motor_operations(motor):
    """Perform calibration and move motor to 90 degrees."""
    # Perform calibration
    motor.calibrate()

    # Move motor to 90 degrees
    motor.move_to_angle(90)

    # After finishing the task, mark the motor state as idle
    motor.update_motor_state("idle")

def main():
    # Initialize the stepper motor
    motor = StepperMotor(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20), limit_switch_1=5, limit_switch_2=6, step_type='fullstep', stepdelay=0.003)

    # Start the thread to continuously display the current angle
    display_thread = threading.Thread(target=display_current_angle, args=(motor,))
    display_thread.start()

    # Start the motor operations in a separate thread
    motor_thread = threading.Thread(target=motor_operations, args=(motor,))
    motor_thread.start()

    # Wait for the motor operations to finish
    motor_thread.join()

    # Stop the motor and clean up after task completion
    motor.stop()
    motor.cleanup()

    # Wait for the display thread to finish
    display_thread.join()

if __name__ == '__main__':
    main()
