from pid_controller.pid import PID
import threading
import time


class Controller:
    """This class controls a single steppermotor-caliper feedback loop."""
    def __init__(self, proportional_gain, integral_gain, differential_gain, sample_frequency, stepper_motor, caliper, error_margin=0.01):
        self.pid = PID(p=proportional_gain, i=integral_gain, d=differential_gain)  # P I D controller
        self.stepper_motor = stepper_motor  # The stepper motor moving the load
        self.caliper = caliper  # The caliper providing position feedback.
        self.stop_loop_event = threading.Event()
        self.sample_frequency = sample_frequency
        self.setpoint = None
        self.error_margin = error_margin  # Allowed margin of error between setpoint and measured position.

    def _control_loop(self):
        """The control loop, self.start and self.stop start and stop this control loop in it's own thread."""
        while not self.stop_loop_event.is_set():
            # Get the current position
            position = self.caliper.get_reading()
            if self.setpoint - position < self.error_margin:
                # If we reached the goal position -> stop the control loop
                self.setpoint = None
                self.stop_loop_event.set()
                break
            # Get the new pid controller output
            output = self.pid(feedback=position)
            # Use the controller output to control the stepper motor
            # todo convert output to stepper motor frequency setting???
            # Wait before taking next sample
            # todo subtract this function's running time if a more accurate sleep time is needed
            time.sleep(1/self.sample_frequency)

    def start(self, setpoint):
        """Start the control loop."""
        self.stop_loop_event.clear()
        self.setpoint = setpoint
        threading.Thread(target=self._control_loop()).start()

    def stop(self):
        """Stop the control loop."""
        self.stop_loop_event.set()
        self.stepper_motor.stop_step()

    def wait_until_finished(self):
        self.stop_loop_event.wait()
