import threading
import time


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
        self.step_counter += 1
        while self.stepping:
            # GPIO HIGH
            # wait period/2
            # GPIO LOW
            # wait period/2
            time.sleep(1/self.step_frequency)
            print("step")
            pass

    def start_step(self):
        """Start stepping"""
        self.stepping = True
        threading.Thread(target=self.step).start()

    def stop_step(self):
        """Stop stepping"""
        self.stepping = False

    def reverse(self):
        """Reverse movement direction"""
        self.reversed = not self.reversed

    def calibrate(self):
        """Calibrate motor to zero position.
        The motor is moved all the way to one side until the microswitch is hit."""
        self.step_counter = 0
        self.reversed = False
