import tkinter as tk
from main import start_process, stop_process, pause_process, z_move_camera
from PIL import ImageTk, Image
import threading
from globals import DROPDOWN_OPTIONS_DICT


class AutomatedMicroplateReaderApplication(tk.Frame):
    def __init__(self, master):
        """Tkinter frame for the automated microplate reader user interface"""
        super().__init__(master)
        self.grid()

        # Register entry validation function that only allows positive integers
        self.check_num_zsteps = (self.register(self.validate_int), '%P')

        self.create_widgets()

        # Set initial status text
        self.update_status('STANDBY')

    def create_widgets(self):
        # Well plate choice drop down
        self.label_well_plate = tk.Label(self, text='Kies well plate')
        self.label_well_plate.grid(row=1, column=0)
        self.stringvar_well_plate = tk.StringVar(value="Kies .csv bestand")
        self.dd_well_plate = tk.OptionMenu(self, self.stringvar_well_plate, *DROPDOWN_OPTIONS_DICT.keys())
        self.dd_well_plate.grid(row=1, column=1)
        # Start button
        self.button_start = tk.Button(self, text='Start', command=self._start_pressed)
        self.button_start.grid(row=2, column=0)
        # Pause button
        self.button_pause = tk.Button(self, text='Pauze', command=pause_process)
        self.button_pause.grid(row=2, column=1)
        # Stop button
        self.button_stop = tk.Button(self, text='Stop', command=stop_process)
        self.button_stop.grid(row=2, column=2)
        # Status labels
        self.label_statustext = tk.Label(self, text='Status: ')
        self.label_statustext.grid(row=0, column=0)
        self.status_stringvar = tk.StringVar(value='')
        self.label_status = tk.Label(self, textvariable=self.status_stringvar)
        self.label_status.grid(row=0, column=1)
        # Image preview container, set an image using self.update_image
        # Edit grid position in self.update_image
        self.label_photo_preview = tk.Label(self, text='Preview laatst genomen foto')
        self.label_photo_preview.grid(row=0, column=3)
        self.image_panel = tk.Label(self)
        # Z axis position controls
        self.label_focus_control = tk.Label(self, text='Camera hoogte instelling')
        self.label_focus_control.grid(row=3, column=0, columnspan=3)
        self.stringvar_num_zsteps = tk.StringVar(value=5)
        self.label_num_zsteps = tk.Label(self, text='Aantal stappen per keer')
        self.label_num_zsteps.grid(row=4, column=0)
        self.entry_num_zsteps = tk.Entry(self, textvariable=self.stringvar_num_zsteps,
                                         validate='key', validatecommand=self.check_num_zsteps)
        self.entry_num_zsteps.grid(row=4, column=1)
        self.button_z_up = tk.Button(self, text='Omhoog',
                                     command=lambda: z_move_camera(int(self.stringvar_num_zsteps.get())))
        self.button_z_up.grid(row=5, column=0)
        self.button_z_down = tk.Button(self, text='Omlaag',
                                       command=lambda: z_move_camera(-int(self.stringvar_num_zsteps.get())))
        self.button_z_down.grid(row=5, column=1)

    def _start_pressed(self):
        """Called when the start button is pressed. start_process is called in it's own thread to not block the gui"""
        threading.Thread(target=start_process, args=[DROPDOWN_OPTIONS_DICT[self.stringvar_well_plate.get()]]).start()

    def update_image(self, image_path):
        """
        Update the image shown on screen, downscaling it to 960 width x 540 height

        Args:
            image_path: the path to the image to display
        """
        img = ImageTk.PhotoImage(Image.open(image_path).resize((960, 520), Image.ANTIALIAS))
        self.image_panel.grid_forget()
        self.image_panel = tk.Label(self, image=img)
        self.image_panel.image = img  # You need to keep this explicit reference for it to work
        self.image_panel.grid(row=1, column=3, rowspan=999)

    def update_status(self, status):
        """Update the status text shown on screen

        Args:
            status: the status text to show

        """
        self.status_stringvar.set(status)

    @staticmethod
    def validate_int(new_value):
        """tk.Entry validation that only allows positive integers"""
        if new_value == '':
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False
