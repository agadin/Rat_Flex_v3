import customtkinter as ctk
import socket
import os
import redis
import multiprocessing.shared_memory as sm
import numpy as np
import time
import struct
import csv
from collections import defaultdict
from threading import Thread

# Initialize CustomTkinter
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

# Shared memory and Redis configuration

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
shm_name = 'shared_data'
fmt = 'i d d d'  # Format for shared memory (stop_flag, step_count, current_angle, current_force)
shm_size = struct.calcsize(fmt)

# Try to access shared memory
try:
    shm = sm.SharedMemory(name=shm_name)
except FileNotFoundError:
    print("Shared memory not found. Creating new shared memory block.")
    redis_client.set("shared_memory_error", 1)
    time.sleep(1)
    shm = sm.SharedMemory(name=shm_name)

def read_shared_memory():
    try:
        data = bytes(shm.buf[:struct.calcsize(fmt)])
        stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)
        return step_count, current_angle, current_force
    except Exception as e:
        print(f"Error reading shared memory: {e}")
        return None

def send_data_to_shared_memory(stop_flag=1):
    step_count, current_angle, current_force = read_shared_memory()
    try:
        packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)
        shm.buf[:len(packed_data)] = packed_data
    except Exception as e:
        print(f"Error writing to shared memory: {e}")

def run_protocol(protocol_path):
    redis_client.set('protocol_trigger', protocol_path)
    print(f"Triggered protocol: {protocol_path}")

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Stepper Motor Control")
        self.geometry("800x600")

        # Top navigation bar
        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.pack(fill="x", pady=5)

        self.home_button = ctk.CTkButton(self.nav_frame, text="Home", command=self.show_home)
        self.home_button.pack(side="left", padx=5)

        self.protocol_builder_button = ctk.CTkButton(self.nav_frame, text="Protocol Builder", command=self.show_protocol_builder)
        self.protocol_builder_button.pack(side="left", padx=5)

        self.inspector_button = ctk.CTkButton(self.nav_frame, text="Inspector", command=self.show_inspector)
        self.inspector_button.pack(side="left", padx=5)

        self.settings_button = ctk.CTkButton(self.nav_frame, text="Settings", command=self.show_settings)
        self.settings_button.pack(side="left", padx=5)

        # Main content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(expand=True, fill="both", pady=10)

        self.home_frame = None
        self.protocol_builder_frame = None
        self.inspector_frame = None
        self.settings_frame = None

        self.show_home()

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_content_frame()

        # Home content
        self.protocol_label = ctk.CTkLabel(self.content_frame, text="Select a Protocol:")
        self.protocol_label.pack(pady=10)

        self.protocol_folder = './protocols'
        self.protocol_files = [f for f in os.listdir(self.protocol_folder) if os.path.isfile(os.path.join(self.protocol_folder, f))]
        self.protocol_var = ctk.StringVar(value=self.protocol_files[0])

        self.protocol_dropdown = ctk.CTkComboBox(self.content_frame, values=self.protocol_files, variable=self.protocol_var)
        self.protocol_dropdown.pack(pady=10)

        self.run_button = ctk.CTkButton(self.content_frame, text="Run Protocol", command=self.run_protocol)
        self.run_button.pack(pady=10)

        self.shared_memory_label = ctk.CTkLabel(self.content_frame, text="Shared Memory Data")
        self.shared_memory_label.pack(pady=10)

        self.shared_memory_display = ctk.CTkLabel(self.content_frame, text="Waiting for data...")
        self.shared_memory_display.pack(pady=10)

        self.stop_button = ctk.CTkButton(self.content_frame, text="Stop", command=self.stop_protocol)
        self.stop_button.pack(pady=10)

        # Start background update thread
        if not hasattr(self, 'update_thread'):
            self.running = True
            self.update_thread = Thread(target=self.update_shared_memory)
            self.update_thread.start()

    def show_protocol_builder(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Protocol Builder (Coming Soon)").pack(pady=20)

    def show_inspector(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Inspector - Data Viewer").pack(pady=10)

        ctk.CTkLabel(self.content_frame, text="Inspector (Coming Soon)").pack(pady=20)

    def show_settings(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Settings (Coming Soon)").pack(pady=20)

    def run_protocol(self):
        selected_protocol = self.protocol_var.get()
        protocol_path = os.path.join(self.protocol_folder, selected_protocol)
        run_protocol(protocol_path)
        print(f"Running protocol: {selected_protocol}")

    def stop_protocol(self):
        send_data_to_shared_memory(stop_flag=0)
        print("Protocol stopped.")

    def update_shared_memory(self):
        while self.running:
            shared_data = read_shared_memory()
            if shared_data:
                step_count, current_angle, current_force = shared_data
                if self.shared_memory_display.winfo_exists():  # Check if the widget still exists
                    self.shared_memory_display.configure(
                        text=f"Step Count: {step_count}, Current Angle: {current_angle}, Current Force: {current_force}"
                    )
            else:
                if self.shared_memory_display.winfo_exists():  # Check if the widget still exists
                    self.shared_memory_display.configure(text="Shared memory not available.")
            time.sleep(0.1)

    def on_closing(self):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
