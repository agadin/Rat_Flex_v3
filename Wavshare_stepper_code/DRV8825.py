import RPi.GPIO as GPIO
import time

MotorDir = [
    'forward',
    'backward',
]

ControlMode = [
    'hardward',
    'softward',
]

# Wavshare_stepper_code/DRV8825.py
import RPi.GPIO as GPIO

class DRV8825:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.mode_pins = mode_pins

        GPIO.setmode(GPIO.BCM)  # Ensure the pin numbering mode is set
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        for pin in self.mode_pins:
            GPIO.setup(pin, GPIO.OUT)

    def digital_write(self, pin, value):
        GPIO.output(pin, value)

    def TurnStep(self, Dir, steps, stepdelay):
        self.digital_write(self.enable_pin, 0)
        self.digital_write(self.dir_pin, 1 if Dir == 'forward' else 0)
        for _ in range(steps):
            self.digital_write(self.step_pin, 1)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, 0)
            time.sleep(stepdelay)

    def Stop(self):
        self.digital_write(self.enable_pin, 0)
