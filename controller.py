from pid_controller.pid import PID
import threading
import queue
import time
from tkinter import messagebox


class Controller:
    def __init__(self, proportional_gain, integral_gain, differential_gain, stepper_motor, caliper, error_margin,
                 steppermotor_frequency_limits, settling_time, name, setpoint_offset, interrupt_ignore_time):
        """This class controls a single steppermotor-caliper feedback loop, by moving the load to a given setpoint.

        Args:
            proportional_gain: P gain of controller
            integral_gain: I gain of controller
            differential_gain: D gain of controller
            stepper_motor: StepperMotor object
            caliper: Caliper object
            error_margin: The maximum error in absolute terms in mm (so error_margin=10 -> +-10mm)
            steppermotor_frequency_limits: tuple with the minimum and maximum allowed steppermotor frequencies
            settling_time: the time in seconds that the position reading should stay within the setpoint +- error_margin range to stop
            name: name for debugging
            setpoints_offset: This is the offset that when given as a setpoint should move the camera to the middle of the first well
            interrupt_ignore_time: The time to ignore interrupts for in seconds when temp_disable_interrupts is called
        """
        self.pid = PID(p=proportional_gain, i=integral_gain, d=differential_gain)  # P I D controller
        self.steppermotor = stepper_motor  # The stepper motor moving the load
        self.caliper = caliper  # The caliper providing position feedback.
        self.stop_loop_event = threading.Event()  # This is set when the control loop stops
        self.setpoint = None  # Current setpoint
        self.error_margin = error_margin
        self.step_frequency_min, self.step_frequency_max = steppermotor_frequency_limits
        self.name = name
        self.settling_time = settling_time
        self.setpoint_offset = setpoint_offset
        self.interrupt_ignore_time = interrupt_ignore_time

        self.start_settling_time = None  # timestamp when settling started
        self.settling = False  # true if within allowed error band
        self.captured_data = []  # Stores captured data for visualization and debugging purposes

    def _control_loop(self, capture_data):
        """The control loop, self.start and self.stop start and stop this control loop in it's own thread.
        The load will be moved to the set self.setpoint
        The control loop will continue until it reaches ist setpoint, stopped by the user, by a limit switch being hit,
        or by the caliper timing out.

        Args:
            capture_data: True to save timestamps and position samples to self.captured_data

        """
        start_time = time.time()
        first_run = True
        while not self.stop_loop_event.is_set():
            # Wait for the next sensor reading
            # If the next reading is filtered wait until a correct reading is received
            try:
                failed = False
                position = self.caliper.get_reading()
                while position is None:
                    failed = True
                    self.steppermotor.set_duty_cycle(0)
                    position = self.caliper.get_reading()
            except queue.Empty:
                # Timed out waiting for sensor reading
                # Check if the process was stopped while waiting for sensor reading
                if self.stop_loop_event.is_set():
                    break
                else:
                    raise TimeoutError("Controller {} timed out waiting for sensor reading".format(self.name))
            finally:
                # Start the motor again if it was stopped before due to filtered data
                if failed:
                    self.steppermotor.set_duty_cycle(50)

            if capture_data:
                self.captured_data.append((time.time() - start_time, position))

            error = self.setpoint - position

            # Check if the goal position was reached
            # The loop is stopped when the load has been in it's allowed error band for at least the given settling time.
            if abs(error) < self.error_margin:
                if self.settling and time.time() - self.start_settling_time > self.settling_time:
                    print("stop {} {}".format(self.name, position))
                    self.stop()
                    break
                elif not self.settling:
                    self.settling = True
                    self.start_settling_time = time.time()
            else:
                self.settling = False
                self.start_settling_time = None

            # Get the new pid controller output
            output = self.pid(feedback=error)

            # Use the controller output to set the stepper motor speed
            if self.steppermotor.stop_step_event.is_set() and not first_run:
                # The steppermotor stopped unexpectedly -> Limit switch was hit
                # Stop the entire process
                # Importing stop_process here to prevent circular import
                from main import stop_process
                stop_process()
                messagebox.showerror('Foutmelding', 'Een eindschakelaar is geraakt tijdens het proces.')
                break

            # Set correct motor direction
            if output > 0 and not self.steppermotor.reversed or output <= 0 and self.steppermotor.reversed:
                self.steppermotor.reverse()

            # Set motor step frequency, clipping it to the upper and lower limit
            if abs(output) > self.step_frequency_max:
                output = self.step_frequency_max
            elif abs(output) < self.step_frequency_min:
                output = self.step_frequency_min

            # Start the motor on the first loop iteration
            if first_run:
                self.steppermotor.start_step()

            # Set the step frequency
            self.steppermotor.set_frequency(abs(output))

            first_run = False

    def start(self, setpoint, capture=False, ignore_interrupts=False):
        """Start the control loop by starting the caliper interrupt, setting the setpoint and calling _control_loop"""
        self.stop_loop_event.clear()
        self.caliper.start_listening()
        self.setpoint = setpoint + self.setpoint_offset
        self.captured_data = []
        if ignore_interrupts:
            threading.Thread(target=self.temp_disable_interrupts).start()
        self._control_loop(capture)

    def temp_disable_interrupts(self):
        """ignore limit switch interrupts for a set time"""
        self.steppermotor.disable_interrupts()
        time.sleep(self.interrupt_ignore_time)
        self.steppermotor.enable_interrupts()

    def stop(self):
        """Stop the control loop, the steppermotor and the caliper interrupts"""
        self.stop_loop_event.set()
        self.steppermotor.stop_step()
        self.caliper.stop_listening()

    def wait_until_finished(self):
        """Blocks until the control loop stops."""
        self.stop_loop_event.wait()
