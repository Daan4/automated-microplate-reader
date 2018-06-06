import RPi.GPIO as GPIO
import time
from queue import Queue


class Caliper:
    # todo check pull up  / down and debounce settings / queue size
    def __init__(self, pin_data, pin_clock, pin_zero, clock_bouncetime=1, pause_time=50, pin_debug=None, name=""):
        """Read a bit on the data pin every time a clock pulse is received.
        Return the 24-bit number that gets sent roughly every 100-150ms by the digital caliper.

        Args:
            pin_data: data digital input gpio pin
            pin_clock: clock digital input gpio pin
            pin_zero: zero digital output gpio pin
            clock_bouncetime: clock debounce time in ms
            pause_time: minimum time between packets in ms
            delay: the delay between clock falling edge and taking the data sample in seconds
            pin_debug: gives a pulse on this pin when a data sample is taking. useful for debuggin with scope
        """
        self.pin_data = pin_data
        self.pin_clock = pin_clock
        self.pin_zero = pin_zero
        self.clock_bouncetime = clock_bouncetime
        self.pause_time = pause_time
        self.current_burst_data = list()
        self.last_clock_time = 0
        self.reading_queue = Queue(1)  # Ideally the reading should always processed before the next one is ready.
        self.pin_debug = pin_debug

        # Setup gpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_data, GPIO.IN)
        GPIO.setup(self.pin_clock, GPIO.IN)
        GPIO.setup(self.pin_zero, GPIO.OUT)
        if self.pin_debug is not None:
            GPIO.setup(self.pin_debug, GPIO.OUT)

    def start_listening(self):
        # Enable clock interrupt
        GPIO.add_event_detect(self.pin_clock, GPIO.RISING, callback=self.clock_callback)

    def stop_listening(self):
        # Disable clock interrupt
        GPIO.remove_event_detect(self.pin_clock)
        # Clear queue (otherwise on the next process start it might start with an old reading in the queue?)
        with self.reading_queue.mutex:
            self.reading_queue.queue.clear()

    def get_reading(self, timeout=1):
        """
        Blocks until a value is stored in self.reading_queue or until timeout

        Args:
            timeout: timeout in seconds


        Returns:
            latest reading that was added to self.reading_queue by clock_callback
        """
        bit_list = self.reading_queue.get(True, timeout)
        bit_list.reverse()
        # bits 0-2 are always 0, bit 3 is the sign where 1 = negative and 0 = positive
        # bit 4-23 needs to be converted to decimal and divided by 100 to get the position in mm.
        value = bit_list_to_decimal(bit_list[4:])
        # use correct sign
        if bit_list[3] == 1:
            value = -value
        return self.filter(value / 100)

    def zero(self):
        """Set the current caliper position to be the zero position."""
        GPIO.output(self.pin_zero, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.pin_zero, GPIO.LOW)

    def clock_callback(self, channel):
        """
        Called on the clock falling edge.
        Sample the data input every call.
        Data is sent in 24-bit bursts every ~100-150ms.
        If listening started mid-burst the data from that first burst will be discarded.
        """
        if self.pin_debug is not None:
            GPIO.output(self.pin_debug, GPIO.HIGH)
        value = GPIO.input(self.pin_data)
        # If last clock was too long ago discard the current_burst_data buffer and assume a new data packet started.
        current_time = time.time()*1000.0
        if current_time - self.last_clock_time >= self.pause_time:
            self.current_burst_data = list()
        self.last_clock_time = current_time
        # Add current data bit to buffer
        self.current_burst_data.append(value)
        # Store buffer in queue when 24 bits have been read.
        #print(self.current_burst_data)
        if len(self.current_burst_data) == 24:
            # todo convert list of bits to distance in mm (w 2 decimals)
            self.reading_queue.put(self.current_burst_data)
        if self.pin_debug is not None:
            GPIO.output(self.pin_debug, GPIO.LOW)

    def filter(self, new_sample):
        # todo implement filter
        return new_sample


def bit_list_to_decimal(bit_list):
    out = 0
    for bit in bit_list:
        out = (out << 1) | bit
    return out
