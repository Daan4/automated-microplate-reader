import tkinter as tk
from main import start_process, stop_process, pause_process
from PIL import ImageTk, Image

class AutomatedMicroplateReaderApplication(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.grid()
        self.create_widgets()

        # Set startup values
        # todo use some logo / text ?
        self.update_image('D:\Libraries\Documents\pycharmprojects\\automated-microplate-reader\\testimage.jpg')
        self.update_status('STANDBY')

    def create_widgets(self):
        # Start button
        self.button_start = tk.Button(self, text='Start', command=start_process)
        self.button_start.grid(row=1, column=0)
        # Pause button
        self.button_pause = tk.Button(self, text='Pause', command=pause_process)
        self.button_pause.grid(row=1, column=1)
        # Stop button
        self.button_stop = tk.Button(self, text='Stop', command=stop_process)
        self.button_stop.grid(row=1, column=2)
        # Status labels
        self.label_statustext = tk.Label(self, text='Status: ')
        self.label_statustext.grid(row=0, column=0)
        self.status_stringvar = tk.StringVar(value='')
        self.label_status = tk.Label(self, textvariable=self.status_stringvar)
        self.label_status.grid(row=0, column=1)
        # Image preview container, set an image using self.update_image
        self.image_panel = tk.Label(self)

    def update_image(self, image_path):
        """

        Update the image shown on screen, downscaling it to 960 width x 540 height

        Args:
            image_path: the path to the image to display

        Returns:

        """
        img = ImageTk.PhotoImage(Image.open(image_path).resize((960, 520), Image.ANTIALIAS))
        self.image_panel.grid_forget()
        self.image_panel = tk.Label(self, image=img)
        self.image_panel.image = img
        self.image_panel.grid(row=0, column=3, rowspan=2)

    def update_status(self, status):
        """
        Update the status shown on screen

        Args:
            status: the status text to show

        Returns:

        """
        self.status_stringvar.set(status)
