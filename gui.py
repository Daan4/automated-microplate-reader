import tkinter as tk
from main import start_process, stop_process, pause_process

class AutomatedMicroplateReaderApplication(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        # Start button
        self.button_start = tk.Button(self, text='Start', command=start_process)
        self.button_start.grid(row=0, column=0)
        # Pause button
        self.button_pause = tk.Button(self, text='Pause', command=pause_process)
        self.button_pause.grid(row=0, column=1)
        # Stop button
        self.button_stop = tk.Button(self, text='Stop', command=stop_process)
        self.button_stop.grid(row=0, column=2)

