from picamera import PiCamera
from picamera.exc import PiCameraError
import time
import os


class Camera:
    def __init__(self):
        """Interfaces to a raspberry pi camera to take pictures and save them to a given path."""
        try:
            self.camera = PiCamera()
        except PiCameraError as e:
            # Camera not connected
            self.camera = None

    def take_photo(self, filename=None):
        """Take a photo and return the stored image path when ready

        Args:
            filename: the name of the photo file.

        Returns:
            the filepath of the saved photo file
        """
        if not os.path.exists('pics'):
            os.mkdir('pics')
        if filename is None:
            image_path = os.path.join(os.path.dirname(__file__), 'pics/well_plate_{}.jpg'.format(time.time()))
        else:
            image_path = os.path.join(os.path.dirname(__file__), 'pics/{}.jpg'.format(filename))

        if self.camera is not None:
            self.camera.capture(image_path)

        return image_path
