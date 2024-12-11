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

        # Protocol selection
        self.protocol_label = ctk.CTkLabel(self, text="Select a Protocol:")
        self.protocol_label.pack(pady=10)

        self.protocol_folder = './protocols'
        self.protocol_files = [f for f in os.listdir(self.protocol_folder) if os.path.isfile(os.path.join(self.protocol_folder, f))]
        self.protocol_var = ctk.StringVar(value=self.protocol_files[0])

        self.protocol_dropdown = ctk.CTkComboBox(self, values=self.protocol_files, variable=self.protocol_var)
        self.protocol_dropdown.pack(pady=10)

        self.run_button = ctk.CTkButton(self, text="Run Protocol", command=self.run_protocol)
        self.run_button.pack(pady=10)

        # Shared memory display
        self.shared_memory_label = ctk.CTkLabel(self, text="Shared Memory Data")
        self.shared_memory_label.pack(pady=10)

        self.shared_memory_display = ctk.CTkLabel(self, text="Waiting for data...")
        self.shared_memory_display.pack(pady=10)

        self.stop_button = ctk.CTkButton(self, text="Stop", command=self.stop_protocol)
        self.stop_button.pack(pady=10)

        # Start background update thread
        self.running = True
        self.update_thread = Thread(target=self.update_shared_memory)
        self.update_thread.start()

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
                self.shared_memory_display.configure(
                    text=f"Step Count: {step_count}, Current Angle: {current_angle}, Current Force: {current_force}"
                )
            else:
                self.shared_memory_display.configure(text="Shared memory not available.")
            time.sleep(0.1)

    def on_closing(self):
        self.running = False
        self.update_thread.join()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
