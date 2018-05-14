import threading


class StepperMotor:
    def __init__(self, pin_step, pin_direction, pin_calibration_microswitch, step_frequency):
        self.reversed = False  # If true then direction is reversed
        self.pin_step = pin_step  # GPIO pin for step pulse output
        self.pin_direction = pin_direction  # GPIO pin for movement direction output
        self.pin_calibration_microswitch = pin_calibration_microswitch  # GPIO pin for microswitch input
        self.stepping = False  # True if on
        self.step_frequency = step_frequency  # Number of steps per second
        self.step_counter = 0  # Number of steps away from zero position

    def step(self):
        """Make a single step"""
        print("step")
        if self.stepping:
            threading.Timer(1/self.step_frequency, self.step).start()

    def start_step(self):
        """Start stepping"""
        self.stepping = True
        self.step()

    def stop_step(self):
        """Stop stepping"""
        self.stepping = False

    def reverse(self):
        """Reverse movement direction"""
        pass

    def calibrate(self):
        """Calibrate motor to zero position.
        The motor is moved all the way to one side until the microswitch is hit."""
        pass