from caliper import Caliper
from controller import Controller
from steppermotor import StepperMotor
from camera import Camera
import RPi.GPIO as GPIO
import threading

"""
This module holds global references to some useful objects.
"""


# Global references to the controllers and steppermotors for motion control
controller_x = None
controller_y = None
steppermotor_z = None

# Global reference to photo camera
camera = None

# Global reference to tkinter app frame
app = None

# Set to stop process while it's running.
stop_process_event = threading.Event()
# Set to pause process while it's running after it finishes the current photo, clear to continue the process.
pause_process_event = threading.Event()


def initialise_io():
    global controller_x, controller_y, steppermotor_z, camera
    # create x-axis controller object
    caliper_x = Caliper(1, 1, 1) # todo set gpio
    steppermotor_x = StepperMotor(17, 27, 22, 10)  # 10 Hz, gpio17 pulse, gpio27 direction, gpio22 interrupt
    controller_x = Controller(1, 1, 1, steppermotor_x, caliper_x)

    # create y-axis controller object
    caliper_y = Caliper(1, 1, 1) # todo set gpio
    steppermotor_y = StepperMotor(2, 3, 4, 100)  # 100 Hz, gpio2 pulse, gpio3 direction, gpio4 interrupt
    controller_y = Controller(1, 1, 1, steppermotor_y, caliper_y)

    # create z-axis steppermotor object
    steppermotor_z = StepperMotor(0, 5, 6, 1)  # 1 Hz, gpio0 pulse, gpio5 direction, gpio6 interrupt

    # create camera object
    camera = Camera()

    # setup emergency stop button interrupt
    from main import stop_process
    GPIO.setmode(GPIO.BCM)
    emergency_stop_pin = 1 # todo set gpio
    GPIO.setwarnings(False)
    GPIO.setup(emergency_stop_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(emergency_stop_pin, GPIO.FALLING, callback=stop_process())


def initialise_gui():
    import gui  # Avoiding circular imports
    global app
    tk_root = gui.tk.Tk()
    # tk_root.iconbitmap(filepath) # optional add icon
    tk_root.title('Automated Microplate Reader')
    # Set up (almost) fullscreen windowed
    #w, h = tk_root.winfo_screenwidth(), tk_root.winfo_screenheight()
    #tk_root.geometry('%dx%d+0+0' % (w, h))

    app = gui.AutomatedMicroplateReaderApplication(tk_root)
