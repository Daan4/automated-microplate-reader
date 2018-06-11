import threading
import time
import RPi.GPIO as GPIO
from tkinter import messagebox


class StepperMotor:
    def __init__(self, pin_step, pin_direction, pin_calibration_microswitch, pin_safety_microswitch,
                 step_frequency, microswitch_bouncetime=300, calibration_timeout=20, name=""):
        """Interfaces with the steppermotors and limit switches.

        Args:
            pin_step: GPIO pin number for step pulse output
            pin_direction: GPIO pin number for direction output
            pin_calibration_microswitch: GPIO pin number for microswitch input in the normal direction
            pin_safety_microswitch: GPIO pin number for microswitch input in reverse direction
            step_frequency: Step frequency in steps per second
            microswitch_bouncetime: Microswitch debounce time in ms
            calibration_timeout: Calibration timeout in seconds
            name: optional name for debugging purposes
        """
        self.pin_step = pin_step
        self.pin_direction = pin_direction
        self.pin_calibration_microswitch = pin_calibration_microswitch  # GPIO pin for microswitch input
        self.pin_safety_microswitch = pin_safety_microswitch
        self.step_frequency = step_frequency
        self.default_step_frequency = step_frequency
        self.calibration_timeout = calibration_timeout
        self.microswitch_bouncetime = microswitch_bouncetime
        self.name = name

        self.reversed = False  # If true then direction is reversed ie digital output HIGH
        self.microswitch_hit_event = threading.Event()  # Set when the microswitch is hit, cleared when start stepping
        self.stop_step_event = threading.Event()  # Set it to stop stepping. Cleared when start stepping.

        self.lock_step_frequency = threading.Lock()

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_step, GPIO.OUT, initial=GPIO.LOW)
        self.step_pwm = GPIO.PWM(self.pin_step, self.default_step_frequency)
        GPIO.setup(self.pin_direction, GPIO.OUT, initial=GPIO.LOW)

        # Setup interrupts for limit switches if used
        self.ignore_interrupt = False
        if self.pin_calibration_microswitch is not None and self.pin_safety_microswitch is not None:
            GPIO.setup(self.pin_calibration_microswitch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.pin_safety_microswitch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            # Setup microswitch interrupt
            GPIO.add_event_detect(self.pin_calibration_microswitch, GPIO.RISING, callback=self.microswitch_callback,
                                  bouncetime=self.microswitch_bouncetime)
            GPIO.add_event_detect(self.pin_safety_microswitch, GPIO.RISING, callback=self.microswitch_callback,
                                  bouncetime=self.microswitch_bouncetime)

    def enable_interrupts(self):
        self.ignore_interrupt = False

    def disable_interrupts(self):
        self.ignore_interrupt = True

    def start_step(self, count=None):
        """Start stepping

        Args:
            count: the number of steps to make. Since using the built in pwm this is only approximated by setting timer,
                    instead of actually counting the steps."""
        self.stop_step_event.clear()
        self.microswitch_hit_event.clear()
        if count is not None:
            # Move a set amount of steps with the default speed if count is given
            self.step_frequency = self.default_step_frequency
            threading.Timer(self.step_frequency / count, self.stop_step).start()
        self.step_pwm.start(50)

    def stop_step(self):
        """Stop stepping"""
        self.stop_step_event.set()
        self.step_pwm.stop()
        self.microswitch_hit_event.clear()

    def set_duty_cycle(self, value):
        """Set pwm duty cycle"""
        self.step_pwm.ChangeDutyCycle(value)

    def reverse(self, setting):
        """Reverse motor direction

        Args:
            setting: optional set to True or False to choose a direction, if None the direction is inverted
        """
        if setting is not None:
            if setting:
                GPIO.output(self.pin_direction, GPIO.LOW)
            else:
                GPIO.output(self.pin_direction, GPIO.HIGH)
            self.reversed = setting
        else:
            if self.reversed:
                GPIO.output(self.pin_direction, GPIO.HIGH)
            else:
                GPIO.output(self.pin_direction, GPIO.LOW)
            self.reversed = not self.reversed

    def calibrate(self):
        """Calibrate motor to zero position.
        The motor is moved all the way to one side until the microswitch is hit."""
        # check if switch is already pressed, if so then don't move -> the motor is already on its zero position
        if GPIO.input(self.pin_calibration_microswitch) == GPIO.HIGH or GPIO.input(
                self.pin_safety_microswitch) == GPIO.HIGH:
            self.stop_step_event.set()
            return
        if self.pin_calibration_microswitch is not None:
            self.reverse(False)
            self.step_frequency = self.default_step_frequency
            self.start_step()
            if self.microswitch_hit_event.wait(self.calibration_timeout):
                self.step_counter = 0
            else:
                self.stop_step()
                messagebox.showerror('FOUT', 'Fout tijdens calibratie: Timeout (kalibreren duurt te lang)')
        else:
            messagebox.showerror('FOUT',
                                 'Voor deze motor is geen eindschakelaar ingesteld en er kan niet worden gekalibreert')

    def microswitch_callback(self, channel):
        """Interrupt callback. This function is called when the microswitch is pressed."""
        if self.ignore_interrupt:
            return
        # Filter out interrupts caused by random noise by checking again after 10ms
        time.sleep(0.01)
        if GPIO.input(self.pin_calibration_microswitch) == GPIO.HIGH or GPIO.input(
                self.pin_safety_microswitch) == GPIO.HIGH:
            self.microswitch_hit_event.set()
            self.stop_step()
            print("interrupt {} {}".format(self.name, channel))


class CalibrationError(BaseException):
    pass
