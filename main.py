import logging
import threading
import time
import csv
from tkinter import filedialog
from globals import initialise_io, initialise_gui, steppermotor_z, controller_x, controller_y

# Set to stop process while it's running.
stop_process_event = threading.Event()
# Set to pause process while it's running after it finishes the current photo, clear to continue the process.
pause_process_event = threading.Event()


def initialise_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def calibrate_all():
    from globals import controller_x, controller_y, steppermotor_z
    # Calibrate steppermotors
    steppermotor_x = controller_x.steppermotor
    steppermotor_y = controller_y.steppermotor

    steppermotor_x.calibrate()
    steppermotor_y.calibrate()
    steppermotor_z.calibrate()
    # Zero the calipers while the steppermotors are on their home position.
    caliper_x = controller_x.caliper
    caliper_y = controller_y.caliper

    steppermotor_x.stop_step_event.wait()
    caliper_x.zero()
    steppermotor_y.stop_step_event.wait()
    caliper_y.zero()
    steppermotor_z.stop_step_event.wait()


def z_move_camera(num_steps):
    """
    Move the camera on the z-axis by a given number of steps in either direction.

    Args:
        num_steps: The number of steps to move, a negative number will move the motor in reverse direction


    """
    if num_steps >= 0:
        if steppermotor_z.reversed:
            steppermotor_z.reverse()
        steppermotor_z.start_step(num_steps)
    else:
        if not steppermotor_z.reversed:
            steppermotor_z.reverse()
        steppermotor_z.start_step(-num_steps)
    steppermotor_z.stop_step_event.wait()


def start_process(setpoints=None):
    """
    Reads setpoints from a csv file with 2 columns (x setpoint, y setpoint per well).
    Then the camera is positioned above each well by using the two controllers.

    Args:
        setpoints: x and y setpoints per well in the format: [(x_setpoint, y_setpoint), ...]
    """
    from globals import app
    # todo disable z axis controls during process

    # Open setpoints from csv file if none are given
    if setpoints is None:
        setpoints_filepath = filedialog.askopenfilename(filetypes=[('Setpoints csv', '*.csv')])
        with open(setpoints_filepath) as f:
            reader = csv.reader(f)
            setpoints = [row for row in reader]

    for well in setpoints:
        setpoint_x, setpoint_y = well
        # Start control loops with given setpoints
        controller_x.start(setpoint_x)
        controller_y.start(setpoint_y)
        # Wait for control loops to finish
        controller_x.wait_until_finished()
        controller_y.wait_until_finished()
        # Take a picture and wait a bit before moving on to the next well
        photo_path = camera.take_photo()
        # Show the image on screen
        app.update_image(photo_path)
        while pause_process_event.is_set():
            # Wait for it to clear before continuing
            time.sleep(0.5)
        if stop_process_event.is_set():
            # Stop the loop. The controllers and steppermotors are stopped by stop_process
            stop_process_event.clear()
            break


def stop_process():
    stop_process_event.set()
    controller_x.stop()
    controller_y.stop()


def pause_process():
    if not pause_process_event.is_set():
        pause_process_event.set()
    else:
        pause_process_event.clear()


if __name__ == '__main__':
    initialise_logging()
    # I/O global references are defined in a seperate globals.py file, so that start_process, pause_process and stop_process can be called from other modules without issues.
    initialise_io()
    #calibrate_all()
    # todo initial height setting on startup defined as steps from zero point
    initialise_gui()
    from globals import app
    app.mainloop()

    # todo write functions to test steppermotor and caliper classes