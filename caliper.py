import RPi.GPIO as GPIO
import time
from queue import Queue


class Caliper:
    # todo check pull up  / down and debounce settings / queue size
    def __init__(self, pin_data, pin_clock, pin_zero, clock_bouncetime=1, pause_time=50):
        """Read a bit on the data pin every time a clock pulse is received.
        Return the 24-bit number that gets sent roughly every 100-150ms by the digital caliper.

        Args:
            pin_data: data digital input gpio pin
            pin_clock: clock digital input gpio pin
            pin_zero: zero digital output gpio pin
            clock_bouncetime: clock debounce time in ms
            pause_time: minimum time between packets in ms
        """
        self.pin_data = pin_data
        self.pin_clock = pin_clock
        self.pin_zero = pin_zero
        self.clock_bouncetime = clock_bouncetime
        self.pause_time = pause_time
        self.current_burst_data = list()
        self.last_clock_time = None
        self.reading_queue = Queue(1)  # Ideally the reading should always processed before the next one is ready.

        # Setup gpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_data, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pin_clock, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.pin_zero, GPIO.OUT)

    def start_listening(self):
        # Enable clock interrupt
        GPIO.add_event_detect(self.pin_clock, GPIO.FALLING, callback=self.clock_callback, bouncetime=self.clock_bouncetime)

    def stop_listening(self):
        # Disable clock interrupt
        GPIO.remove_event_detect(self.pin_clock)
        # Clear queue
        self.reading_queue = Queue(1)

    def get_reading(self, timeout=1):
        """
        Blocks until a value is stored in self.reading_queue or until timeout

        Args:
            timeout: timeout in seconds


        Returns:
            latest reading that was added to self.reading_queue by clock_callback
        """
        return self.reading_queue.get(True, timeout)

    def zero(self):
        """Set the current caliper position to be the zero position."""
        GPIO.output(self.pin_zero, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.pin_zero, GPIO.LOW)

    def clock_callback(self):
        """
        Called on the clock falling edge.
        Sample the data input every call.
        Data is sent in 24-bit bursts every ~100-150ms.
        If listening started mid-burst the data from that first burst will be discarded.
        """
        # If last clock was too long ago discard the current_burst_data buffer and assume a new data packet started.
        current_time = time.time()*1000.0
        if current_time - self.last_clock_time >= self.pause_time:
            self.current_burst_data = list()
        self.last_clock_time = current_time
        # Add current data bit to buffer
        self.current_burst_data.append(GPIO.input(self.pin_data))
        # Store buffer in queue when 24 bits have been read.
        if len(self.current_burst_data) == 24:
            # todo convert list of bits to distance in mm (w 2 decimals)
            self.reading_queue.put(self.current_burst_data)
