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

# constant settings
# TODO SET CORRECT VALUES
CALIPER_X_PIN_DATA = 12
CALIPER_X_PIN_CLOCK = 16
CALIPER_X_PIN_ZERO = 19
STEPPERMOTOR_X_PIN_STEP = 3
STEPPERMOTOR_X_PIN_DIRECTION = 2
STEPPERMOTOR_X_PIN_CALIBRATION_SWITCH = 14
STEPPERMOTOR_X_PIN_SAFETY_SWITCH = 25
STEPPERMOTOR_X_FREQUENCY_DEFAULT = 300
CONTROLLER_X_P_GAIN = 150
CONTROLLER_X_I_GAIN = 0
CONTROLLER_X_D_GAIN = 0
CONTROLLER_X_FREQ_LIMITS = [25, 300]
CONTROLLER_X_ERROR_MARGIN = 0.1

CALIPER_Y_PIN_DATA = 20
CALIPER_Y_PIN_CLOCK = 21
CALIPER_Y_PIN_ZERO = 26
STEPPERMOTOR_Y_PIN_STEP = 17
STEPPERMOTOR_Y_PIN_DIRECTION = 4
STEPPERMOTOR_Y_PIN_CALIBRATION_SWITCH = 15
STEPPERMOTOR_Y_PIN_SAFETY_SWITCH = 8
STEPPERMOTOR_Y_FREQUENCY_DEFAULT = 300
CONTROLLER_Y_P_GAIN = 1
CONTROLLER_Y_I_GAIN = 0
CONTROLLER_Y_D_GAIN = 0
CONTROLLER_Y_FREQ_LIMITS = [100, 300]
CONTROLLER_Y_ERROR_MARGIN = 0.5

STEPPERMOTOR_Z_PIN_STEP = 22
STEPPERMOTOR_Z_PIN_DIRECTION = 27
STEPPERMOTOR_Z_PIN_CALIBRATION_SWITCH = None
STEPPERMOTOR_Z_PIN_SAFETY_SWITCH = None
STEPPERMOTOR_Z_FREQUENCY_DEFAULT = 25

EMERGENCY_STOP_BUTTON_PIN = 23

DROPDOWN_OPTIONS_DICT = {'Kies .csv bestand': None,
                         '12': '/setpoints/wellplate_12.csv',
                         '36': '/setpoints/wellplate_36.csv',
                         '48': '/setpoints/wellplate_48.csv',
                         '96': '/setpoints/wellplate_96.csv'}


def initialise_io():
    global controller_x, controller_y, steppermotor_z, camera
    # create x-axis controller object
    caliper_x = Caliper(CALIPER_X_PIN_DATA,
                        CALIPER_X_PIN_CLOCK,
                        CALIPER_X_PIN_ZERO)
    steppermotor_x = StepperMotor(STEPPERMOTOR_X_PIN_STEP,
                                  STEPPERMOTOR_X_PIN_DIRECTION,
                                  STEPPERMOTOR_X_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_X_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_X_FREQUENCY_DEFAULT,
                                  calibration_timeout=1000)
    controller_x = Controller(CONTROLLER_X_P_GAIN,
                              CONTROLLER_X_I_GAIN,
                              CONTROLLER_X_D_GAIN,
                              steppermotor_x,
                              caliper_x,
                              CONTROLLER_X_ERROR_MARGIN,
                              CONTROLLER_X_FREQ_LIMITS,
                              "x")

    # create y-axis controller object
    caliper_y = Caliper(CALIPER_Y_PIN_DATA,
                        CALIPER_Y_PIN_CLOCK,
                        CALIPER_Y_PIN_ZERO)
    steppermotor_y = StepperMotor(STEPPERMOTOR_Y_PIN_STEP,
                                  STEPPERMOTOR_Y_PIN_DIRECTION,
                                  STEPPERMOTOR_Y_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_Y_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_Y_FREQUENCY_DEFAULT,
                                  calibration_timeout=1000)
    controller_y = Controller(CONTROLLER_Y_P_GAIN,
                              CONTROLLER_Y_I_GAIN,
                              CONTROLLER_Y_D_GAIN,
                              steppermotor_y,
                              caliper_y,
                              CONTROLLER_Y_ERROR_MARGIN,
                              CONTROLLER_Y_FREQ_LIMITS,
                              "y")

    # create z-axis steppermotor object # todo set gpio
    steppermotor_z = StepperMotor(STEPPERMOTOR_Z_PIN_STEP,
                                  STEPPERMOTOR_Z_PIN_DIRECTION,
                                  STEPPERMOTOR_Z_PIN_CALIBRATION_SWITCH,
                                  STEPPERMOTOR_Z_PIN_SAFETY_SWITCH,
                                  STEPPERMOTOR_Z_FREQUENCY_DEFAULT)

    # create camera object
    #camera = Camera()

    # setup emergency stop button interrupt
    from main import stop_process
    GPIO.setmode(GPIO.BCM)
    emergency_stop_pin = EMERGENCY_STOP_BUTTON_PIN
    GPIO.setwarnings(False)
    GPIO.setup(emergency_stop_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(emergency_stop_pin, GPIO.FALLING, callback=stop_process)


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
