from caliper import Caliper
from controller import Controller
from steppermotor import StepperMotor
import logging

controller_x = None
controller_y = None
steppermotor_z = None


def initialise_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def initialise_io():
    global controller_x, controller_y, steppermotor_z

    # create x-axis controller
    caliper_x = Caliper()
    steppermotor_x = StepperMotor(1, 1, 1, 1)
    controller_x = Controller(1, 1, 1, 1, steppermotor_x, caliper_x)

    # create y-axis controller
    caliper_y = Caliper()
    steppermotor_y = StepperMotor(1, 1, 1, 1)
    controller_y = Controller(1, 1, 1, 1, steppermotor_y, caliper_y)

    # create z-axis steppermotor
    steppermotor_z = StepperMotor(1, 1, 1, 1)

    # Calibrate steppermotors
    steppermotor_x.calibrate()
    steppermotor_y.calibrate()
    # Zero the calipers while the steppermotors are on their home position.
    steppermotor_x.stop_step_event.wait()
    caliper_x.zero()
    steppermotor_y.stop_step_event.wait()
    caliper_y.zero()


def initialise_gui():
    pass


def start_process(setpoints):
    """

    Args:
        setpoints: x and y setpoints per well in the format: [(x_setpoint, y_setpoint), ...]
    """
    global controller_x, controller_y
    for well in setpoints:
        setpoint_x, setpoint_y = well
        # Start control loops with given setpoints
        controller_x.start(setpoint_x)
        controller_y.start(setpoint_y)
        # Wait for control loops to finish
        controller_x.wait_until_finished()
        controller_y.wait_until_finished()
        # Take a picture and wait a bit before moving on to the next well
        # todo implement taking pictures


def stop_process():
    pass


def pause_process():
    pass


if __name__ == '__main__':
    initialise_logging()
    initialise_io()
    initialise_gui()
