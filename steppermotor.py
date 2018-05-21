import threading
import time
import RPi.GPIO as GPIO


class StepperMotor:
    def __init__(self, pin_step, pin_direction, pin_calibration_microswitch, step_frequency, microswitch_bouncetime=300, calibration_timeout=10):
        self.reversed = False  # If true then direction is reversed ie digital output HIGH
        self.pin_step = pin_step  # GPIO pin for step pulse output
        self.pin_direction = pin_direction  # GPIO pin for movement direction output
        self.pin_calibration_microswitch = pin_calibration_microswitch  # GPIO pin for microswitch input
        self.stop_step_event = threading.Event()  # Set it to stop stepping. Clear it when starting stepping.
        self.step_frequency = step_frequency  # Number of steps per second
        self.step_counter = 0  # Number of steps away from zero position
        self.calibration_timeout = calibration_timeout
        self.microswitch_hit_event = threading.Event()

        # Setup GPIO
        GPIO.setup(self.pin_step, GPIO.OUT)
        GPIO.setup(self.pin_direction, GPIO.OUT)
        GPIO.setup(self.pin_calibration_microswitch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Setup microswitch interrupt
        GPIO.add_event_detect(self.pin_calibration_microswitch, GPIO.RISING, callback=self.microswitch_callback, bouncetime=microswitch_bouncetime)

    def step(self):
        """Make a single step"""
        while not self.stop_step_event.is_set():
            # Keep stepping until stop_step is called
            GPIO.output(self.pin_step, GPIO.HIGH)
            time.sleep(1/(2*self.step_frequency))
            GPIO.output(self.pin_step, GPIO.LOW)
            time.sleep(1 / (2 * self.step_frequency))
            self.step_counter += 1
            print("step")

    def start_step(self):
        """Start stepping"""
        self.stop_step_event.clear()
        threading.Thread(target=self.step).start()

    def stop_step(self):
        """Stop stepping"""
        self.stop_step_event.set()

    def reverse(self):
        """Reverse movement direction"""
        if not self.reversed:
            GPIO.output(self.pin_direction, GPIO.HIGH)
        else:
            GPIO.output(self.pin_direction, GPIO.LOW)
        self.reversed = not self.reversed

    def calibrate(self):
        """Calibrate motor to zero position.
        The motor is moved all the way to one side until the microswitch is hit."""
        self.reversed = False
        self.start_step()
        if self.microswitch_hit_event.wait(self.calibration_timeout):
            self.stop_step()
            self.step_counter = 0
            self.microswitch_hit_event.clear()
        else:
            raise TimeoutError('Timed out waiting for microswitch during calibration.')

    def microswitch_callback(self):
        """Interrupt callback. This function is called when the microswitch is pressed."""
        self.microswitch_hit_event.set()
