from caliper import Caliper
from controller import Controller
from steppermotor import StepperMotor
from camera import Camera
import RPi.GPIO as GPIO
import threading

# The options that appear in the gui in the well plate choice drop down menu
# The dict value should be the path to a setpoints file (see testsetpoints.csv for an example)
# Setting the path to None will prompt the user to choose and open a file
DROPDOWN_OPTIONS_DICT = {'Kies .csv bestand': None,
                         '12': '/setpoints/wellplate_12.csv',
                         '36': '/setpoints/wellplate_36.csv',
                         '48': '/setpoints/wellplate_48.csv',
                         '96': 'D:\Libraries\Documents\pycharmprojects\\automated-microplate-reader\\testsetpoints.csv'}

# Constants/Settings
# See the class implementations for an explanation of the available parameters
# Pins are RPi 3B BCM GPIO pin numbers www.pinout.xyz
CALIPER_X_PIN_DATA = 12
CALIPER_X_PIN_CLOCK = 16
CALIPER_X_PIN_ZERO = 19
CALIPER_X_MEDIAN_FILTER_MAX_ERROR = 4.9  # in mm
CALIPER_X_MEDIAN_FILTER_WINDOW_SIZE = 3
STEPPERMOTOR_X_PIN_STEP = 3
STEPPERMOTOR_X_PIN_DIRECTION = 2
STEPPERMOTOR_X_PIN_CALIBRATION_SWITCH = 14
STEPPERMOTOR_X_PIN_SAFETY_SWITCH = 25
STEPPERMOTOR_X_FREQUENCY_DEFAULT = 800  # Hz
CONTROLLER_X_P_GAIN = 300
CONTROLLER_X_I_GAIN = 0
CONTROLLER_X_D_GAIN = 0
CONTROLLER_X_FREQ_LIMITS = [10, 800]  # Hz
CONTROLLER_X_ERROR_MARGIN = 0.1  # mm
CONTROLLER_X_SETTLING_TIME = 0.3  # s
CONTROLLER_X_SETPOINT_OFFSET = 7 + 12  # mm

CALIPER_Y_PIN_DATA = 20
CALIPER_Y_PIN_CLOCK = 21
CALIPER_Y_PIN_ZERO = 26
CALIPER_Y_MEDIAN_FILTER_MAX_ERROR = 4.9  # in mm
CALIPER_Y_MEDIAN_FILTER_WINDOW_SIZE = 3
STEPPERMOTOR_Y_PIN_STEP = 17
STEPPERMOTOR_Y_PIN_DIRECTION = 4
STEPPERMOTOR_Y_PIN_CALIBRATION_SWITCH = 15
STEPPERMOTOR_Y_PIN_SAFETY_SWITCH = 8
STEPPERMOTOR_Y_FREQUENCY_DEFAULT = 800
CONTROLLER_Y_P_GAIN = 300
CONTROLLER_Y_I_GAIN = 0
CONTROLLER_Y_D_GAIN = 0
CONTROLLER_Y_FREQ_LIMITS = [10, 800]
CONTROLLER_Y_ERROR_MARGIN = 0.1
CONTROLLER_Y_SETTLING_TIME = 0.3
CONTROLLER_Y_SETPOINT_OFFSET = 0 + 6

STEPPERMOTOR_Z_PIN_STEP = 22
STEPPERMOTOR_Z_PIN_DIRECTION = 27
STEPPERMOTOR_Z_PIN_CALIBRATION_SWITCH = None
STEPPERMOTOR_Z_PIN_SAFETY_SWITCH = None
STEPPERMOTOR_Z_FREQUENCY_DEFAULT = 25

EMERGENCY_STOP_BUTTON_PIN = 23

# The time to ignore interrupts for after leaving the calibrated zero position for the first time.
INTERRUPT_IGNORE_TIME = 1.5  # s

# Global references to the controller and steppermotor objects
controller_x = None
controller_y = None
steppermotor_z = None

# Global reference to camera object
camera = None

# Global reference to tkinter app frame object
app = None

