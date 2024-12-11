import lgpio
import time

MotorDir = [
    'forward',
    'backward',
]

ControlMode = [
    'hardward',
    'softward',
]

class DRV8825:
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins, limit_pins):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.mode_pins = mode_pins
        self.limit_pins = limit_pins
        self.limit_switch_1 = limit_pins[0]
        self.limit_switch_2 = limit_pins[1]

        # Open GPIO chip
        self.chip = lgpio.gpiochip_open(0)

        # Setup GPIO pins
        self.setup_gpio()

    def setup_gpio(self):
        # Claim output pins
        lgpio.gpio_claim_output(self.chip, self.dir_pin)
        lgpio.gpio_claim_output(self.chip, self.step_pin)
        lgpio.gpio_claim_output(self.chip, self.enable_pin)

        # Setup mode pins
        for pin in self.mode_pins:
            lgpio.gpio_claim_output(self.chip, pin)

        # Claim input pins for limit switches
        lgpio.gpio_claim_input(self.chip, self.limit_switch_1)
        lgpio.gpio_claim_input(self.chip, self.limit_switch_2)

    def digital_write(self, pin, value):
        lgpio.gpio_write(self.chip, pin, value)

    def digital_read(self, pin):
        return lgpio.gpio_read(self.chip, pin)

    @property
    def limit_switch_1_state(self):
        return lgpio.gpio_read(self.chip, self.limit_switch_1)

    @property
    def limit_switch_2_state(self):
        return lgpio.gpio_read(self.chip, self.limit_switch_2)

    def Stop(self):
        self.digital_write(self.enable_pin, 0)

    def SetMicroStep(self, mode, stepformat):
        microstep = {
            'fullstep': (0, 0, 0),
            'halfstep': (1, 0, 0),
            '1/4step': (0, 1, 0),
            '1/8step': (1, 1, 0),
            '1/16step': (0, 0, 1),
            '1/32step': (1, 0, 1)
        }

        print("Control mode:", mode)
        if mode == 'software':
            steps = microstep[stepformat]
            for i, pin in enumerate(self.mode_pins):
                self.digital_write(pin, steps[i])

    def TurnStep(self, Dir, steps, stepdelay=0.005):
        if Dir == 'forward':
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 0)
        elif Dir == 'backward':
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 1)
        else:
            print("The direction must be 'forward' or 'backward'")
            self.digital_write(self.enable_pin, 0)
            return

        if steps == 0:
            return

        for i in range(steps):
            if (Dir == 'forward' and not self.digital_read(self.limit_switch_1)) or \
               (Dir == 'backward' and not self.digital_read(self.limit_switch_2)):
                print("Limit switch triggered, stopping motor")
                return 1

            self.digital_write(self.step_pin, 1)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, 0)
            if steps != 1:
                time.sleep(stepdelay)

    def cleanup(self):
        lgpio.gpiochip_close(self.chip)

def setup_gpio(limit_switch_1, limit_switch_2):
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_input(h, limit_switch_1)
    lgpio.gpio_claim_input(h, limit_switch_2)
    return h