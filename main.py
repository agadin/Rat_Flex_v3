import shutil
import customtkinter as ctk
import redis
import multiprocessing.shared_memory as sm
from tkinter import Canvas, Frame, Scrollbar, filedialog
from PIL import Image, ImageTk
from tkinter import Canvas, StringVar
import cv2
import queue
import time
import struct
import csv
from collections import defaultdict
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import seaborn as sns
from tkinter import ttk
import matplotlib.ticker as ticker
import datetime
import tkinter as tk
import subprocess
import queue
import threading
import sys
import os
import signal
import psutil
from CTkMessagebox import CTkMessagebox
import argparse
import numpy as np


# Global variable to store process reference
protocol_process = None

shm = None

from arcdrawer import AdvancedCurvedSlider
output_queue = queue.Queue()

# Define the format for packing and unpacking data


# Function to initialize resources
# Function to initialize resources
def is_protocol_running():
    for proc in psutil.process_iter(['cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if isinstance(cmdline, list) and any("protocol_runner.py" in part for part in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


# Function to start protocol_runner.py
import subprocess
import threading

def start_protocol_runner(app):
    global protocol_process

    #clear protocol_runner_stdout.log and protocol_runner_stderr.log
    with open("protocol_runner_stdout.log", "w") as f:
        f.write("")

    with open("protocol_runner_stderr.log", "w") as f:
        f.write("")
        
    # Open log files for writing
    stdout_log_file = open("protocol_runner_stdout.log", "w")
    stderr_log_file = open("protocol_runner_stderr.log", "w")

    if sys.platform.startswith('win'):
        protocol_process = subprocess.Popen(
            [sys.executable, "protocol_runner.py"],
            stdout=stdout_log_file,
            stderr=subprocess.PIPE,  # Capture stderr
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        try:
            protocol_process = subprocess.Popen(
                ["xterm", "-e", f"bash -c '{sys.executable} protocol_runner.py; exit'"],
                stdout=stdout_log_file,
                stderr=subprocess.PIPE,  # Capture stderr
                text=True,
                preexec_fn=os.setsid
            )
        except FileNotFoundError:
            protocol_process = subprocess.Popen(
                [sys.executable, "protocol_runner.py"],
                stdout=stdout_log_file,
                stderr=subprocess.PIPE,  # Capture stderr
                text=True
            )

    # Function to continuously write stderr to the log file
    def log_stderr(pipe, log_file):
        for line in iter(pipe.readline, ''):
            log_file.write(line)
            log_file.flush()
        pipe.close()

    # Start a thread to handle stderr logging
    threading.Thread(target=log_stderr, args=(protocol_process.stderr, stderr_log_file), daemon=True).start()
# Function to read process output


def read_calibration_data(file_path):
    calibration_data = defaultdict(dict)
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            angle = float(row['angle'])
            force = float(row['force'])
            direction = row['direction'].strip().lower()
            calibration_data[direction][angle] = force
    return calibration_data




import os
from tkinter import Scrollbar
from tkinter import Frame


class ProtocolViewer(ctk.CTkFrame):
    def __init__(self, master, protocol_folder, protocol_var, app, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.app = app
        self.protocol_folder = protocol_folder
        self.protocol_var = protocol_var

        self.protocol_steps = []  # List of parsed protocol steps
        self.step_widgets = []  # References to step widgets for updating opacity

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=400, height=800)
        self.scrollable_frame.pack(fill="both", expand=True)

        # Dynamically update current step opacity
        self.update_current_step()

    def get_label_text_color(self):
        mode = ctk.get_appearance_mode()
        return "black" if mode == "Light" else "white"

    def load_protocol(self, protocol_var):
        # Clear existing steps
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.step_widgets = []
        self.protocol_steps = []
        print("Loading protocol:", protocol_var)
        # Get the protocol path
        protocol_path = os.path.join(self.protocol_folder, protocol_var)
        self.protocol_var = protocol_var

        # Read and parse the protocol
        if os.path.exists(protocol_path):
            with open(protocol_path, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if i >= 25:  # Limit to the first 25 steps
                    break
                step_num = i + 1
                step_details = self.parse_step(line.strip())
                self.protocol_steps.append((step_num, *step_details))
                self.create_step_widget(step_num, *step_details)

    def parse_step(self, line):
        """Parse a protocol step from the line."""
        if ":" in line:
            step_name, details = line.split(":", 1)
        else:
            step_name, details = line, ""
        return step_name, details.strip()

    def create_step_widget(self, step_num, step_name, details):
        """Create a rounded box for a protocol step."""
        frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        frame.pack(fill="x", padx=5, pady=5)

        # Step number
        text_color = self.get_label_text_color()

        step_num_label = ctk.CTkLabel(frame, text=f"Step {step_num}", width=10, text_color=text_color)
        step_name_label = ctk.CTkLabel(frame, text=f"{step_name}: {details}", anchor="w", text_color=text_color)

        # Step name and details
        step_name_label = ctk.CTkLabel(frame, text=f"{step_name}: {details}", anchor="w")
        step_name_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Checkbox
        checkbox_var = ctk.BooleanVar(value=True)
        checkbox = ctk.CTkCheckBox(
            frame,
            text="",
            variable=checkbox_var,
            command=lambda: self.app.redis_client.set(f"checkedbox_{step_num}", int(checkbox_var.get()))
        )
        checkbox.grid(row=0, column=2, padx=5, pady=5)

        self.step_widgets.append((frame, step_num))

    def reload_font_colors(self):
        color = self.get_label_text_color()
        for frame in self.scrollable_frame.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    widget.configure(text_color=color)

    def update_current_step(self):
        """Update opacity dynamically based on the current step."""
        try:
            current_step = self.app.redis_client.get("current_step")
            current_step = int(current_step) if current_step else None
        except (ValueError, TypeError):
            current_step = None

        # Update frame background color to simulate opacity
        for frame, step_num in self.step_widgets:
            if current_step == step_num:
                frame.configure(fg_color="lightblue")  # Simulate higher opacity
            else:
                frame.configure(fg_color="lightgray")  # Simulate lower opacity
        current_mode = ctk.get_appearance_mode()
        if getattr(self, "_last_mode", None) != current_mode:
            self._last_mode = current_mode
            self.reload_font_colors()

        self.after(500, self.update_current_step)  # Check every 500ms


class App(ctk.CTk):
    def __init__(self):
        global start_protocol
        super().__init__()
        print(f" {start_protocol}")
        if start_protocol:
            print("Starting protocol runner...")
            start_protocol_runner(self)
        self.last_update_time = time.time()
        self.update_interval = 1 #second
        self.advanced_slider = None
        self.angle_force_data = []
        self.running = True  # Initialize the running attribute
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.initialize_resources()

        icon_path = os.path.abspath('./img/ratfav.ico')
        png_icon_path = os.path.abspath('./img/ratfav.png')
        try:
            img = Image.open(icon_path)
            img.save(png_icon_path)
            self.icon_img = ImageTk.PhotoImage(file=png_icon_path)
            self.iconphoto(False, self.icon_img)
        except Exception as e:
            print(f"Failed to set icon: {e}")
        self.queue = queue.Queue()
        self.step_time_int = None
        self.clock_values = False
        self.timing_clock = None
        self.step_time = None
        self.none_count = 0
        self.total_steps = 0
        self.show_boot_animation()

        # Stationary variables
        self.angle_special = []
        self.force_special = []
        self.poll_rate = 0.2
        self.time_data = []
        self.angle_data = []
        self.force_data = []


        # Window configuration
        self.title("RatFlex")
        self.resizable(False, False)
        # Calculate the center of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (1800 // 2)
        y_coordinate = (screen_height // 2) - (920 // 2)

        self.geometry(f"1800x920+{x_coordinate}+{y_coordinate}")


        # Top navigation bar
        # --------------------------
        # Top Navigation Bar Section
        # --------------------------

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=5)

        # Left frame for the logo
        self.nav_left_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.nav_left_frame.pack(side="left")

        # Right frame for nav buttons
        self.nav_right_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.nav_right_frame.pack(side="right", padx=20)

        self.data_recording = False
        self.recorded_graph_times = []
        self.recorded_input_pressures = []
        self.recorded_pressure1s = []
        self.recorded_pressure2s = []

        # --- Logo on Left Side ---
        # Create a white icon from the SVG file
        icon_size = (20, 20)

        # Create CTkImage for the first logo (lake logo)
        logo_image = ctk.CTkImage(
            light_image=Image.open("./img/lakelogo_dark.png"),  # For light mode
            dark_image=Image.open("./img/lakelogo.png"),  # For dark mode
            size=(60, 60)
        )

        # Create the first CTkButton with the lake logo
        self.logo_button = ctk.CTkButton(
            self.nav_left_frame,
            image=logo_image,
            text="",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_home
        )
        self.logo_button.pack(side="left", padx=1)


        # Create CTkImage objects
        home_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-home_dark.png"),
            dark_image=Image.open("./img/fa-home.png"),
            size=(20, 20)
        )

        protocol_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-tools_dark.png"),
            dark_image=Image.open("./img/fa-tools.png"),
            size=(20, 20)
        )

        calibrate_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-tachometer-alt_dark.png"),
            dark_image=Image.open("./img/fa-tachometer-alt.png"),
            size=(20, 20)
        )

        settings_icon = ctk.CTkImage(
            light_image=Image.open("./img/fa-cog_dark.png"),
            dark_image=Image.open("./img/fa-cog.png"),
            size=(20, 20)
        )

        # --- Navigation Buttons on Right Side ---
        self.settings_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Settings",
            text_color="white",
            image=settings_icon,
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_settings
        )
        self.settings_button.pack(side="right", padx=20)

        self.inspector_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Data Inspector",
            text_color="white",
            image=calibrate_icon,
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_inspector
        )
        self.inspector_button.pack(side="right", padx=20)

        self.protocol_builder_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Protocol Builder",
            image=protocol_icon,
            text_color="white",
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_protocol_builder
        )
        self.protocol_builder_button.pack(side="right", padx=20)

        self.home_button = ctk.CTkButton(
            self.nav_right_frame,
            text="Home",
            image=home_icon,
            text_color="white",
            compound="left",
            fg_color="transparent",
            hover_color="gray",
            command=self.show_home
        )
        self.home_button.pack(side="right", padx=20)

        # Main content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", pady=10)

        self.home_frame = None
        self.protocol_builder_frame = None
        self.inspector_frame = None
        self.settings_frame = None

        self.show_home()

    def run_calibration(self):
        self.protocol_var = ctk.StringVar(value="calibrate_protocol.txt")
        self.run_protocol("calibrate_protocol.txt")
        self.timing_clock = time.time()

    def show_overlay_notification(self, message, auto_dismiss_ms=5000, color_disp="green"):
            notification = ctk.CTkFrame(self, fg_color=color_disp, corner_radius=10)
            # Position the notification slightly higher at the top center
            notification.place(relx=0.5, rely=0.05, anchor="n")
            label = ctk.CTkLabel(notification, text=message, text_color="white", font=("Arial", 12))
            label.pack(side="left", padx=(10, 5), pady=5)
            close_button = ctk.CTkButton(
                notification,
                text="X",
                width=20,
                fg_color="transparent",
                text_color="white",
                command=notification.destroy
            )
            close_button.pack(side="right", padx=(5, 10), pady=5)
            if auto_dismiss_ms is not None:
                notification.after(auto_dismiss_ms, notification.destroy)

    def show_boot_animation(self):
        # Remove title bar for splash screen effect
        self.overrideredirect(True)

        # Set the desired window size (720p video dimensions)
        window_width = 1280
        window_height = 720

        # Calculate the center of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (window_width // 2)
        y_coordinate = (screen_height // 2) - (window_height // 2)

        # Position the window at the center of the screen
        self.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Create a canvas for video and text overlay
        canvas = Canvas(self, bg="black", highlightthickness=0)
        canvas.pack(expand=True, fill="both")

        # Variable for overlay text
        setup_status = StringVar()
        setup_status.set("")

        # Function to play video
        def play_video():
            video_path = "./img/STL_Boot_2.mp4"
            video = cv2.VideoCapture(video_path)

            setup_steps = [
                ("", 4),
                ("", 2),
                ("", 4),
                ("", 6),
            ]

            current_step_index = 0
            next_step_time = setup_steps[current_step_index][1]
            start_time = time.time()

            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break

                # Convert frame to ImageTk format
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image = ImageTk.PhotoImage(image)

                # Display video frame on the canvas
                canvas.create_image(0, 0, anchor="nw", image=image)
                canvas.image = image  # Keep a reference to avoid garbage collection

                # Update overlay text based on time
                elapsed_time = time.time() - start_time
                if current_step_index < len(setup_steps) and elapsed_time >= next_step_time:
                    setup_status.set(setup_steps[current_step_index][0])
                    current_step_index += 1
                    if current_step_index < len(setup_steps):
                        next_step_time = setup_steps[current_step_index][1]

                # Overlay text on the canvas
                canvas.delete("text")
                canvas.create_text(
                    canvas.winfo_width() // 2,
                    (canvas.winfo_height() // 2)-50,
                    text=setup_status.get(),
                    font=("Arial", 24),
                    fill="white",
                    tags="text",
                )

                self.update()
                time.sleep(1 / video.get(cv2.CAP_PROP_FPS))


            video.release()
            canvas.destroy()
        # Start the video playback
        play_video()
        self.overrideredirect(False)

    def initialize_resources(self):


        # Initialize CustomTkinter
        ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")

        # Shared memory and Redis configuration
        shm_name = 'shared_data'
        self.fmt = 'i d d d'
        shm_size = struct.calcsize(self.fmt)

        # Try to access shared memory
        try:
            self.shm = sm.SharedMemory(name='shared_memory')
        except FileNotFoundError:
            print("Shared memory not found. Creating new shared memory block.")
            self.redis_client.set("shared_memory_error", 1)
            time.sleep(1)
            try:
                self.shm = sm.SharedMemory(name=shm_name)
            except FileExistsError:
                # Unlink the existing shared memory and create a new one
                existing_shm = sm.SharedMemory(name=shm_name)
                existing_shm.unlink()
                self.shm = sm.SharedMemory(name=shm_name)
                
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def save_to_redis_dict(self, redis_key, variable_name, value):
        # Retrieve the dictionary from Redis
        redis_dict = self.redis_client.hgetall(redis_key)

        # Update the dictionary
        redis_dict[variable_name] = value

        # Save the updated dictionary back to Redis
        self.redis_client.hset(redis_key, mapping=redis_dict)

    def run_protocol(self, protocol_path):
        # add ./protocols/ to the protocol path
        data_path = "data.csv"
        #running protocol_path
        self.show_overlay_notification(f"Running {protocol_path}...", auto_dismiss_ms=2000)
        if os.path.exists(data_path):
            try:
                if os.path.getsize(data_path) > 0:
                    msg = CTkMessagebox(
                        title="Existing Data Detected",
                        message="data.csv is not empty.\n\nWhat would you like to do?",
                        icon="warning",
                        option_1="Wipe & Continue",
                        option_2="Keep & Continue",
                        option_3="Cancel"
                    )

                    response = msg.get()
                    if response == "Cancel":
                        return
                    elif response == "Wipe & Continue":
                        open(data_path, 'w').close()
                        print("data.csv wiped.")
                    else:
                        print("Keeping existing data.")

            except Exception as e:
                CTkMessagebox(title="Error", message=f"Could not read data.csv:\n{e}", icon="cancel")

        protocol_path = os.path.join('./protocols', protocol_path)
        self.redis_client.set('protocol_trigger', protocol_path)
        print(f"Triggered protocol: {protocol_path}")

    def read_shared_memory(self):
        try:
            current_protocol_out = self.redis_client.get("current_protocol_out")
            # Check if timing_clock has a value
            if self.timing_clock is not None:
                if not current_protocol_out:  # Check if current_protocol_out is None or empty
                    self.none_count += 1
                else:
                    self.none_count = 0
                if self.none_count == 6:
                    self.timing_clock = None
                    self.none_count = 0
            data = bytes(self.shm.buf[:struct.calcsize(self.fmt)])
            stop_flag, step_count, current_angle, current_force = struct.unpack(self.fmt, data)
            return step_count, current_angle, current_force
        except Exception as e:
            print(f"Error reading shared memory: {e}")
            return None


    def show_home(self):
        self.clear_content_frame()

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=300)
        self.sidebar_frame.pack(side="left", fill="y", padx=15)

        # Calibrate button
        self.calibrate_button = ctk.CTkButton(self.sidebar_frame, text="Calibrate", command=self.run_calibration)
        self.calibrate_button.pack(pady=5, padx=15)

        # Protocol selector
        self.protocol_label = ctk.CTkLabel(self.sidebar_frame, text="Select a Protocol:")
        self.protocol_label.pack(pady=5, padx=15)

        self.protocol_folder = './protocols'
        self.protocol_files = [f for f in os.listdir(self.protocol_folder) if os.path.isfile(os.path.join(self.protocol_folder, f))]
        # remove calibrate_protocol.txt from the list if it exists
        if "calibrate_protocol.txt" in self.protocol_files:
            self.protocol_files.remove("calibrate_protocol.txt")

        self.protocol_var = ctk.StringVar(value=self.protocol_files[0])


        # Update the displayed value of protocol_var dynamically
        self.displayed_protocol_var = ctk.StringVar(value=self.protocol_var.get() if self.protocol_var.get() != "calibrate_protocol.txt" else "")

        self.protocol_dropdown = ctk.CTkComboBox(
            self.sidebar_frame,
            values=self.protocol_files,
            variable=self.displayed_protocol_var,
            width=200
        )
        self.protocol_dropdown.pack(pady=5)

        self.run_button = ctk.CTkButton(self.sidebar_frame, text="Run Protocol", command=self.run_protocol_init)
        self.run_button.pack(pady=5)

        # Stop button
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="Stop", command=self.stop_protocol)
        self.stop_button.pack(pady=15)

        # create an input field for the user to input the animal ID and save it to redis when it is 4 numbers long
        self.animal_id_var = ctk.StringVar( value="Animal ID")
        self.animal_id_entry = ctk.CTkEntry(self.sidebar_frame, textvariable=self.animal_id_var, placeholder_text="Animal ID")
        self.animal_id_entry.pack(pady=5, padx=15)

        def save_animal_id_to_redis(*args):
            animal_id = self.animal_id_var.get()
            if animal_id and animal_id != "Animal ID":
                self.save_to_redis_dict('set_vars', 'animal_id', animal_id)

        self.animal_id_var.trace("w", save_animal_id_to_redis)

        self.button_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.button_frame.pack(padx=15, pady=5, fill="x")

        # Right and Left Arm Toggle Buttons
        self.arm_selection = ctk.StringVar(value="")  # To track the current selection

        def toggle_arm_selection(selection):
            """Toggle the arm selection and update Redis."""
            if self.arm_selection.get() == selection:
                # Unselect if clicked again
                self.arm_selection.set("")
                self.redis_client.set("selected_arm", "")  # Clear Redis value
            else:
                self.arm_selection.set(selection)
                self.redis_client.set("selected_arm", selection)

            # Update button states
            update_button_states()

        def update_button_states():
            """Update the visual state of the buttons."""
            if self.arm_selection.get() == "Right Arm":
                self.run_protocol("right_arm_jog.txt")
                right_button.configure(fg_color="blue", text_color="white")
                left_button.configure(fg_color="gray", text_color="black")
            elif self.arm_selection.get() == "Left Arm":
                self.run_protocol("left_arm_jog.txt")
                right_button.configure(fg_color="gray", text_color="black")
                left_button.configure(fg_color="blue", text_color="white")
            else:
                right_button.configure(fg_color="gray", text_color="black")
                left_button.configure(fg_color="gray", text_color="black")

        right_button = ctk.CTkButton(
            self.button_frame,
            text="Right Arm",
            command=lambda: toggle_arm_selection("Right Arm"),
            fg_color="gray",  # Default color
            text_color="black",
            corner_radius=10,
            width=100
        )
        right_button.pack(side="left", padx=20)

        left_button = ctk.CTkButton(
            self.button_frame,
            text="Left Arm",
            command=lambda: toggle_arm_selection("Left Arm"),
            fg_color="gray",  # Default color
            text_color="black",
            corner_radius=10,
            width=100
        )
        left_button.pack(side="right", padx=20)

        # Update button states initially
        update_button_states()

        # Have four three in the blank fields that allow the users to input values into redis. Stack these vertically and automatically update the redis values when the user inputs a value.
        # Four input fields for Redis values
        default_texts = ["input_0", "input_1", "input_2", "input_3"]  # Replace with your default texts
        self.redis_inputs = []
        for i in range(4):
            input_var = ctk.StringVar(value=default_texts[i])  # Set the initial value
            input_entry = ctk.CTkEntry(self.sidebar_frame, textvariable=input_var, placeholder_text=f"input_{i}")
            input_entry.pack(pady=5, padx=15)
            input_var.trace("w", lambda name, index, mode, var=input_var, idx=i: self.save_to_redis_dict('set_vars', f"input_{idx}", var.get()))
            self.redis_inputs.append(input_var)

        # Create a container frame for the curved slider in the sidebar
        slider_container = ctk.CTkFrame(self.sidebar_frame)
        slider_container.pack(pady=5, padx=15, fill="x")
        # Create the AdvancedCurvedSlider instance, passing self as the parent_app
        self.advanced_slider = AdvancedCurvedSlider(slider_container, width=300, height=150, min_val=10, max_val=170,parent_app=self)
        self.advanced_slider.pack()

        self.darkmodeToggle = False

        if self.darkmodeToggle:
            # Light/dark mode automatic toggle
            current_hour = datetime.datetime.now().hour
            default_mode = "Dark" if current_hour >= 18 or current_hour < 6 else "Light"
            ctk.set_appearance_mode(default_mode)
        else:
            ctk.set_appearance_mode("Dark")

        # Light/Dark mode toggle
        self.mode_toggle = ctk.CTkSwitch(self.sidebar_frame, text="Light/Dark Mode", command=self.toggle_mode)
        self.mode_toggle.pack(pady=5)

        self.status_frame = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color="gray",
            corner_radius=12,
            height=100,  # Set height to make it a square
            width=100,  # Set width to match height
            border_color="black",  # Add black border
            border_width=2  # Set border width
        )
        self.status_frame.place(relx=0.5, rely=1.0, anchor="s", y=-20)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="PR",
            font=("Arial", 12)
        )
        self.status_label.pack(expand=True)
        self.status_frame.place(relx=0.5, rely=1.0, anchor="s", y=-20)


        # Main content area
        self.main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_frame.pack(side="left", expand=True, fill="both", padx=10)

        self.protocol_name_label = ctk.CTkLabel(self.main_frame, text="Current Protocol: None", anchor="w", font=("Arial", 35, "bold"))
        self.protocol_name_label.pack(pady=10, padx=20, anchor="w")

        display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        display_frame.pack(pady=5)

        # Style for all three displays
        display_style = {
            "width": 200,
            "height": 100,
            "corner_radius": 20,
            "fg_color": "lightblue",
            "text_color": "black",
            "font": ("Arial", 50, "bold"),
        }

        # Create and pack time display
        self.time_display = ctk.CTkLabel(display_frame, text="Time: N/A", **display_style)
        self.time_display.grid(row=0, column=0, padx=10, pady=5)
        self.time_display.bind("<Button-1>", lambda e: setattr(self, 'clock_values', False))

        self.protocol_step_counter = ctk.CTkLabel(display_frame, text="Step: N/A", **display_style)
        self.protocol_step_counter.grid(row=0, column=4, padx=10, pady=5)

        # Create and pack step count display
        self.step_display = ctk.CTkLabel(display_frame, text="Steps: N/A", **display_style)
        self.step_display.grid(row=0, column=1, padx=10, pady=5)

        # Create and pack angle display
        self.angle_display = ctk.CTkLabel(display_frame, text="Angle: N/A", **display_style)
        self.angle_display.grid(row=0, column=2, padx=10, pady=5)

        # Create and pack force display
        self.force_display = ctk.CTkLabel(display_frame, text="Force: N/A", **display_style)
        self.force_display.grid(row=0, column=3, padx=10, pady=5)


        self.segmented_button = ctk.CTkSegmentedButton(self.main_frame, values=["Angle v Force", "Simple", "All"], command=self.update_graph_view)
        self.segmented_button.set("Angle v Force")  # Set default selection
        self.segmented_button.pack(pady=10)

        # Placeholder for graphs
        self.graph_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.graph_frame.pack(expand=True, fill="both", pady=10)

        self.clear_button = ctk.CTkButton(self.main_frame, text="Clear", command=self.clear_graphs)
        self.clear_button.pack(pady=10)

        # Start background threads
        self.running = True
        self.update_thread = Thread(target=self.update_shared_memory)
        # self.calibration_thread = Thread(target=self.update_displays)
        self.update_thread.start()
        # self.calibration_thread.start()

        self.update_graph_view("Angle v Force")  # Initialize with default view

        print( "protocol: ", self.protocol_var.get())

        self.initialize_protocol_viewer()
        self.process_queue()


    def process_queue(self):
        try:
            while not self.queue.empty():
                data = self.queue.get_nowait()
                self.update_displays(*data)
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def initialize_protocol_viewer(self):
        # Initialize ProtocolViewer directly
        self.protocol_viewer = ProtocolViewer(
            self.main_frame,
            protocol_folder=self.protocol_folder,
            protocol_var=self.protocol_var,
            app=self  # Pass the current app instance
        )

        self.protocol_viewer.pack(fill="both", expand=True, pady=10)

        # Trace for protocol_var to update ProtocolViewer when protocol changes
        self.protocol_var.trace("w", self.update_protocol_viewer)

    def update_protocol_viewer(self, *args):
        # Update the protocol viewer synchronously when protocol_var changes
        protocol_name = self.protocol_var.get()
        print(f"Updating ProtocolViewer with: {protocol_name}")  # Debug print
        self.protocol_viewer.load_protocol(protocol_name)

    def create_step_box(self, step_number, command):
        step_frame = ctk.CTkFrame(self.protocol_steps_container, corner_radius=10, fg_color="lightblue")
        step_frame.pack(fill="x", pady=5, padx=10)

        step_number_label = ctk.CTkLabel(step_frame, text=f"Step {step_number}", font=("Arial", 14))
        step_number_label.pack(side="left", padx=10)

        command_label = ctk.CTkLabel(step_frame, text=command, font=("Arial", 14))
        command_label.pack(side="left", expand=True)

        timer_label = ctk.CTkLabel(step_frame, text="00:00", font=("Arial", 14))
        timer_label.pack(side="right", padx=10)

        self.update_timer(timer_label, step_number)

    def update_timer(self, timer_label, step_number):
        def update():
            current_step = self.redis_client.get("current_step")
            if current_step and int(current_step.split()[1]) == step_number:
                elapsed_time = int(time.time() - start_time)
                minutes, seconds = divmod(elapsed_time, 60)
                timer_label.configure(text=f"{minutes:02}:{seconds:02}")
            self.after(1000, update)

        start_time = time.time()
        update()

    def show_protocol_builder(self):
        """Display the protocol builder page with a sidebar and main content area."""
        self.clear_content_frame()

        # Main frame for protocol builder (sidebar + main content)
        self.pb_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pb_frame.pack(fill="both", expand=True, pady=10)

        # -------------------------------
        # Sidebar on the left for builder controls
        # -------------------------------
        self.pb_sidebar = ctk.CTkFrame(self.pb_frame, width=300)
        self.pb_sidebar.pack(side="left", fill="y", padx=15, pady=10)

        # Dropdown at the top: "Create New" + protocol .txt files in ./protocols/
        protocol_folder = "./protocols"
        # List only the txt files
        protocol_files = [f for f in os.listdir(protocol_folder) if f.endswith(".txt")]
        dropdown_options = ["Create New"] + protocol_files
        self.pb_mode_var = ctk.StringVar(value="Create New")
        self.pb_dropdown = ctk.CTkComboBox(
            self.pb_sidebar,
            values=dropdown_options,
            variable=self.pb_mode_var,
            command=self.on_pb_dropdown_change
        )
        self.pb_dropdown.pack(pady=10, padx=10)

        # Initialize builder state: "create" (default) or "edit"
        self.builder_mode = "create"  # This will be set to "edit" if a protocol file is selected.
        self.current_protocol_steps = []  # List to store protocol steps (each row from the file)

        # -------------------------------
        # Button grid: six buttons arranged in 2 columns x 3 rows
        # -------------------------------
        self.pb_buttons_frame = ctk.CTkFrame(self.pb_sidebar)
        self.pb_buttons_frame.pack(pady=10, padx=10)

        button_names = ["Description", "Cyclic", "Scratch", "LLM", "Flow", "Other"]
        self.pb_buttons = {}
        for i, name in enumerate(button_names):
            row = i // 2  # two columns per row
            col = i % 2
            btn = ctk.CTkButton(
                self.pb_buttons_frame,
                text=name,
                command=lambda n=name: self.on_pb_button_click(n)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            self.pb_buttons[name] = btn

        # Set the default selected button and update the button colors
        self.current_pb_selection = "Description"
        self.update_pb_button_states()

        # -------------------------------
        # Main content area for building the protocol
        # -------------------------------
        self.pb_main = ctk.CTkFrame(self.pb_frame, fg_color="transparent")
        self.pb_main.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Display the default builder view (e.g., Description mode)
        self.show_description_builder()

    # -----------------------------------------------------------------
    # Callback: When the dropdown selection changes.
    # -----------------------------------------------------------------
    def on_pb_dropdown_change(self, value):
        """
        Called when the protocol dropdown value changes.
        If "Create New" is selected, we enter create mode.
        Otherwise, we are in edit mode and we load the selected file's steps.
        """
        if value == "Create New":
            self.builder_mode = "create"
            self.current_protocol_steps = []
            print("Protocol Builder in CREATE mode.")
            # Update main content to reflect the create mode view
            self.show_description_builder()
        else:
            self.builder_mode = "edit"
            protocol_path = os.path.join("./protocols", value)
            try:
                with open(protocol_path, "r") as f:
                    # Read nonempty, stripped lines as protocol steps
                    self.current_protocol_steps = [line.strip() for line in f if line.strip()]
                print(f"Loaded protocol steps from '{value}':")
                print(self.current_protocol_steps)
            except Exception as e:
                print(f"Error loading protocol '{value}': {e}")
                self.current_protocol_steps = []
            # Update main content as needed (for now, default to description view)
            self.show_description_builder()

    # -----------------------------------------------------------------
    # Callback: When one of the six builder buttons is clicked.
    # -----------------------------------------------------------------
    def on_pb_button_click(self, button_name):
        # Update the current selection and change button colors accordingly.
        self.current_pb_selection = button_name
        self.update_pb_button_states()

        print(f"Builder button clicked: {button_name}")

        if button_name == "Description":
            self.show_description_builder()

        elif button_name == "Cyclic":
            if self.builder_mode == "create":
                # In create mode, call the (to-be-implemented) cyclic builder function
                self.build_cyclic_create_mode()
            else:  # edit mode
                # In edit mode, analyze the current protocol steps
                allowed_commands = {"wait", "move_to_force", "move_to_angle_jog", "move_to_angle"}
                unique_commands = set()
                for step in self.current_protocol_steps:
                    if ":" in step:
                        # Get the command name (normalize spaces and case)
                        command = step.split(":", 1)[0].strip().lower().replace(" ", "_")
                        if command in allowed_commands:
                            unique_commands.add(command)
                print(f"Unique commands found: {unique_commands}")
                if len(unique_commands) > 2:
                    # More than two unique commands are present so show an error message
                    self.show_popup("Error",
                                    "For cyclic mode in edit mode, the protocol must have only two unique commands.")
                elif len(unique_commands) == 2:
                    # Exactly two unique commands: proceed with the cyclic edit mode
                    self.build_cyclic_edit_mode()
                else:
                    self.show_popup("Error", "Not enough commands for a valid cyclic protocol.")

        elif button_name in ["Scratch", "LLM", "Flow", "Other"]:
            # For now, simply show an informational popup.
            self.show_popup("Info", f"'{button_name}' mode is not yet implemented.")

    # -----------------------------------------------------------------
    # Helper function to update the button colors.
    # -----------------------------------------------------------------
    def update_pb_button_states(self):
        """
        Update the appearance of the builder buttons.
        The currently selected button is highlighted (e.g., in blue),
        and the others are set to the default color (e.g., gray).
        """
        for name, btn in self.pb_buttons.items():
            if name == self.current_pb_selection:
                btn.configure(fg_color="blue", text_color="white")
            else:
                btn.configure(fg_color="gray", text_color="black")

    # -----------------------------------------------------------------
    # The following helper methods update the main content area.
    # They are placeholders to be expanded later.
    # -----------------------------------------------------------------
    def show_description_builder(self):
        """Display the Description builder view in the main content area."""
        # Clear any existing widgets in the main content area.
        for widget in self.pb_main.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(self.pb_main, text="Description Builder Mode (to be implemented)")
        label.pack(pady=20, padx=20)

    def build_cyclic_create_mode(self):
        """Placeholder for cyclic create mode functionality."""
        for widget in self.pb_main.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(self.pb_main, text="Cyclic Create Mode (to be implemented)")
        label.pack(pady=20, padx=20)

    def build_cyclic_edit_mode(self):
        """Placeholder for cyclic edit mode functionality (when in edit mode and exactly two allowed commands are found)."""
        for widget in self.pb_main.winfo_children():
            widget.destroy()
        label = ctk.CTkLabel(self.pb_main, text="Cyclic Edit Mode (to be implemented)")
        label.pack(pady=20, padx=20)

    def get_trials(self):
        data_dir = "./data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        # Get all subfolders in the data directory
        folders = [folder for folder in os.listdir(data_dir)
                   if os.path.isdir(os.path.join(data_dir, folder))]

        # Custom sort key that extracts date, animal, and trial
        def sort_key(folder):
            parts = folder.split("_")
            if len(parts) >= 3:
                # Extract parts
                date_str, animal_str, trial_str = parts[0], parts[1], parts[2]
                try:
                    # Convert to integers (assuming valid format)
                    date_val = int(date_str)  # e.g., 20250124
                    animal_val = int(animal_str)  # e.g., 0 or 1234
                    trial_val = int(trial_str)  # e.g., 2
                except ValueError:
                    # If conversion fails, send it to the end of the list
                    date_val, animal_val, trial_val = float('inf'), float('inf'), float('inf')
                return (date_val, animal_val, trial_val)
            else:
                # If the folder name doesn't match the format, push it to the end.
                return (float('inf'), float('inf'), float('inf'))

        sorted_folders = sorted(folders, key=sort_key)
        return sorted_folders if sorted_folders else ["No Trials Found"]

    def no_trials_popup(self):
        # Create a popup window
        popup = ctk.CTkToplevel(self)
        popup.title("No Trials Found")
        popup.geometry("400x200")

        label = ctk.CTkLabel(popup, text="No trials found. What would you like to do?", font=("Arial", 14))
        label.pack(pady=20)

        # Return to Home Page button
        return_button = ctk.CTkButton(popup, text="Return to Home Page",
                                      command=lambda: [popup.destroy(), self.show_home()])
        return_button.pack(pady=10)

        # Upload Data button
        upload_button = ctk.CTkButton(popup, text="Upload Data", command=lambda: [popup.destroy(), self.upload_csv()])
        upload_button.pack(pady=10)

    import shutil

    def upload_csv(self):
        # Open file browser to select a CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return  # User canceled the file dialog

        # Create the imported folder inside the data directory
        imported_folder = os.path.join("./data", "imported")
        if not os.path.exists(imported_folder):
            os.makedirs(imported_folder)

        # Clear out the imported folder
        for file in os.listdir(imported_folder):
            file_path_to_remove = os.path.join(imported_folder, file)
            os.remove(file_path_to_remove)

        # Copy the selected CSV file into the imported folder
        new_file_path = os.path.join(imported_folder, os.path.basename(file_path))
        shutil.copy(file_path, new_file_path)

        # Set the dropdown to "imported"
        self.trial_dropdown.set("imported")
        self.load_trial("imported")

    def load_trial(self, selected_trial):
        if selected_trial == "No Trials Found":
            ctk.messagebox.showwarning("Warning", "No trials found. Please run a protocol or upload manually.")
            return
        self.trial_path = os.path.join("./data", selected_trial)
        print(f"Loading trial: {self.trial_path}")
        csv_file = next((f for f in os.listdir(self.trial_path) if f.endswith('.csv')), None)
        if not csv_file:
            ctk.messagebox.showerror("Error", "CSV file not found in the selected trial folder.")
            return
        headers = ['Time', 'Angle', 'Force', 'raw_Force', 'Motor_State', 'Direction', 'Protocol_Step']
        data = pd.read_csv(os.path.join(self.trial_path, csv_file), header=None, names=headers)
        data['Protocol_Step'] = data['Protocol_Step'].astype(str)

        if data['Protocol_Step'].str.len().eq(0).any():
            data['Row_Type'] = data['Protocol_Step'].apply(lambda x: '6_column' if x == '' else '7_column')

            data['Force'] = pd.to_numeric(data['Force'], errors='coerce')
            data['raw_Force'] = pd.to_numeric(data['raw_Force'], errors='coerce')

            def fix_data_rows(data):
                fixed_data = []
                last_diff = 0

                for _, row in data.iterrows():
                    if row['Row_Type'] == '7_column':
                        last_diff = row['raw_Force'] - row['Force']
                        fixed_data.append(row)
                    elif row['Row_Type'] == '6_column':
                        new_row = row.copy()
                        new_row['raw_Force'] = new_row['Force'] + last_diff
                        fixed_data.append(new_row)

                return pd.DataFrame(fixed_data)

            def fix_rows(data):
                fixed_data = []
                for _, row in data.iterrows():
                    if row['Row_Type'] == '6_column':
                        new_row = row.copy()
                        new_row.loc['Protocol_Step'] = new_row['Direction']
                        new_row.loc['Direction'] = new_row['Motor_State']
                        fixed_data.append(new_row)
                    else:
                        fixed_data.append(row)
                return pd.DataFrame(fixed_data)

            fixed_data = fix_data_rows(data)
            fixed_data = fix_rows(fixed_data)

            fixed_data.to_csv('fixed_data.csv', index=False)
        else:
            fixed_data = data

        self.data = self.data_f = fixed_data
        self.display_metadata(selected_trial)
        self.plot_figures()
        self.add_checkboxes()

    def display_metadata(self, folder_name):
        parts = folder_name.split("_")
        if len(parts) >= 3:
            timestamp, animal_id, trial_number = parts[0], parts[1], parts[2]
            metadata = f"Timestamp: {timestamp}    Animal ID: {animal_id}    Trial Number: {trial_number}"

        else:
            metadata = "Invalid folder name format."

        info_file_path = os.path.join(self.trial_path, "information.txt")

        if os.path.exists(info_file_path):
            try:
                # Open and read the file
                with open(info_file_path, "r") as info_file:
                    lines = info_file.readlines()

                # Parse each line and append to metadata
                for line in lines:
                    metadata += line.strip() + "    "
            except Exception as e:
                metadata = f"Error reading information.txt: {e}"
        else:
            metadata = "information.txt not found in the selected folder."

        # open up information.txt inside the selected folder and parse and display all avaiable information ie Created on: 2025-02-07 12:04
        # Total time: 64.68000000000168
        # Total steps: 20
        # Animal ID: 6549
        # Selected arm: Left Arm
        self.metadata_label.configure(text=metadata)

    def plot_figures(self):
        # Clear previous plots
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        if self.data_f is not None:
            angle = self.data_f['Angle']
            force = self.data_f['Force']
            time = self.data_f['Time']

            direction_mapping = {'idle': 0, 'forward': 1, 'backward': -1}
            self.data_f['Direction_numeric'] = self.data_f['Direction'].map(direction_mapping)

            figures = []

            # Constants for scaling
            FIGSIZE_ROW = (5, 3)  # Larger width for row-spanning plot
            FIGSIZE_SMALL = (3, 2)  # Smaller size for side-by-side plots
            DPI = 125  # Moderate DPI for clarity
            FONT_SIZE = 6  # Font size suitable for small plots
            LINE_WIDTH = 0.7  # Thin but visible lines
            MARKER_SIZE = 2  # Small marker size
            FLIER_SIZE = 1  # Smaller circles for outliers in boxplot

            # Plot 1: Angle vs. Force (spans columns 0 and 1 in row 0)
            fig1, ax1 = plt.subplots(figsize=FIGSIZE_ROW, dpi=DPI)
            fig1.patch.set_facecolor('none')  # Make the figure background transparent
            fig1.patch.set_edgecolor('none')  # Make the figure edge transparent

            ax1.plot(
                angle, force,
                label='Force',
                marker='o', markersize=MARKER_SIZE,
                linestyle='-', linewidth=LINE_WIDTH,
                color='b'
            )
            ax1.set_title('Angle vs. Force', fontsize=FONT_SIZE + 2)
            ax1.set_xlabel('Angle (degrees)', fontsize=FONT_SIZE)
            ax1.set_ylabel('Force (N)', fontsize=FONT_SIZE)
            ax1.tick_params(axis='both', labelsize=FONT_SIZE - 1)
            ax1.legend(fontsize=FONT_SIZE - 1)
            ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            ax1.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
            ax1.grid(True, linewidth=0.3)
            plt.tight_layout()  # Adjust margins to prevent crowding
            figures.append((fig1, 0, 0, 2))  # Spans 2 columns

            # Plot 2: Force Distribution by Protocol_Step (column 0, row 1)
            fig2, ax2 = plt.subplots(figsize=FIGSIZE_SMALL, dpi=DPI)
            sns.boxplot(
                x='Protocol_Step', y='Force',
                data=self.data_f, ax=ax2,
                linewidth=LINE_WIDTH, fliersize=FLIER_SIZE
            )
            ax2.set_title('Force Distribution by Protocol_Step', fontsize=FONT_SIZE + 2)
            ax2.set_xlabel('Protocol_Step', fontsize=FONT_SIZE)
            ax2.set_ylabel('Force (N)', fontsize=FONT_SIZE)
            ax2.tick_params(axis='both', labelsize=FONT_SIZE - 1)
            ax2.grid(axis='y', linestyle='--', alpha=0.5, linewidth=0.3)
            plt.tight_layout()  # Adjust margins to prevent crowding
            figures.append((fig2, 1, 0, 1))  # Single column

            # Plot 3: Force and Direction Over Time (column 1, row 1)
            fig3, ax3 = plt.subplots(figsize=FIGSIZE_SMALL, dpi=DPI)
            ax3.plot(
                time, force,
                label='Force (N)',
                color='blue', alpha=0.7,
                linewidth=LINE_WIDTH
            )
            ax3.fill_between(
                time, self.data_f['Direction_numeric'],
                step='mid', alpha=0.3,
                label='Direction', color='orange'
            )
            ax3.set_title('Force and Direction Over Time', fontsize=FONT_SIZE + 2)
            ax3.set_xlabel('Time', fontsize=FONT_SIZE)
            ax3.set_ylabel('Force (N) / Direction', fontsize=FONT_SIZE)
            ax3.tick_params(axis='both', labelsize=FONT_SIZE - 1)
            ax3.legend(fontsize=FONT_SIZE - 1)
            ax3.grid(True, linewidth=0.3)
            plt.tight_layout()  # Adjust margins to prevent crowding
            figures.append((fig3, 1, 1, 1))  # Single column

            # Display plots in the customtkinter canvas_frame
            for fig, row, col, colspan in figures:
                self.add_plot(fig, row, col, colspan)

            # Add a table in column 2 (3rd column)
            self.add_table(rowspan=2)

    def update_content_based_on_checkboxes(self, selected_steps):
        """Update plots and table based on selected checkboxes."""
        # Filter data based on selected steps
        if "Remove Wait" in selected_steps:
            filtered_data = self.data[self.data['Protocol_Step'].astype(int) % 2 != 0]
        else:
            filtered_data = self.data[self.data['Protocol_Step'].astype(int).isin(selected_steps)]

        # Update the main content (plots and table)
        self.data_f = filtered_data  # Update the data
        self.plot_figures()  # Recreate plots
        self.add_table(rowspan=2)  # Recreate table

    def add_checkboxes(self):
        """Add checkboxes for odd Protocol_Steps and 'Remove Wait' in the main_content area."""
        # Ensure main_content exists
        if not hasattr(self, "main_content") or not self.main_content.winfo_exists():
            print("Error: 'main_content' does not exist or has been destroyed.")
            return

        # Clear existing checkboxes if they exist
        if hasattr(self, "checkbox_frame") and self.checkbox_frame.winfo_exists():
            self.checkbox_frame.destroy()

        # Create and store the frame for checkboxes at the bottom of main_content
        self.checkbox_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.checkbox_frame.pack(side="bottom", fill="x", pady=10)

        # Track checkbox states
        self.checkbox_states = {}
        odd_steps = sorted(self.data['Protocol_Step'].astype(int).unique())
        odd_steps = [step for step in odd_steps if step % 2 != 0]

        # Callback function when a checkbox is toggled
        def checkbox_callback():
            selected_steps = [step for step, var in self.checkbox_states.items() if var.get()]
            print(f"Selected steps: {selected_steps}")
            # Update the plots and table based on selected checkboxes
            self.update_content_based_on_checkboxes(selected_steps)

        # Create checkboxes dynamically with an 8-column grid
        num_columns = 8  # Set the number of columns in the grid
        for i, step in enumerate(odd_steps):
            var = ctk.BooleanVar(value=True)  # Default to checked
            self.checkbox_states[step] = var
            checkbox = ctk.CTkCheckBox(
                self.checkbox_frame, text=f"Step {step}", variable=var, command=checkbox_callback
            )
            checkbox.grid(row=i // num_columns, column=i % num_columns, padx=5, pady=5, sticky="w")

        # Add "Remove Wait" checkbox for all even Protocol_Steps
        remove_wait_var = ctk.BooleanVar(value=False)
        self.checkbox_states["Remove Wait"] = remove_wait_var
        remove_wait_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame, text="Remove Wait", variable=remove_wait_var, command=checkbox_callback
        )
        # Place "Remove Wait" in the next available row
        remove_wait_checkbox.grid(row=(len(odd_steps) // num_columns) + 1, column=0, padx=5, pady=5, sticky="w")

    def add_plot(self, figure, row, col, colspan=1):
        """Helper function to embed matplotlib figures into the tkinter GUI."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(figure, self.canvas_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5)
        canvas.draw()

    def add_table(self, rowspan):
        """Add tables to display general statistics and detailed calculations.
        Both the general stats table and the detailed stats table (inside a scrollable frame)
        are added using grid so that they do not conflict with other grid-managed widgets
        in self.canvas_frame.
        """
        # Create a container frame inside self.canvas_frame using grid
        table_frame = ctk.CTkFrame(self.canvas_frame)
        table_frame.grid(row=0, column=2, rowspan=rowspan, sticky="nsew", padx=5, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)

        # ---------------------------
        # General Statistics Table (unchanged)
        # ---------------------------
        general_stats_frame = ctk.CTkFrame(table_frame)
        general_stats_frame.grid(row=0, column=0, sticky="ew", pady=10)
        general_stats_frame.grid_columnconfigure(0, weight=1)

        try:
            with open(os.path.join(self.trial_path, "information.txt"), "r") as f:
                lines = f.readlines()
            created_on = next(line.split("Created on:")[1].strip() for line in lines if "Created on:" in line)
        except Exception:
            created_on = "Unknown"

        total_duration = self.data["Time"].iloc[-1] if not self.data.empty else 0
        total_steps = self.data["Protocol_Step"].nunique()
        total_data_points = len(self.data)
        max_force = self.data["Force"].max()
        min_force = self.data["Force"].min()
        max_angle = self.data["Angle"].max()
        min_angle = self.data["Angle"].min()
        num_cycles = self.data["Protocol_Step"].astype(int).isin(range(1, total_steps + 1, 2)).sum() // 2

        general_stats = pd.DataFrame({
            "Metric": [
                "Created On", "Total Duration", "Total Steps", "Total Data Points",
                "Max Force", "Min Force", "Max Angle", "Min Angle", "Number of Cycles"
            ],
            "Value": [
                created_on, f"{total_duration:.2f}s", total_steps, total_data_points,
                f"{max_force:.2f}", f"{min_force:.2f}", f"{max_angle:.2f}", f"{min_angle:.2f}", num_cycles
            ]
        })

        general_tree = ttk.Treeview(general_stats_frame, columns=list(general_stats.columns),
                                    show="headings", height=10)
        for col in general_stats.columns:
            general_tree.heading(col, text=col)
            # Let columns stretch as needed
            general_tree.column(col, anchor="center", width=300, stretch=True)
        for _, row in general_stats.iterrows():
            general_tree.insert("", "end", values=list(row))
        general_tree.grid(row=0, column=0, sticky="ew")

        # ---------------------------
        # Detailed Statistics Table in a Scrollable Frame
        # ---------------------------
        # Prepare detailed statistics data as before
        odd_protocol_data = self.data_f[self.data_f['Protocol_Step'].astype(int) % 2 != 0]
        angle_diff = odd_protocol_data.groupby('Protocol_Step')['Angle'].agg(lambda x: x.iloc[-1] - x.iloc[0]).abs()
        final_angle = odd_protocol_data.groupby('Protocol_Step')['Angle'].last()
        angle_diff.index = angle_diff.index.astype(str)
        final_angle.index = final_angle.index.astype(str)

        def count_points_within_iqr(group):
            q1 = group['Force'].quantile(0.25)
            q3 = group['Force'].quantile(0.75)
            return ((group['Force'] >= q1) & (group['Force'] <= q3)).sum()

        def angle_diff_iqr(group):
            q1 = group['Force'].quantile(0.25)
            q3 = group['Force'].quantile(0.75)
            iqr_data = group[(group['Force'] >= q1) & (group['Force'] <= q3)]
            if not iqr_data.empty:
                return abs(iqr_data['Angle'].iloc[-1] - iqr_data['Angle'].iloc[0])
            return np.nan

        def slope_iqr_to_last(group):
            q1 = group['Force'].quantile(0.25)
            q3 = group['Force'].quantile(0.75)
            iqr_data = group[(group['Force'] >= q1) & (group['Force'] <= q3)]
            if not iqr_data.empty:
                last_iqr_angle = iqr_data['Angle'].iloc[-1]
                last_iqr_force = iqr_data['Force'].iloc[-1]
                last_angle = group['Angle'].iloc[-1]
                last_force = group['Force'].iloc[-1]
                if last_angle != last_iqr_angle:
                    return (last_force - last_iqr_force) / (last_angle - last_iqr_angle)
            return np.nan

        points_within_iqr = odd_protocol_data.groupby('Protocol_Step').apply(count_points_within_iqr)
        angle_diff_in_iqr = odd_protocol_data.groupby('Protocol_Step').apply(angle_diff_iqr)
        slope_iqr_last = odd_protocol_data.groupby('Protocol_Step').apply(slope_iqr_to_last)
        points_within_iqr.index = points_within_iqr.index.astype(str)
        angle_diff_in_iqr.index = angle_diff_in_iqr.index.astype(str)
        slope_iqr_last.index = slope_iqr_last.index.astype(str)

        custom_data = pd.DataFrame({
            "Protocol_Step": angle_diff.index,
            "RoM": angle_diff.round(1),
            "Final Angle": final_angle.round(1),
            "Points in IQR": points_within_iqr,
            "Angle Diff in IQR": angle_diff_in_iqr.round(1),
            "Slope IQR to Last": slope_iqr_last.round(4)  # 4 decimal places
        }).reset_index(drop=True)

        summary_row = pd.DataFrame([{
            "Protocol_Step": "Summary",
            "RoM": f"{angle_diff.mean():.1f} | {angle_diff.std():.1f}",
            "Final Angle": "",
            "Points in IQR": f"{points_within_iqr.mean():.1f} | {points_within_iqr.std():.1f}",
            "Angle Diff in IQR": f"{angle_diff_in_iqr.mean():.1f} | {angle_diff_in_iqr.std():.1f}",
            "Slope IQR to Last": f"{slope_iqr_last.mean():.2f} | {slope_iqr_last.std():.2f}"
        }])
        # Define the path to the main data directory

        main_data_directory = "./data"

        # Define the file name for the CSV
        csv_file_path = os.path.join(main_data_directory, "custom_data.csv")

        # Ensure the Protocol_Step column is treated as numeric for filtering and sorting
        custom_data["Protocol_Step_Numeric"] = pd.to_numeric(custom_data["Protocol_Step"], errors="coerce")

        # Filter out rows where Protocol_Step is 1
        custom_data = custom_data[custom_data["Protocol_Step_Numeric"] != 1]

        # Sort the DataFrame by the numeric Protocol_Step column in ascending order
        custom_data = custom_data.sort_values(by="Protocol_Step_Numeric", ascending=True).drop(
            columns=["Protocol_Step_Numeric"])

        # Calculate the average of each column
        average_row = custom_data.mean(numeric_only=True).to_dict()
        average_row["Protocol_Step"] = "Average"

        # Convert the average row to a DataFrame
        average_row_df = pd.DataFrame([average_row])

        # Append the average row to the DataFrame using pd.concat
        custom_data = pd.concat([custom_data, average_row_df], ignore_index=True)

        # Calculate alternating averages for "Final Angle" and "Slope IQR to Last"
        odd_rows = custom_data.iloc[::2]
        even_rows = custom_data.iloc[1::2]

        final_angle_avg1 = odd_rows["Final Angle"].mean()
        final_angle_avg2 = even_rows["Final Angle"].mean()

        slope_avg1 = odd_rows["Slope IQR to Last"].mean()
        slope_avg2 = even_rows["Slope IQR to Last"].mean()

        # Create DataFrames for the new rows
        final_angle_avg1_df = pd.DataFrame([{"Protocol_Step": "Final Angle Avg 1", "Final Angle": final_angle_avg1}])
        final_angle_avg2_df = pd.DataFrame([{"Protocol_Step": "Final Angle Avg 2", "Final Angle": final_angle_avg2}])
        slope_avg1_df = pd.DataFrame([{"Protocol_Step": "Slope Avg 1", "Slope IQR to Last": slope_avg1}])
        slope_avg2_df = pd.DataFrame([{"Protocol_Step": "Slope Avg 2", "Slope IQR to Last": slope_avg2}])

        # Append the new rows to the DataFrame using pd.concat
        custom_data = pd.concat([custom_data, final_angle_avg1_df, final_angle_avg2_df, slope_avg1_df, slope_avg2_df],
                                ignore_index=True)

        # Save the DataFrame to a CSV file
        custom_data.to_csv(csv_file_path, index=False)

        print(f"Data saved to {csv_file_path}")

        custom_data = pd.concat([custom_data, summary_row], ignore_index=True)
        custom_data["Protocol_Step_Numeric"] = pd.to_numeric(custom_data["Protocol_Step"], errors="coerce")
        custom_data = custom_data.sort_values(by=["Protocol_Step_Numeric", "Protocol_Step"],
                                              ascending=[True, True]).drop(columns=["Protocol_Step_Numeric"])

        total_rows = len(custom_data)
        visible_rows = 10 if total_rows > 10 else total_rows

        # Use CustomTkinter's scrollable frame (grid-managed) for the detailed table
        scroll_frame = ctk.CTkScrollableFrame(table_frame, height=300)
        scroll_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        detailed_tree = ttk.Treeview(scroll_frame, columns=list(custom_data.columns), show="headings",
                                     height=visible_rows)
        for col in custom_data.columns:
            detailed_tree.heading(col, text=col)
            detailed_tree.column(col, anchor="center", width=150, stretch=True)
        for _, row in custom_data.iterrows():
            detailed_tree.insert("", "end", values=list(row))
        detailed_tree.grid(row=0, column=0, sticky="nsew")

    def add_slider(self):
        if self.slider:
            self.slider.destroy()

        min_step, max_step = int(self.data['Protocol_Step'].min()), int(self.data['Protocol_Step'].max())
        self.slider = ctk.CTkSlider(self.canvas_frame, from_=min_step, to=max_step,
                                    number_of_steps=max_step - min_step + 1, command=self.update_cropped_data)
        self.slider.pack(pady=20)

        # Enable download button
        self.download_button.configure(state="normal")

    def update_cropped_data(self, value):
        step = int(value)
        self.cropped_data = self.data[self.data['Protocol_Step'] == step]

    def save_all_figures(self):
        """Save all figures and tables displayed on the page as PNG files and show a popup message."""
        angle = self.data_f['Angle']
        force = self.data_f['Force']
        time = self.data_f['Time']

        direction_mapping = {'idle': 0, 'forward': 1, 'backward': -1}
        self.data_f['Direction_numeric'] = self.data_f['Direction'].map(direction_mapping)

        # Create a folder for saving
        save_dir = os.path.join(self.trial_path, "screenshots")
        os.makedirs(save_dir, exist_ok=True)

        figures = []

        # Constants for scaling
        FIGSIZE_ROW = (5, 3)  # Larger width for row-spanning plot
        FIGSIZE_SMALL = (3, 2)  # Smaller size for side-by-side plots
        DPI = 300  # Moderate DPI for clarity
        FONT_SIZE = 6  # Font size suitable for small plots
        LINE_WIDTH = 0.7  # Thin but visible lines
        MARKER_SIZE = 2  # Small marker size
        FLIER_SIZE = 1  # Smaller circles for outliers in boxplot

        # Plot 1: Angle vs. Force
        fig1, ax1 = plt.subplots(figsize=FIGSIZE_ROW, dpi=DPI)
        ax1.plot(
            angle, force,
            label='Force',
            marker='o', markersize=MARKER_SIZE,
            linestyle='-', linewidth=LINE_WIDTH,
            color='b'
        )
        ax1.set_title(f'Angle vs. Force - {self.selected_trial}', fontsize=FONT_SIZE + 2)
        ax1.set_xlabel('Angle (degrees)', fontsize=FONT_SIZE)
        ax1.set_ylabel('Force (N)', fontsize=FONT_SIZE)
        ax1.tick_params(axis='both', labelsize=FONT_SIZE - 1)
        ax1.legend(fontsize=FONT_SIZE - 1)
        ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
        ax1.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
        ax1.grid(True, linewidth=0.3)
        plt.tight_layout()  # Adjust margins to prevent crowding
        figures.append((fig1, 0, 0, 2))  # Spans 2 columns

        # Plot 2: Force Distribution by Protocol_Step (column 0, row 1)
        fig2, ax2 = plt.subplots(figsize=FIGSIZE_SMALL, dpi=DPI)
        sns.boxplot(
            x='Protocol_Step', y='Force',
            data=self.data_f, ax=ax2,
            linewidth=LINE_WIDTH, fliersize=FLIER_SIZE
        )
        ax2.set_title('Force Distribution by Protocol_Step', fontsize=FONT_SIZE + 2)
        ax2.set_xlabel('Protocol_Step', fontsize=FONT_SIZE)
        ax2.set_ylabel('Force (N)', fontsize=FONT_SIZE)
        ax2.tick_params(axis='both', labelsize=FONT_SIZE - 1)
        ax2.grid(axis='y', linestyle='--', alpha=0.5, linewidth=0.3)
        plt.tight_layout()  # Adjust margins to prevent crowding
        figures.append((fig2, 1, 0, 1))  # Single column

        # Plot 3: Force and Direction Over Time (column 1, row 1)
        fig3, ax3 = plt.subplots(figsize=FIGSIZE_SMALL, dpi=DPI)
        ax3.plot(
            time, force,
            label='Force (N)',
            color='blue', alpha=0.7,
            linewidth=LINE_WIDTH
        )
        ax3.fill_between(
            time, self.data_f['Direction_numeric'],
            step='mid', alpha=0.3,
            label='Direction', color='orange'
        )
        ax3.set_title('Force and Direction Over Time', fontsize=FONT_SIZE + 2)
        ax3.set_xlabel('Time', fontsize=FONT_SIZE)
        ax3.set_ylabel('Force (N) / Direction', fontsize=FONT_SIZE)
        ax3.tick_params(axis='both', labelsize=FONT_SIZE - 1)
        ax3.legend(fontsize=FONT_SIZE - 1)
        ax3.grid(True, linewidth=0.3)
        plt.tight_layout()  # Adjust margins to prevent crowding
        figures.append((fig3, 1, 1, 1))  # Single column

        # Save the figures above to the folder
        for i, (fig, row, col, colspan) in enumerate(figures):
            fig.savefig(os.path.join(save_dir, f"figure_{i + 1}.png"))

        # Render and save general stats table
        self.render_table_as_image(self.get_general_stats(), os.path.join(save_dir, "general_stats.png"))

        # Render and save protocol stats table
        self.render_table_as_image(self.get_protocol_stats(), os.path.join(save_dir, "protocol_stats.png"))

        # Show success popup
        self.show_success_popup(save_dir)

    def render_table_as_image(self, data, filepath):
        """Render a pandas DataFrame as a table image and save it."""
        fig, ax = plt.subplots(figsize=(10, len(data) * 0.5))  # Dynamically scale height by rows
        ax.axis('tight')
        ax.axis('off')

        # Create table
        table = ax.table(
            cellText=data.values,
            colLabels=data.columns,
            cellLoc='center',
            loc='center'
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.auto_set_column_width(col=list(range(len(data.columns))))  # Adjust column widths
        plt.savefig(filepath, bbox_inches='tight', dpi=300)
        print(f"Saved table as image: {filepath}")
        plt.close(fig)

    def get_general_stats(self):
        """Generate general statistics as a pandas DataFrame."""
        try:
            with open(os.path.join(self.trial_path, "information.txt"), "r") as f:
                lines = f.readlines()
            created_on = next(line.split("Created on:")[1].strip() for line in lines if "Created on:" in line)
        except Exception:
            created_on = "Unknown"

        total_duration = self.data["Time"].iloc[-1] if not self.data.empty else 0
        total_steps = self.data["Protocol_Step"].nunique()
        total_data_points = len(self.data)
        max_force = self.data["Force"].max()
        min_force = self.data["Force"].min()
        max_angle = self.data["Angle"].max()
        min_angle = self.data["Angle"].min()
        num_cycles = self.data["Protocol_Step"].astype(int).isin(range(1, total_steps + 1, 2)).sum() // 2

        general_stats = pd.DataFrame({
            "Metric": [
                "Created On", "Total Duration", "Total Steps", "Total Data Points",
                "Max Force", "Min Force", "Max Angle", "Min Angle", "Number of Cycles"
            ],
            "Value": [
                created_on, f"{total_duration:.2f}s", total_steps, total_data_points,
                f"{max_force:.2f}", f"{min_force:.2f}", f"{max_angle:.2f}", f"{min_angle:.2f}", num_cycles
            ]
        })
        return general_stats

    def get_protocol_stats(self):
        """Generate protocol statistics as a pandas DataFrame."""
        # Filter rows with odd Protocol_Step
        odd_protocol_data = self.data_f[self.data_f['Protocol_Step'].astype(int) % 2 != 0]

        # Group by Protocol_Step and calculate the absolute difference in Angle
        angle_diff = odd_protocol_data.groupby('Protocol_Step')['Angle'].agg(lambda x: x.iloc[-1] - x.iloc[0]).abs()
        angle_diff.index = angle_diff.index.astype(str)  # Convert index to strings

        # Points within IQR calculations
        def count_points_within_iqr(group):
            q1 = group['Force'].quantile(0.25)
            q3 = group['Force'].quantile(0.75)
            return ((group['Force'] >= q1) & (group['Force'] <= q3)).sum()

        points_within_iqr = odd_protocol_data.groupby('Protocol_Step').apply(count_points_within_iqr)
        points_within_iqr.index = points_within_iqr.index.astype(str)  # Convert index to strings

        # Prepare the data for display
        custom_data = pd.DataFrame({
            "Protocol_Step": angle_diff.index,  # Protocol steps as strings
            "RoM": angle_diff.round(1),  # Round to 1 decimal place
            "Points in IQR": points_within_iqr
        }).reset_index(drop=True)

        return custom_data

    def show_success_popup(self, save_dir):
        """Show a popup window with the success message."""
        popup = ctk.CTkToplevel(self)
        popup.title("Success")
        popup.geometry("400x200")

        # Success message
        label = ctk.CTkLabel(
            popup,
            text=f"All figures and tables have been successfully saved to:\n{save_dir}",
            font=("Arial", 14),
            wraplength=350
        )
        label.pack(pady=20, padx=20)

        # OK button to close the popup
        ok_button = ctk.CTkButton(popup, text="OK", command=popup.destroy)
        ok_button.pack(pady=10)

    def download_cropped_data(self):
        if self.cropped_data is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if save_path:
                self.cropped_data.to_csv(save_path, index=False)
                ctk.messagebox.showinfo("Success", f"Cropped data saved to {save_path}")
        else:
            ctk.messagebox.showwarning("Warning", "No cropped data available.")

    def show_inspector(self):
        # create a side bar that has a drop down menu for the user to select the trial they want to inspect. The trials will be read by reading the folders in ./data directory. If there are no trials in the directory the user will be prompted by a pop up window to got to the home page to run a protocol or can manually select one which will open up a file path dialog box for them to select the trial they want to inspect. Automatically create the figures for the trial and display them in the main frame
        # On the side bar also have a mannual upload box, save all figures button. Add a button if the slider is currently modified that says download cropped data. If slider is not modified, then the button will be greyed out. This button will trigger a popup that will have the default new file name as the folder name but with _cropped appended to the end. The user can change the name if they want. The .csv should be saved to the trial folder

        # once a trial has been selected, open the .csv file and read the data. See logic below on what figures to produce and how to handle the data. At the top of the main frame parse date, animal_ID, trial #, and provided_name (if there). The folder name format will either be f"{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}" or f"./data/{timestamp}_{provided_name}_{animal_id}_{trial_number:02d}". Neatly display this information. Below that Neatly format the figures on the main frame, place a save figure button for each graph (which saves the figure to the current folder selected in ./data). At the bottom of the main frame make a dragable slider that allows the user to set the start and end data displayed. Have this update everything automtaically. In the data the final column is the step column and each step nin the slider should corespond to a step. Make sure to plot an axis for this slider.
        # Get available trials
        self.clear_content_frame()  # Clear existing content in the frame

        trials = self.get_trials()

        if not trials or "No Trials Found" in trials:
            self.no_trials_popup()
            return

        # Create inspector layout
        inspector_frame = ctk.CTkFrame(self.content_frame, corner_radius=0)
        inspector_frame.pack(fill="both", expand=True)

        # Sidebar for trial selection
        sidebar = ctk.CTkFrame(inspector_frame, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")

        sidebar_label = ctk.CTkLabel(sidebar, text="Inspector Controls", font=("Arial", 16, "bold"))
        sidebar_label.pack(padx=5, pady=20)

        trial_dropdown = ctk.CTkOptionMenu(sidebar, values=self.get_trials(), command=self.load_trial)
        trial_dropdown.pack(padx=5, pady=10)

        upload_button = ctk.CTkButton(sidebar, text="Upload CSV", command=self.upload_csv)
        upload_button.pack(padx=5, pady=10)

        save_all_button = ctk.CTkButton(sidebar, text="Save All Figures", command=self.save_all_figures)
        save_all_button.pack(padx=5, pady=10)

        self.download_button = ctk.CTkButton(sidebar, text="Download Cropped Data", state="disabled",
                                             command=self.download_cropped_data)
        self.download_button.pack(padx=5, pady=10)

        # Main content area
        self.main_content = ctk.CTkFrame(inspector_frame, corner_radius=0)
        self.main_content.pack(side="left", fill="both", expand=True)

        # Metadata display
        self.metadata_label = ctk.CTkLabel(self.main_content, text="", font=("Arial", 14))
        self.metadata_label.pack(pady=10)

        # Canvas frame for plots and table
        self.canvas_frame = ctk.CTkFrame(self.main_content)
        self.canvas_frame.pack(fill="both", expand=True)


        # Load the first trial and create initial content
        self.load_trial(trials[0])

    def show_restart_popup(self):
        """Show a popup asking the user if they want to restart protocol_runner.py."""
        popup = ctk.CTkToplevel(self)
        popup.title("Protocol Runner Crashed")
        popup.geometry("400x200")

        label = ctk.CTkLabel(popup, text="Protocol Runner has crashed. Restart?", font=("Arial", 14))
        label.pack(pady=20)

        def restart():
            popup.destroy()
            # restart logic here

        def cancel():
            popup.destroy()

        restart_button = ctk.CTkButton(popup, text="Restart", command=restart)
        restart_button.pack(side="left", padx=10, pady=10)

        cancel_button = ctk.CTkButton(popup, text="Cancel", command=cancel)
        cancel_button.pack(side="right", padx=10, pady=10)


    def update_output_window(self):
        """Update the settings page window with new output from protocol_runner.py."""
        try:
            while not output_queue.empty():
                line = output_queue.get_nowait()
                self.output_text.config(state="normal")
                self.output_text.insert(tk.END, line)
                self.output_text.config(state="disabled")
                self.output_text.see(tk.END)  # Auto-scroll to latest line
        except queue.Empty:
            pass

        # Repeat the update process every 500ms
        self.after(500, self.update_output_window)


    def show_settings(self):
        """Show settings and monitor protocol_runner.py output"""
        self.clear_content_frame()

        # Create a frame for settings
        settings_frame = ctk.CTkFrame(self.content_frame)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Label
        settings_label = ctk.CTkLabel(settings_frame, text="Settings", font=("Arial", 16, "bold"))
        settings_label.pack(pady=10)

        # Create a frame for output display
        output_frame = ctk.CTkFrame(settings_frame)
        output_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a scrolling text widget to show protocol_runner.py output
        self.output_text = tk.Text(output_frame, wrap="word", height=15, width=80, state="disabled", bg="black",
                                   fg="white")
        self.output_text.pack(side="left", fill="both", expand=True)

        # Add a scrollbar
        scrollbar = tk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)

        # Start updating the output text widget
        self.update_output_window()

    def run_protocol_init(self):
        selected_protocol = self.displayed_protocol_var.get()
        self.protocol_var = selected_protocol
        current_protocol = self.redis_client.get("current_protocol_out")
        print(f"Selected protocol: {selected_protocol}, Current protocol: {current_protocol}")
        if selected_protocol == current_protocol:
            def on_confirm():
                protocol_path_c = os.path.join(self.protocol_folder, selected_protocol)
                self.run_protocol(protocol_path_c)
                self.total_steps = self.redis_client.get("total_steps")
                print(f"Running protocol again: {self.total_steps}")
                self.protocol_name_label.configure(text=f"Current Protocol: {selected_protocol}")
                confirm_popup.destroy()

            def on_cancel():
                confirm_popup.destroy()

            confirm_popup = ctk.CTk()
            confirm_popup.title("Confirm Protocol Run")

            label = ctk.CTkLabel(confirm_popup,
                                 text="The selected protocol is already running. Do you want to run it again?")
            label.pack(pady=10)

            confirm_button = ctk.CTkButton(confirm_popup, text="Yes", command=on_confirm)
            confirm_button.pack(side="left", padx=10, pady=10)

            cancel_button = ctk.CTkButton(confirm_popup, text="No", command=on_cancel)
            cancel_button.pack(side="right", padx=10, pady=10)

            confirm_popup.mainloop()
        else:
            # protocol_path = os.path.join(self.protocol_folder, selected_protocol)
            protocol_path = selected_protocol
            self.run_protocol(protocol_path)
            self.total_steps = self.redis_client.get("total_steps")
            print(f"Running protocol: {selected_protocol}")
            self.protocol_name_label.configure(text=f"Current Protocol: {selected_protocol}")
        self.timing_clock = time.time()
    def start_timing_thread(self):
        print('test')
        # self.timing_thread = Thread(target=self.check_protocol_status)
        # self.timing_thread.start()

    def check_protocol_status(self):
        while True:
            current_protocol_out = self.redis_client.get("current_protocol_out")
           #stop looping when current_protocol_out is empty
            print(self.timing_clock)
            print(current_protocol_out)
            if not current_protocol_out:
                self.timing_clock = None
                break
            time.sleep(0.1)  # Adjust the sleep time as needed to reduce CPU usage

    def send_data_to_shared_memory(self,stop_flag=1):
        step_count, current_angle, current_force = self.read_shared_memory()
        try:
            print(f"Writing to shared memory: stop_flag={stop_flag}, step_count={step_count}, current_angle={current_angle}, current_force={current_force}")
            packed_data = struct.pack(self.fmt, stop_flag, step_count, current_angle, current_force)
            self.shm.buf[:len(packed_data)] = packed_data
        except Exception as e:
            print(f"Error writing to shared memory: {e}")

    def stop_protocol(self):
        # send self.send_data_to_shared_memory(stop_flag=1) multiple times to ensure the protocol stops
        for _ in range(10):
            self.send_data_to_shared_memory(stop_flag=1)
        self.redis_client.set("stop_flag", 1)
        self.show_overlay_notification("Protocol Stopped", color_disp="red")

    def toggle_mode(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)
        if mode == "Light":
            self.inspector_button.configure(text_color="black")
            self.settings_button.configure(text_color="black")
            self.home_button.configure(text_color="black")
            self.protocol_builder_button.configure(text_color="black")
        else:
            self.inspector_button.configure(text_color="white")
            self.settings_button.configure(text_color="white")
            self.home_button.configure(text_color="white")
            self.protocol_builder_button.configure(text_color="white")

    def update_shared_memory(self):
        while self.running:
            shared_data = self.read_shared_memory()
            if shared_data:
                step_count, current_angle, current_force = shared_data
                self.angle_special.append(current_angle)
                self.force_special.append(current_force)
                self.time_data.append(time.time())
                self.angle_data.append(current_angle)
                self.force_data.append(current_force)
                self.angle_force_data.append((current_angle, current_force))


                # Cap the data lists at (60 / self.poll_rate)
                max_length = int(30 / self.poll_rate)
                if len(self.time_data) > max_length:
                    self.time_data.pop(0)
                    self.angle_data.pop(0)
                    self.force_data.pop(0)

                if step_count ==-1:
                    if self.step_time is None:
                        self.step_time_int = time.time()
                        self.step_time = 0
                    else:
                        self.step_time = time.time() - self.step_time_int
                else:
                    self.step_time = None



                # Update individual displays if widgets exist
                if self.timing_clock is not None:
                    elapsed_time = time.time() - self.timing_clock
                    hours, remainder = divmod(elapsed_time, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
                    self.clock_values = True

                else:
                    # zero
                    if self.clock_values is not True:
                        hours = minutes = seconds = milliseconds = 0

                self.total_steps = self.redis_client.get("total_commands")
                self.queue.put((step_count, current_angle, current_force, minutes, seconds, milliseconds))
            else:
                self.queue.put((None, None, None, 0, 0, 0))

            time.sleep(0.05)


    def update_displays(self, step_count, current_angle, current_force, minutes, seconds, milliseconds):
        if is_protocol_running():
            self.status_frame.configure(fg_color="green")
            self.status_label.configure(text="Protocol Running")
        else:
            self.status_frame.configure(fg_color="red")
            self.status_label.configure(text="Protocol Not Running")
            self.show_overlay_notification("Protocol Not Running", color_disp="red")
        if step_count is not None:
            self.time_display.configure(text=f"{int(minutes):02}:{int(seconds):02}.{milliseconds:03}")
            if step_count < 0:
                if self.step_time is not None:
                    self.step_display.configure(text=f"{self.step_time:.1f}s")
            else:
                self.moving_steps_total= self.redis_client.get("moving_steps_total")
                if self.moving_steps_total is None:
                    self.moving_steps_total = 0
                self.step_display.configure(text=f"{step_count} / {self.moving_steps_total}")
            self.angle_display.configure(text=f"{current_angle:.1f}°")
            self.force_display.configure(text=f"{current_force:.2f} N")
            current_step_number = self.redis_client.get("current_step_number")
            if current_step_number is None:
                current_step_number = 0
            self.protocol_step_counter.configure(text=f"Step: {current_step_number} / {self.total_steps}")
            #pass in background color here dependning on light or dark mode
            if ctk.get_appearance_mode() == "Dark":
                self.advanced_slider.set_blue_angle(current_angle, '#333333')
            else:
                self.advanced_slider.set_blue_angle(current_angle, '#cfcfcf')
        else:
            self.step_display.configure(text="N/A")
            self.angle_display.configure(text="N/A")
            self.force_display.configure(text="N/A")
            self.time_display.configure(text=f"{int(0):02}:{int(0):02}:{int(0):02}.{0:03}")
            current_step = self.redis_client.get("current_step")
            if current_step is None:
                current_step = 0
            self.protocol_step_counter.configure(text=f"Step: {current_step} / {self.total_steps}")
        try:
            calibration_level = int(self.redis_client.get("calibration_Level") or 0)
            if calibration_level == 0:
                self.calibrate_button.configure(fg_color="red")
            elif calibration_level == 1:
                self.calibrate_button.configure(fg_color="yellow")
            elif calibration_level == 2:
                steps_level = int(self.redis_client.get("steps_Level") or 0)
                if steps_level <= 7500:
                    # Transition from blue (0,0,255) to yellow (255,255,0)
                    t = steps_level / 7500.0
                    r = int(255 * t)
                    g = int(255 * t)
                    b = int(255 * (1 - t))
                elif steps_level <= 15000:
                    # Transition from yellow (255,255,0) to red (255,0,0)
                    t = (steps_level - 7500) / 7500.0
                    r = 255
                    g = int(255 * (1 - t))
                    b = 0
                else:
                    # For steps beyond 15000, default to red
                    r, g, b = 255, 0, 0

                # Convert RGB to hexadecimal color string
                color_hex = f'#{r:02x}{g:02x}{b:02x}'
                self.calibrate_button.configure(fg_color=color_hex)
            else:
                self.calibrate_button.configure(fg_color="gray")  # Default color for unknown states

        except Exception as e:
            print(f"Error updating Calibrate button: {e}")
            self.calibrate_button.configure(fg_color="gray")

        try:
            # check redis status check the ordered list display the first message and then delet (next message will be display after 1 second)
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                # Get the ordered list from Redis
                messages = self.redis_client.lrange("message_list", 0, -1)
                if messages:
                    self.show_overlay_notification(messages, color_disp="blue")
                else:
                    return
                self.last_update_time = current_time
        except Exception as e:
            print(f"Error updating Calibrate button: {e}")



    def clear_graphs(self):
        # Reset the data lists
        self.angle_special = []
        self.force_special = []
        self.time_data = []
        self.angle_data = []
        self.force_data = []
        self.angle_force_data = []

        self.update_graph_view(self.segmented_button.get())


    def update_graph_view(self, mode):
        # Clear the current graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Initialize variables
        self.angle_data = []
        self.force_data = []
        self.time_data = []

        # Create a new Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(6, 4))  # Adjust the figure size as needed
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill="both")

        def fetch_data():
            # Read shared data for live updates
            shared_data = self.read_shared_memory()
            if ctk.get_appearance_mode() == "Dark":
                app_bg_color = "#1F1F1F"
                text_bg_color = "white"
            else:
                app_bg_color = "#FFFFFF"
                text_bg_color = "black"
            self.fig.patch.set_facecolor(app_bg_color)
            self.ax.set_facecolor(app_bg_color)

            if shared_data:

                # Plot data based on selected mode
                self.ax.clear()
                if mode == "Angle v Force":
                    # check if self.angle_special, self.force_special are same dimensions as each other if they are not remove from highest until they are
                    data_copy = list(self.angle_force_data)
                    if data_copy:
                        # Unzip the tuples into x and y values
                        x_values, y_values = zip(*data_copy)
                        self.ax.plot(x_values, y_values, label="Angle vs Force", color=text_bg_color)
                        self.ax.set_xlim(0, 180)
                        self.ax.set_ylim(-1.75, 1.75)
                        self.ax.set_xlabel("Angle (degrees)", color=text_bg_color)
                        self.ax.set_ylabel("Force (N)", color=text_bg_color)
                        self.ax.title.set_color(text_bg_color)
                elif mode == "Simple":
                    current_time = time.time()
                    valid_indices = [i for i, t in enumerate(self.time_data) if current_time - t <= 30]
                    filtered_time_data = [self.time_data[i] for i in valid_indices]
                    filtered_angle_data = [self.angle_data[i] for i in valid_indices]
                    filtered_force_data = [self.force_data[i] for i in valid_indices]

                    self.ax.plot(filtered_time_data, filtered_angle_data, label="Angle vs Time")
                    self.ax.plot(filtered_time_data, filtered_force_data, label="Force vs Time")
                    self.ax.set_xlabel("Time (s)")
                    self.ax.legend()
                elif mode == "All":
                    # Create subplots for all graphs
                    self.fig.clear()
                    gs = self.fig.add_gridspec(2, 2)

                    # Large plot on the left column
                    ax0 = self.fig.add_subplot(gs[:, 0])
                    data_copy = list(self.angle_force_data)
                    if data_copy:
                        x_values, y_values = zip(*data_copy)
                        ax0.plot(x_values, y_values, label="Angle vs Force", color='blue')
                    ax0.set_xlabel("Angle (degrees)")
                    ax0.set_ylabel("Force (N)")
                    ax0.set_xlim(0, 180)
                    ax0.set_ylim(-1.75, 1.75)
                    ax0.legend()

                    # Top right plot
                    ax1 = self.fig.add_subplot(gs[0, 1])
                    ax1.plot(self.time_data, self.angle_data, label="Angle vs Time", color='green')
                    ax1.set_ylabel("Angle (degrees)")
                    ax1.legend()

                    # Bottom right plot
                    ax2 = self.fig.add_subplot(gs[1, 1])
                    ax2.plot(self.time_data, self.force_data, label="Force vs Time", color='red')
                    ax2.set_xlabel("Time (s)")
                    ax2.set_ylabel("Force (N)")
                    ax2.legend()

                self.canvas.draw()

        # Start a periodic update of the graph
        if hasattr(self, 'update_loop_id'):
            self.graph_frame.after_cancel(self.update_loop_id)

        def update_loop():
            fetch_data()
            if self.running:
                self.update_loop_id = self.graph_frame.after(int(self.poll_rate * 1000), update_loop)

        update_loop()

    def on_closing(self):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()
        if protocol_process is not None and protocol_process.poll() is None:
            os.killpg(os.getpgid(protocol_process.pid), signal.SIGTERM)  # Kill entire terminal group
            protocol_process.wait()

        self.destroy()
        try:
            self.shm.close()
            self.shm.unlink()  # Only unlink if you're sure no other process needs it
        except Exception as e:
            print(f"Error during shared memory cleanup: {e}")


if __name__ == "__main__":
    global start_protocol
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the RatFlex application.")
    parser.add_argument("--run-protocol", action="store_true", help="Run the protocol runner on startup.")
    args = parser.parse_args()

    # Pass the argument to the App class
    start_protocol = args.run_protocol
    if start_protocol:
        print("Running protocol on startup...")
    else:
        print("Not running protocol on startup.")

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
