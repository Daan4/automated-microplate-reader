import logging
import time
from datetime import datetime
import csv
import threading
from tkinter import filedialog, messagebox
from globals import initialise_io, initialise_gui, steppermotor_z, controller_x, controller_y, \
    stop_process_event, pause_process_event


def initialise_logging():
    """Initialise debug logging to file
    Not really used at the moment..."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def calibrate_all():
    """Calibrate the x and y steppermotors to their zero position.
    Both calipers are also zeroed when the steppermotors reach this position.
    At the moment is z steppermotor is not connected nor does it have any limit switches, so those lines are commented out
    """
    from globals import controller_x, controller_y, steppermotor_z

    # Calibrate steppermotors simultaneously
    steppermotor_x = controller_x.steppermotor
    steppermotor_y = controller_y.steppermotor
    threading.Thread(target=steppermotor_x.calibrate).start()
    threading.Thread(target=steppermotor_y.calibrate).start()
    # threading.Thread(target=steppermotor_z.calibrate).start()
    # Zero the calipers while the steppermotors are on their home position.
    caliper_x = controller_x.caliper
    caliper_y = controller_y.caliper

    t1 = threading.Thread(target=await_calibration_and_zero, args=[caliper_x, steppermotor_x])
    t1.start()
    t2 = threading.Thread(target=await_calibration_and_zero, args=[caliper_y, steppermotor_y])
    t2.start()
    # t3 = threading.Thread(target=await_calibration_and_zero, args=[None, steppermotor_z])
    t1.join()
    t2.join()
    # t3.join()


def await_calibration_and_zero(caliper, steppermotor):
    """Waits for the steppermotor to calibrate, then zeroes the caliper

    Args:
        caliper: Caliper object to zero
        steppermotor: StepperMotor object to calibrate
    """
    steppermotor.stop_step_event.wait()
    if caliper is not None:
        caliper.zero()


def z_move_camera(num_steps):
    """Move the camera on the z-axis by a given number of steps in either direction.

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


def start_process(filepath=None, capture_data=False):
    """Reads setpoints from a csv file with 2 columns (x setpoint, y setpoint per well).
    Then the camera is positioned above each well by starting the x and y controllers.

    Args:
        filepath: filepath to csv with x, y setpoints in mm with 2 decimal numbers in each row
        capture_data: True to save datapoints to a list (controller.captured_data)
    """

    # Import here so the function works when called from main.py for testing
    from globals import app, controller_x, controller_y, camera

    # Save start timestamp for photo file naming
    start_timestamp = datetime.now()

    # Read setpoints from csv file or ask for a file to open
    if filepath is None:
        filepath = filedialog.askopenfilename(filetypes=[('Setpoints csv', '*.csv')])
    else:
        filepath = filepath
    try:
        with open(filepath) as f:
            reader = csv.reader(f)
            filepath = [row for row in reader]
    except FileNotFoundError:
        messagebox.showinfo("INFO", "{} is geen geldig bestand".format(filepath))
        return

    # Calibrate the steppermotors and calipers
    calibrate_all()

    # Reset median filter values to all zeroes
    controller_x.caliper.reset_median_filter()
    controller_y.caliper.reset_median_filter()

    old_setpoint_x, old_setpoint_y = None, None

    # On the first pair of setpoints ignore interrupts while moving away from the limit switches.
    first_well = True

    for counter, well in enumerate(filepath):
        app.update_status("WELL {}/{}".format(counter + 1, len(filepath)))

        setpoint_x, setpoint_y = list(map(float, well))

        # Start the controllers in their own thread, to wait for both of them to finish asynchronously.
        x_thread, y_thread = None, None
        if setpoint_x != old_setpoint_x:
            x_thread = threading.Thread(target=controller_x.start,
                                        args=[setpoint_x, capture_data, first_well])
            x_thread.start()
        if setpoint_y != old_setpoint_y:
            y_thread = threading.Thread(target=controller_y.start,
                                        args=[setpoint_y, capture_data, first_well])
            y_thread.start()
        try:
            x_thread.join()
        except AttributeError:
            pass
        try:
            y_thread.join()
        except AttributeError:
            pass

        old_setpoint_x = setpoint_x
        old_setpoint_y = setpoint_y

        # Check for pause or stop
        while pause_process_event.is_set():
            # Wait for it to clear before continuing
            time.sleep(1.5)
        if stop_process_event.is_set():
            # Stop the loop. The controllers and steppermotors are stopped by stop_process
            stop_process_event.clear()
            break

        # Take a picture
        filename = "{}_{}_of_{}".format(datetime.strftime(start_timestamp, "%Y%m%d%H%M%S"), counter + 1, len(filepath))
        photo_path = camera.take_photo(filename)

        # Show the image on screen
        app.update_image(photo_path)

        first_well = False

    app.update_status("EINDE - STANDBY")


def stop_process():
    """Stop the process."""
    stop_process_event.set()
    controller_x.stop()
    controller_y.stop()
    from globals import app
    app.update_status("STANDBY")


def pause_process():
    """Pause the process after it finishes the current well."""
    from globals import app, pause_process_event
    if not pause_process_event.is_set():
        app.update_status("GEPAUZEERD")
        pause_process_event.set()
    else:
        pause_process_event.clear()


def test_calipers():
    from globals import controller_x, controller_y
    caliper_x = controller_x.caliper
    caliper_y = controller_y.caliper
    caliper_x.start_listening()
    caliper_y.start_listening()
    while True:
        print("schuifmaat x {}".format(caliper_x.get_reading()))
        print("schuifmaat y {}".format(caliper_y.get_reading()))


if __name__ == '__main__':
    initialise_logging()
    initialise_io()
    # test_calipers()
    initialise_gui()
    from globals import app

    app.mainloop()
