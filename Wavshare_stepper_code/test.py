# plan: Use a multimeter
# Set the multimeter to the diode test position and check for resistance between pairs of wires. There should be a few ohms of resistance between wires in the same phase, and no continuity between wires in different phases

import RPi.GPIO as GPIO
import time

# Define GPIO pins connected to the DRV8825 driver
DIR_PIN = 20  # Direction pin
STEP_PIN = 21  # Step pin
ENABLE_PIN = 16  # Enable pin

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(ENABLE_PIN, GPIO.OUT)

# Enable the driver by setting the ENABLE_PIN low
GPIO.output(ENABLE_PIN, GPIO.LOW)


# Function to rotate the motor
def rotate_motor(steps, direction, delay):
	# Set the direction
	GPIO.output(DIR_PIN, direction)

	for _ in range(steps):
		# Pulse the step pin to move the motor
		GPIO.output(STEP_PIN, GPIO.HIGH)
		time.sleep(delay)
		GPIO.output(STEP_PIN, GPIO.LOW)
		time.sleep(delay)


try:
	# Rotate motor clockwise 200 steps
	print("Rotating clockwise...")
	rotate_motor(steps=200, direction=GPIO.HIGH, delay=0.001)

	time.sleep(1)

	# Rotate motor counterclockwise 200 steps
	print("Rotating counterclockwise...")
	rotate_motor(steps=200, direction=GPIO.LOW, delay=0.001)

finally:
	# Cleanup GPIO setup
	GPIO.output(ENABLE_PIN, GPIO.HIGH)  # Disable the motor
	GPIO.cleanup()
