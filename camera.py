from picamera import PiCamera
from picamera.exc import PiCameraError
import time
import os

class Camera:
    def __init__(self, exposure_time=1):
        """

        Args:
            exposure_time: Time to wait after taking a picture before continuing in seconds
        """
        try:
            self.camera = PiCamera()
            #self.camera.start_preview()
            #while True:
            #    time.sleep(1)
        except PiCameraError as e:
            # Camera not connected
            self.camera = None
        self.exposure_time = exposure_time

    def take_photo(self):
        """Take a photo and return the stored image path when ready"""
        # todo better image file names, maybe structured in folder per well plate and named per well
        if not os.path.exists('pics'):
            os.mkdir('pics')
        image_path = os.path.join(os.path.dirname(__file__), 'pics/well_plate_{}.jpg'.format(time.time()))
        if self.camera is not None:
            # self.camera.start_preview()
            # time.sleep(2)
            # todo return default test image
            self.camera.capture(image_path)
        return image_path
