from pid_controller.pid import PID
import threading
import queue
from tkinter import messagebox


class Controller:
    """This class controls a single steppermotor-caliper feedback loop."""
    def __init__(self, proportional_gain, integral_gain, differential_gain, stepper_motor, caliper, error_margin=0.01,
                 steppermotor_frequency_limits=(5, 1000), name=""):
        """

        Args:
            proportional_gain: P gain of controller
            integral_gain: I gain of controller
            differential_gain: D gain of controller
            stepper_motor: StepperMotor object
            caliper: Caliper object
            error_margin: The maximum error in absolute terms in mm (so error_margin=10 -> +-10)
            steppermotor_frequency_limits: tuple with the minimum and maximum steppermotor frequencies
        """
        self.pid = PID(p=proportional_gain, i=integral_gain, d=differential_gain)  # P I D controller
        self.steppermotor = stepper_motor  # The stepper motor moving the load
        self.caliper = caliper  # The caliper providing position feedback.
        self.stop_loop_event = threading.Event()
        self.setpoint = None
        self.error_margin = error_margin  # Allowed margin of error between setpoint and measured position.
        self.step_frequency_min, self.step_frequency_max = steppermotor_frequency_limits
        self.name = name

    def _control_loop(self):
        """The control loop, self.start and self.stop start and stop this control loop in it's own thread."""
        while not self.stop_loop_event.is_set():
            # Wait for the next sensor reading
            try:
                position = self.caliper.get_reading()
            except queue.Empty:
                # Timed out waiting for sensor reading
                # Check if the process was while waiting for sensor reading
                if self.stop_loop_event.is_set():
                    break
                else:
                    raise TimeoutError("Controller {} timed out waiting for sensor reading".format(self.name))

            error = self.setpoint - position
            print("loop")
            print(position)
            print(error)
            
            if abs(error) < self.error_margin:
                # If we reached the goal position -> stop the control loop
                print("stop {}".format(self.name))
                self.stop()
                break
            
            # Get the new pid controller output
            output = self.pid(feedback=error)

            # Use the controller output to control the stepper motor
            if self.steppermotor.stop_step_event.is_set():
                # The steppermotor stopped unexpectedly -> Limit switch was hit
                # Stop the entire process
                # Importing stop_process here to prevent circular import
                from main import stop_process
                stop_process()
                messagebox.showerror('Foutmelding', 'Een eindschakelaar is geraakt tijdens het proces.')
                break
                # todo display error message?

            # Set correct motor direction
            if output > 0 and not self.steppermotor.reversed or output <= 0 and self.steppermotor.reversed:
                self.steppermotor.reverse()
            print(self.steppermotor.reversed)

            # Set motor step frequency, adhering to the upper and lower limit
            if abs(output) > self.step_frequency_max:
                output = self.step_frequency_max
            elif abs(output) < self.step_frequency_min:
                output = self.step_frequency_min
            self.steppermotor.step_frequency = abs(output)

    def start(self, setpoint):
        """Start the control loop."""
        self.stop_loop_event.clear()
        self.caliper.start_listening()
        self.steppermotor.start_step()
        self.setpoint = setpoint
        threading.Thread(target=self._control_loop()).start()

    def stop(self):
        """Stop the control loop."""
        self.stop_loop_event.set()
        self.steppermotor.stop_step()
        self.caliper.stop_listening()

    def wait_until_finished(self):
        """Blocks until the control loop stops."""
        self.stop_loop_event.wait()
