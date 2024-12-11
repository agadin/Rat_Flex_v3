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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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


def run_calibration():
    redis_client.set('protocol_trigger', "./protocols/calibrate_protocol.txt")


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
        self.protocol_builder_button = ctk.CTkButton(self.nav_frame, text="Protocol Builder", command=self.show_protocol_builder)
        self.inspector_button = ctk.CTkButton(self.nav_frame, text="Inspector", command=self.show_inspector)
        self.settings_button = ctk.CTkButton(self.nav_frame, text="Settings", command=self.show_settings)

        for btn in (self.home_button, self.protocol_builder_button, self.inspector_button, self.settings_button):
            btn.pack(side="left", padx=20, expand=True)

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

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=200)
        self.sidebar_frame.pack(side="left", fill="y", padx=10)

        # Calibrate button
        self.calibrate_button = ctk.CTkButton(self.sidebar_frame, text="Calibrate", command=run_calibration)
        self.calibrate_button.pack(pady=10)

        # Protocol selector
        self.protocol_label = ctk.CTkLabel(self.sidebar_frame, text="Select a Protocol:")
        self.protocol_label.pack(pady=10)

        self.protocol_folder = './protocols'
        self.protocol_files = [f for f in os.listdir(self.protocol_folder) if os.path.isfile(os.path.join(self.protocol_folder, f))]
        self.protocol_var = ctk.StringVar(value=self.protocol_files[0])

        self.protocol_dropdown = ctk.CTkComboBox(self.sidebar_frame, values=self.protocol_files, variable=self.protocol_var)
        self.protocol_dropdown.pack(pady=10)

        self.run_button = ctk.CTkButton(self.sidebar_frame, text="Run Protocol", command=self.run_protocol)
        self.run_button.pack(pady=10)

        # Stop button
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="Stop", command=self.stop_protocol)
        self.stop_button.pack(pady=10)

        # Light/Dark mode toggle
        self.mode_toggle = ctk.CTkSwitch(self.sidebar_frame, text="Light/Dark Mode", command=self.toggle_mode)
        self.mode_toggle.pack(pady=10)

        # Main content area
        self.main_frame = ctk.CTkFrame(self.content_frame)
        self.main_frame.pack(side="left", expand=True, fill="both", padx=10)

        self.protocol_name_label = ctk.CTkLabel(self.main_frame, text="Current Protocol: None", anchor="w")
        self.protocol_name_label.pack(pady=10, padx=20, anchor="w")

        display_frame = ctk.CTkFrame(self.main_frame)
        display_frame.pack(pady=20)

        # Style for all three displays
        display_style = {
            "width": 200,
            "height": 100,
            "corner_radius": 20,
            "fg_color": "lightblue",
            "text_color": "black",
            "font": ("Arial", 24, "bold"),
        }

        # Create and pack step count display
        self.step_display = ctk.CTkLabel(display_frame, text="Steps: N/A", **display_style)
        self.step_display.grid(row=0, column=0, padx=10, pady=10)

        # Create and pack angle display
        self.angle_display = ctk.CTkLabel(display_frame, text="Angle: N/A", **display_style)
        self.angle_display.grid(row=0, column=1, padx=10, pady=10)

        # Create and pack force display
        self.force_display = ctk.CTkLabel(display_frame, text="Force: N/A", **display_style)
        self.force_display.grid(row=0, column=2, padx=10, pady=10)

        self.segmented_button = ctk.CTkSegmentedButton(self.main_frame, values=["Angle v Force", "Simple", "All"], command=self.update_graph_view)
        self.segmented_button.pack(pady=10)

        # Placeholder for graphs
        self.graph_frame = ctk.CTkFrame(self.main_frame)
        self.graph_frame.pack(expand=True, fill="both", pady=10)

        self.clear_button = ctk.CTkButton(self.main_frame, text="Clear", command=self.clear_graphs)
        self.clear_button.pack(pady=10)

        # Start background threads
        self.running = True
        self.update_thread = Thread(target=self.update_shared_memory)
        self.calibration_thread = Thread(target=self.update_calibrate_button)
        self.update_thread.start()
        self.calibration_thread.start()


    def show_protocol_builder(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Protocol Builder (Coming Soon)").pack(pady=20)

    def show_inspector(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Inspector - Data Viewer").pack(pady=10)

        try:
            with open("data.csv", "r") as file:
                data = file.readlines()
                for line in data:
                    ctk.CTkLabel(self.content_frame, text=line.strip()).pack(anchor="w")
        except FileNotFoundError:
            ctk.CTkLabel(self.content_frame, text="data.csv not found.").pack(pady=10)

    def show_settings(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Settings (Coming Soon)").pack(pady=20)

    def run_protocol(self):
        selected_protocol = self.protocol_var.get()
        protocol_path = os.path.join(self.protocol_folder, selected_protocol)
        run_protocol(protocol_path)
        print(f"Running protocol: {selected_protocol}")
        self.protocol_name_label.configure(text=f"Current Protocol: {selected_protocol}")

    def stop_protocol(self):
        send_data_to_shared_memory(stop_flag=0)
        print("Protocol stopped.")

    def toggle_mode(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)

    def update_shared_memory(self):
        while self.running:
            shared_data = read_shared_memory()
            if shared_data:
                step_count, current_angle, current_force = shared_data

                # Update individual displays if widgets exist
                if self.step_display.winfo_exists():
                    self.step_display.configure(text=f"{step_count}")
                if self.angle_display.winfo_exists():
                    self.angle_display.configure(text=f"{current_angle:.1f}°")
                if self.force_display.winfo_exists():
                    self.force_display.configure(text=f"{current_force:.2f} N")
            else:
                # Handle shared memory not available case
                if self.step_display.winfo_exists():
                    self.step_display.configure(text="N/A")
                if self.angle_display.winfo_exists():
                    self.angle_display.configure(text="N/A")
                if self.force_display.winfo_exists():
                    self.force_display.configure(text="N/A")

            time.sleep(0.1)

    def update_calibrate_button(self):
        while self.running:
            try:
                calibration_level = int(redis_client.get("calibration_Level") or 0)

                if calibration_level == 0:
                    self.calibrate_button.configure(fg_color="red")
                elif calibration_level == 1:
                    self.calibrate_button.configure(fg_color="yellow")
                elif calibration_level == 2:
                    self.calibrate_button.configure(fg_color="green")
                else:
                    self.calibrate_button.configure(fg_color="gray")  # Default color for unknown states

            except Exception as e:
                print(f"Error updating Calibrate button: {e}")
                self.calibrate_button.configure(fg_color="gray")  # Fallback color in case of error

            time.sleep(0.5)  # Adjust the refresh rate as needed

    def clear_graphs(self):
        # Reset the data lists
        self.time_data = []
        self.angle_data = []
        self.force_data = []

        # Clear the graph by redrawing it with empty data
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(expand=True, fill="both")
        canvas.draw()

    def update_graph_view(self, mode):
        # Clear the current graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Initialize variables
        angle_data = []
        force_data = []
        time_data = []

        # Create a new Matplotlib figure
        fig, ax = plt.subplots()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(expand=True, fill="both")

        def fetch_data():
            # Read shared data for live updates
            shared_data = read_shared_memory()
            if shared_data:
                _, angle, force = shared_data
                time_data.append(time.time())
                angle_data.append(angle)
                force_data.append(force)

                # Keep only the last 30 seconds for "Simple" mode
                if mode == "Simple":
                    current_time = time.time()
                    valid_indices = [i for i, t in enumerate(time_data) if current_time - t <= 30]
                    time_data[:] = [time_data[i] for i in valid_indices]
                    angle_data[:] = [angle_data[i] for i in valid_indices]
                    force_data[:] = [force_data[i] for i in valid_indices]

                # Limit angle to 0-180 degrees and force to -15 to 1.5 N
                if mode in ["Angle v Force", "All"]:
                    ax.set_xlim(0, 180)
                    ax.set_ylim(-15, 1.5)

                # Plot data based on selected mode
                ax.clear()
                if mode == "Angle v Force":
                    ax.plot(angle_data, force_data, label="Angle vs Force")
                    ax.set_xlabel("Angle (degrees)")
                    ax.set_ylabel("Force (N)")
                elif mode == "Simple":
                    ax.plot(time_data, angle_data, label="Angle vs Time")
                    ax.plot(time_data, force_data, label="Force vs Time")
                    ax.set_xlabel("Time (s)")
                    ax.legend()
                elif mode == "All":
                    # Create subplots for all graphs
                    fig.clear()
                    axes = fig.subplots(3, 1)
                    axes[0].plot(time_data, angle_data, label="Angle vs Time")
                    axes[0].set_ylabel("Angle (degrees)")
                    axes[0].legend()

                    axes[1].plot(time_data, force_data, label="Force vs Time")
                    axes[1].set_ylabel("Force (N)")
                    axes[1].legend()

                    axes[2].plot(angle_data, force_data, label="Angle vs Force")
                    axes[2].set_xlabel("Angle (degrees)")
                    axes[2].set_ylabel("Force (N)")
                    axes[2].legend()

                canvas.draw()

        # Start a periodic update of the graph
        def update_loop():
            fetch_data()
            if self.running:
                self.graph_frame.after(100, update_loop)  # Update every 100ms

        update_loop()

    def on_closing(self):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