# Set to stop process while it's running.
stop_process_event = threading.Event()
# Set to pause process while it's running after it finishes the current photo, clear to continue the process.
pause_process_event = threading.Event()


def initialise_io():
    """Initialise all IO pins and global object references (except gui)"""
    global controller_x, controller_y, steppermotor_z, camera
    # create x-axis controller object
    caliper_x = Caliper(CALIPER_X_PIN_DATA,
                        CALIPER_X_PIN_CLOCK,
                        CALIPER_X_PIN_ZERO,
                        name="x",
                        median_filter_max_error=CALIPER_X_MEDIAN_FILTER_MAX_ERROR,
                        median_filter_window_size=CALIPER_X_MEDIAN_FILTER_WINDOW_SIZE)
    steppermotor_x = StepperMotor(STEPPERMOTOR_X_PIN_STEP,
                                  STEPPERMOTOR_X_PIN_DIRECTION,
                                  STEPPERMOTOR_X_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_X_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_X_FREQUENCY_DEFAULT,
                                  calibration_timeout=60,
                                  name="x")
    controller_x = Controller(CONTROLLER_X_P_GAIN,
                              CONTROLLER_X_I_GAIN,
                              CONTROLLER_X_D_GAIN,
                              steppermotor_x,
                              caliper_x,
                              CONTROLLER_X_ERROR_MARGIN,
                              CONTROLLER_X_FREQ_LIMITS,
                              CONTROLLER_X_SETTLING_TIME,
                              "x",
                              CONTROLLER_X_SETPOINT_OFFSET,
                              INTERRUPT_IGNORE_TIME)

    # create y-axis controller object
    caliper_y = Caliper(CALIPER_Y_PIN_DATA,
                        CALIPER_Y_PIN_CLOCK,
                        CALIPER_Y_PIN_ZERO,
                        name="y",
                        median_filter_max_error=CALIPER_Y_MEDIAN_FILTER_MAX_ERROR,
                        median_filter_window_size=CALIPER_Y_MEDIAN_FILTER_WINDOW_SIZE)
    steppermotor_y = StepperMotor(STEPPERMOTOR_Y_PIN_STEP,
                                  STEPPERMOTOR_Y_PIN_DIRECTION,
                                  STEPPERMOTOR_Y_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_Y_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_Y_FREQUENCY_DEFAULT,
                                  calibration_timeout=60,
                                  name="y")
    controller_y = Controller(CONTROLLER_Y_P_GAIN,
                              CONTROLLER_Y_I_GAIN,
                              CONTROLLER_Y_D_GAIN,
                              steppermotor_y,
                              caliper_y,
                              CONTROLLER_Y_ERROR_MARGIN,
                              CONTROLLER_Y_FREQ_LIMITS,
                              CONTROLLER_Y_SETTLING_TIME,
                              "y",
                              CONTROLLER_Y_SETPOINT_OFFSET,
                              INTERRUPT_IGNORE_TIME)

    # create z-axis steppermotor object
    steppermotor_z = StepperMotor(STEPPERMOTOR_Z_PIN_STEP,
                                  STEPPERMOTOR_Z_PIN_DIRECTION,
                                  STEPPERMOTOR_Z_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_Z_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_Z_FREQUENCY_DEFAULT,
                                  calibration_timeout=60,
                                  name="z")

    # create camera object
    camera = Camera()

    # setup emergency stop button interrupt
    from main import stop_process
    GPIO.setmode(GPIO.BCM)
    emergency_stop_pin = EMERGENCY_STOP_BUTTON_PIN
    GPIO.setwarnings(False)
    GPIO.setup(emergency_stop_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(emergency_stop_pin, GPIO.FALLING, callback=stop_process)


def initialise_gui():
    """Initialises the user interface in gui.py"""
    import gui  # Avoiding circular imports
    global app
    tk_root = gui.tk.Tk()
    # tk_root.iconbitmap(filepath) # optional add icon
    tk_root.title('Automated Microplate Reader')  # window title
    app = gui.AutomatedMicroplateReaderApplication(tk_root)
