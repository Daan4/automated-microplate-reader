import RPi.GPIO as GPIO
import time
from queue import Queue


class Caliper:
    def __init__(self, pin_data, pin_clock, pin_zero, clock_bouncetime=1, pause_time=50, pin_debug=None, name="",
                 median_filter_max_error=10, median_filter_window_size=10):
        """This class interfaces with the digital caliper.
        It reads clock and data pins and returns the value in mm.
        The caliper can be zeroed and a median outlier filter is used.
        Data packets are received in fixed intervals, so the value is read asynchronously and placed into a queue.

        Args:
            pin_data: data digital input gpio pin
            pin_clock: clock digital input gpio pin
            pin_zero: zero digital output gpio pin
            clock_bouncetime: clock debounce time in ms
            pause_time: minimum time between packets in ms
            pin_debug: gives a pulse on this pin when a data sample is taking. useful for debuggin with scope
            name: optional name for debugging purposes
            median_filter_max_error: the maximum error allowed before the median filter triggers
            median_filter_window_size: the amount of past samples considered for calculating the median
        """
        self.pin_data = pin_data
        self.pin_clock = pin_clock
        self.pin_zero = pin_zero
        self.clock_bouncetime = clock_bouncetime
        self.pause_time = pause_time
        self.pin_debug = pin_debug
        self.name = name
        self.median_filter_max_error = median_filter_max_error
        self.median_filter_window_size = median_filter_window_size

        # data buffer for current data packet
        self.current_burst_data = list()

        # keep track of clock signal interval
        self.last_clock_time = 0

        # Queue to pass reading to another thread
        # Ideally the reading should always processed before the next one is ready (queue size = 1)
        self.reading_queue = Queue(1)

        # keep track of previous readings for median filter
        self.median_filter_samples = [0 for _ in range(median_filter_window_size)]

        # Setup gpio
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_data, GPIO.IN)
        GPIO.setup(self.pin_clock, GPIO.IN)
        GPIO.setup(self.pin_zero, GPIO.OUT)
        if self.pin_debug is not None:
            GPIO.setup(self.pin_debug, GPIO.OUT)

        # Setup interrupt
        self.ignore_interrupt = True
        GPIO.add_event_detect(self.pin_clock, GPIO.RISING, callback=self.clock_callback)

    def start_listening(self):
        """Enable clock interrupt"""
        self.ignore_interrupt = False

    def reset_median_filter(self):
        """Reset past samples for median filter to all zeroes"""
        self.median_filter_samples = [0 for _ in range(self.median_filter_window_size)]

    def stop_listening(self):
        """"Disable clock interrupt"""
        self.ignore_interrupt = True
        # Clear queue (otherwise on the next start the previous value might be passed)
        with self.reading_queue.mutex:
            self.reading_queue.queue.clear()

    def get_reading(self, timeout=1):
        """
        Blocks until a value is stored in self.reading_queue by the clock callback or until timeout

        Args:
            timeout: timeout in seconds

        Returns:
            The reading in mm or None if it was filtered
        """
        bit_list = self.reading_queue.get(True, timeout)
        bit_list.reverse()
        # bits 0-2 are always 0, bit 3 is the sign where 1 = negative and 0 = positive
        # bit 4-23 needs to be converted to decimal and divided by 100 to get the position in mm (2 decimals)
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
        """Called on the clock rising edge.
        Sample the data input pin every function call.
        Data is sent in 24-bit bursts every ~100-150ms.
        If listening started mid-burst the data from that first burst will be discarded.
        """
        if self.ignore_interrupt:
            return

        if self.pin_debug is not None:
            GPIO.output(self.pin_debug, GPIO.HIGH)

        value = GPIO.input(self.pin_data)
        # If the last clock pulse was too long ago,
        # discard the current_burst_data buffer and assume a new data packet started.
        current_time = time.time() * 1000.0
        if current_time - self.last_clock_time >= self.pause_time:
            self.current_burst_data = list()
        self.last_clock_time = current_time
        # Add current data bit to buffer
        self.current_burst_data.append(value)
        # Store buffer in queue when 24 bits have been read.
        if len(self.current_burst_data) == 24:
            self.reading_queue.put(self.current_burst_data)

        if self.pin_debug is not None:
            GPIO.output(self.pin_debug, GPIO.LOW)

    def filter(self, sample):
        """Attempt to filter out random flipped bits in the data signal due to glitches.
        Uses a median outlier filter, where the current sampled is compared to the median of previous (unfiltered) samples
        If the new sample is too far away from the old sample it gets discarded

        Args:
            sample: the new data sample

        Returns: sample or None if it was discarded

        """
        # Calculate median
        sorted_list = sorted(self.median_filter_samples)
        median = sorted_list[self.median_filter_window_size // 2]

        if abs(sample - median) > self.median_filter_max_error:
            return None
        else:
            self.median_filter_samples.append(sample)
            self.median_filter_samples = self.median_filter_samples[1:]
            return sample


def bit_list_to_decimal(bit_list):
    """Convert a list of bits to a decimal number (no sign, msb on the left)"""
    out = 0
    for bit in bit_list:
        out = (out << 1) | bit
    return out
