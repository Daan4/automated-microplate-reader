from picamera import PiCamera
from picamera.exc import PiCameraError
import time
import os

class Camera:
    def __init__(self, sleep_time=5):
        """

        Args:
            sleep_time: Time to wait after taking a picture before continuing in seconds
        """
        try:
            self.camera = PiCamera()
        except PiCameraError:
            # Camera not connected
            self.camera = None
        self.sleep_time = sleep_time

    def take_photo(self):
        """Take a photo and return the stored image path when ready"""
        # todo better image file names, maybe structured in folder per well plate and named per well
        image_path = os.path.join(os.path.dirname(__file__), 'pics/well_plate_{}.jpg'.format(time.time()))
        if self.camera is not None:
            # todo return default test image
            self.camera.capture(image_path)
        time.sleep(self.sleep_time)
        return image_path
