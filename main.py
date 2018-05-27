from caliper import Caliper
from controller import Controller
from steppermotor import StepperMotor
from camera import Camera
import logging
import threading
import time
import csv
from tkinter import filedialog

# Global references to the controllers and steppermotors for motion control
controller_x = None
controller_y = None
steppermotor_z = None

# Global reference to photo camera
camera = None

# Global reference to tkinter app frame
app = None

# Global reference to tkinter root frame
tk_root = None

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


def initialise_io():
    global controller_x, controller_y, steppermotor_z, camera

    # create x-axis controller object
    caliper_x = Caliper(1, 1) # todo set gpio
    steppermotor_x = StepperMotor(17, 27, 22, 10)  # 10 Hz, gpio17 pulse, gpio27 direction, gpio22 interrupt
    controller_x = Controller(1, 1, 1, 1, steppermotor_x, caliper_x)

    # create y-axis controller object
    caliper_y = Caliper(1, 1) # todo set gpio
    steppermotor_y = StepperMotor(2, 3, 4, 100)  # 100 Hz, gpio2 pulse, gpio3 direction, gpio4 interrupt
    controller_y = Controller(1, 1, 1, 1, steppermotor_y, caliper_y)

    # create z-axis steppermotor object
    steppermotor_z = StepperMotor(0, 5, 6, 1)  # 1 Hz, gpio0 pulse, gpio5 direction, gpio6 interrupt

    # create camera object
    camera = Camera()

    # Calibrate steppermotors
    steppermotor_x.calibrate()
    steppermotor_y.calibrate()
    # Zero the calipers while the steppermotors are on their home position.
    steppermotor_x.stop_step_event.wait()
    caliper_x.zero()
    steppermotor_y.stop_step_event.wait()
    caliper_y.zero()


def initialise_gui():
    import gui  # Avoiding circular imports
    global tk_root, app
    tk_root = gui.tk.Tk()
    # tk_root.iconbitmap(filepath) # optional add icon
    tk_root.title('Automated Microplate Reader')
    # Set up (almost) fullscreen windowed
    #w, h = tk_root.winfo_screenwidth(), tk_root.winfo_screenheight()
    #tk_root.geometry('%dx%d+0+0' % (w, h))

    app = gui.AutomatedMicroplateReaderApplication(tk_root)
    app.mainloop()


def start_process():
    """
    Reads setpoints from a csv file with 2 columns (x setpoint, y setpoint per well).
    Then the camera is positioned above each well by using the two controllers.

    Args:
        setpoints: x and y setpoints per well in the format: [(x_setpoint, y_setpoint), ...]
    """
    # Ask for setpoints file path
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
    #initialise_io()
    initialise_gui()
