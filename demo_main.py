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
from tkinter import Canvas, Frame, Scrollbar
import pandas as pd
import seaborn as sns
from tkinter import ttk
import matplotlib.ticker as ticker
import readyplot as rp
from PIL import Image, ImageTk

def read_shared_memory():
    try:
        step_count= 1
        current_angle= 10
        current_force= 0.1
        return step_count, current_angle, current_force
    except Exception as e:
        print(f"Error reading shared memory: {e}")
        return None

def send_data_to_shared_memory(stop_flag=1):
    try:
        # Create shared memory
        shm = sm.SharedMemory(create=True, size=1024)
        data = np.array([stop_flag], dtype=np.int32)
        data_view = data.view(np.uint8)
        shm.buf[:data_view.nbytes] = data_view
        print(f"Data sent to shared memory: {stop_flag}")
    except Exception as e:
        print(f"Error sending data to shared memory: {e}")

def run_protocol(protocol_path):
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
    print("Running calibration...")

def save_to_redis_dict(self, key, value):
    print(f"Saving to Redis: {key} -> {value}")

class App(ctk.CTk):
    def __init__(self, demo_mode=True):
        super().__init__()
        self.demo_mode = demo_mode
        # Convert .ico to .png
        icon_path = os.path.abspath('./img/ratfav.ico')
        png_icon_path = os.path.abspath('./img/ratfav.png')
        try:
            img = Image.open(icon_path)
            img.save(png_icon_path)
            self.icon_img = ImageTk.PhotoImage(file=png_icon_path)
            self.iconphoto(False, self.icon_img)
            print("Icon set successfully.")
        except Exception as e:
            print(f"Failed to set icon: {e}")
        # Stationary variables
        self.angle_special = []
        self.force_special = []
        self.poll_rate = 0.2
        self.time_data = []
        self.angle_data = []
        self.force_data = []

        # Window configuration
        self.title("Stepper Motor Control")
        self.geometry("1920x1080")

        # Top navigation bar
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=5)

        self.home_button = ctk.CTkButton(self.nav_frame, text="Home", command=self.show_home)
        self.protocol_builder_button = ctk.CTkButton(self.nav_frame, text="Protocol Builder", command=self.show_protocol_builder)
        self.inspector_button = ctk.CTkButton(self.nav_frame, text="Inspector", command=self.show_inspector)
        self.settings_button = ctk.CTkButton(self.nav_frame, text="Settings", command=self.show_settings)

        self.comparer_button = ctk.CTkButton(self.nav_frame, text="Comparer", command=self.show_comparer)

        for btn in (self.home_button, self.protocol_builder_button, self.inspector_button, self.settings_button, self.comparer_button):
            btn.pack(side="left", padx=20, expand=True)

        # Main content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
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

        # Demo mode label
        if self.demo_mode:
            demo_label = ctk.CTkLabel(self.sidebar_frame, text="Demo Mode Active", font=("Arial", 14, "bold"))
            demo_label.pack(pady=10)

        # Calibrate button (disabled in demo mode)
        self.calibrate_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Calibrate",
            command=lambda: print("Calibration disabled in demo mode") if self.demo_mode else run_calibration,
            state="disabled" if self.demo_mode else "normal"
        )
        self.calibrate_button.pack(pady=10)

        # Protocol selector
        self.protocol_label = ctk.CTkLabel(self.sidebar_frame, text="Select a Protocol:")
        self.protocol_label.pack(pady=10)

        self.protocol_var = ctk.StringVar(value="Demo Protocol" if self.demo_mode else "None")

        self.protocol_dropdown = ctk.CTkComboBox(
            self.sidebar_frame,
            values=["Demo Protocol"] if self.demo_mode else [],
            variable=self.protocol_var
        )
        self.protocol_dropdown.pack(pady=10)

        self.run_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Run Protocol",
            command=lambda: print("Protocol run simulation in demo mode") if self.demo_mode else self.run_protocol,
        )
        self.run_button.pack(pady=10)

        # Stop button (placeholder in demo mode)
        self.stop_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Stop",
            command=lambda: print("Stopping simulation in demo mode") if self.demo_mode else self.stop_protocol,
        )
        self.stop_button.pack(pady=10)

        # create an input field for the user to input the animal ID and save it to redis when it is 4 numbers long
        self.animal_id_var = ctk.StringVar( value="Animal ID")
        self.animal_id_entry = ctk.CTkEntry(self.sidebar_frame, textvariable=self.animal_id_var)
        self.animal_id_entry.pack(pady=15, padx=15)

        def save_animal_id_to_redis(*args):
            animal_id = self.animal_id_var.get()
            if animal_id and animal_id != "Animal ID":
                save_to_redis_dict('set_vars', 'animal_id', animal_id)

        self.animal_id_var.trace("w", save_animal_id_to_redis)

        self.button_frame = ctk.CTkFrame(self.sidebar_frame)
        self.button_frame.pack(padx=5, pady=10, fill="x")

        # Right and Left Arm Toggle Buttons
        self.arm_selection = ctk.StringVar(value="")  # To track the current selection

        def toggle_arm_selection(selection):
            """Toggle the arm selection and update Redis."""
            if self.arm_selection.get() == selection:
                # Unselect if clicked again
                self.arm_selection.set("")
                print("selected_arm", "")  # Clear Redis value
            else:
                self.arm_selection.set(selection)
                print("selected_arm", selection)

            # Update button states
            update_button_states()

        def update_button_states():
            """Update the visual state of the buttons."""
            if self.arm_selection.get() == "Right Arm":
                run_protocol("./protocols/right_arm_jog.txt")
                right_button.configure(fg_color="blue", text_color="white")
                left_button.configure(fg_color="gray", text_color="black")
            elif self.arm_selection.get() == "Left Arm":
                run_protocol("./protocols/left_arm_jog.txt")
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
        right_button.pack(side="left", padx=10, pady=10)

        left_button = ctk.CTkButton(
            self.button_frame,
            text="Left Arm",
            command=lambda: toggle_arm_selection("Left Arm"),
            fg_color="gray",  # Default color
            text_color="black",
            corner_radius=10,
            width=100
        )
        left_button.pack(side="left", padx=10, pady=10)

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
            input_var.trace("w", lambda name, index, mode, var=input_var, idx=i: save_to_redis_dict('set_vars',
                                                                                                    f"input_{idx}",
                                                                                                    var.get()))
            self.redis_inputs.append(input_var)
        # Light/Dark mode toggle
        self.mode_toggle = ctk.CTkSwitch(self.sidebar_frame, text="Light/Dark Mode", command=self.toggle_mode)
        self.mode_toggle.pack(pady=10)

        # Main content area
        self.main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_frame.pack(side="left", expand=True, fill="both", padx=10)

        self.protocol_name_label = ctk.CTkLabel(self.main_frame, text="Current Protocol: None", anchor="w", font=("Arial", 20, "bold"))
        self.protocol_name_label.pack(pady=10, padx=20, anchor="w")

        display_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        display_frame.pack(pady=20)


        # Style for all three displays
        display_style = {
            "width": 300,
            "height": 150,
            "corner_radius": 20,
            "fg_color": "lightblue",
            "text_color": "black",
            "font": ("Arial", 45, "bold"),
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
        self.segmented_button.set("Angle v Force")  # Set default selection
        self.segmented_button.pack(pady=10)

        # Placeholder for graphs
        self.graph_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.graph_frame.pack(expand=True, fill="both", pady=10)

        self.clear_button = ctk.CTkButton(self.main_frame, text="Clear", command=self.clear_graphs)
        self.clear_button.pack(pady=10)

        # In demo mode, use dummy data for steps
        if self.demo_mode:
            self.step_display.configure(text="Time")
            self.angle_display.configure(text="Pressure")
            self.force_display.configure(text="Force")

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

    # -----------------------------------------------------------------
    # Simple popup message helper.
    # -----------------------------------------------------------------

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
        self.selected_trial = selected_trial
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
            general_tree.column(col, anchor="center", width=150, stretch=True)
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
            trial_dropdown.pack(padx=5,pady=10)

            upload_button = ctk.CTkButton(sidebar, text="Upload CSV", command=self.upload_csv)
            upload_button.pack(padx=5,pady=10)

            save_all_button = ctk.CTkButton(sidebar, text="Save All Figures", command=self.save_all_figures)
            save_all_button.pack(padx=5,pady=10)

            self.download_button = ctk.CTkButton(sidebar, text="Download Cropped Data", state="disabled",command=self.download_cropped_data)
            self.download_button.pack(padx=5,pady=10)

            # Main content area
            self.main_content = ctk.CTkFrame(inspector_frame, corner_radius=0)
            self.main_content.pack(side="right", fill="both", expand=True)

            # Metadata display
            self.metadata_label = ctk.CTkLabel(self.main_content, text="", font=("Arial", 14))
            self.metadata_label.pack(pady=10)

            # Canvas frame for plots and table
            self.canvas_frame = ctk.CTkFrame(self.main_content)
            self.canvas_frame.pack(fill="both", expand=True)

            # Load the first trial and create initial content
            self.load_trial(trials[0])

            # Add checkboxes in the main_content area
            self.add_checkboxes()

    def show_settings(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Settings (Coming Soon)").pack(pady=20)

    def run_protocol(self):
        protocol_path = self.protocol_var.get()
        run_protocol(protocol_path)

    def stop_protocol(self):
        send_data_to_shared_memory(stop_flag=1)

    def toggle_mode(self):
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if mode == "Dark" else "Dark")
    def update_graph_view(self, mode):
        # Clear the current graph frame
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Initialize variables
        self.angle_data = []
        self.force_data = []
        self.time_data = []

        # Create a new Matplotlib figure
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill="both")

        def fetch_data():
            # Read shared data for live updates
            shared_data = read_shared_memory()
            if shared_data:

                # Plot data based on selected mode
                self.ax.clear()
                if mode == "Angle v Force":
                    self.ax.plot(self.angle_special, self.force_special, label="Angle vs Force")
                    self.ax.set_xlim(0, 180)
                    self.ax.set_ylim(-1.75, 1.75)
                    self.ax.set_xlabel("Angle (degrees)")
                    self.ax.set_ylabel("Force (N)")
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
                    ax0.plot(self.angle_special, self.force_special, label="Angle vs Force", color='blue')
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
    def clear_graphs(self):
        # Reset the data lists
        self.angle_special = []
        self.force_special = []
        self.time_data = []
        self.angle_data = []
        self.force_data = []

    def show_comparer(self):
        self.clear_content_frame()

        # Create a container frame for the Comparer page
        comparer_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        comparer_container.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Left Sidebar ---
        self.comparer_sidebar = ctk.CTkFrame(comparer_container, width=200)
        self.comparer_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Saved Figures button
        self.saved_figures_button = ctk.CTkButton(self.comparer_sidebar, text="Saved Figures",
                                                  command=self.show_saved_figures)
        self.saved_figures_button.pack(pady=10, padx=10)

        # Height adjuster button (cycles bottom section height)
        self.bottom_height_mode = "half"  # starting mode: half the main area
        self.height_adjust_button = ctk.CTkButton(self.comparer_sidebar, text="Adjust Bottom Height",
                                                  command=self.cycle_bottom_height)
        self.height_adjust_button.pack(pady=10, padx=10)

        # --- Main Content Area ---
        self.comparer_main = ctk.CTkFrame(comparer_container, fg_color="transparent")
        self.comparer_main.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Top section: combined angle vs force graph
        self.combined_graph_frame = ctk.CTkFrame(self.comparer_main, fg_color="transparent", height=200)
        self.combined_graph_frame.pack(side="top", fill="x", expand=False)
        # (We will update this frame with our combined graph in update_combined_graph())

        # Bottom section: will contain folder boxes
        self.folder_section = ctk.CTkFrame(self.comparer_main, fg_color="transparent")
        self.folder_section.pack(side="bottom", fill="both", expand=True)

        # Create a horizontally scrollable canvas for folder boxes
        self.folder_canvas = ctk.CTkCanvas(self.folder_section, bg="white")
        self.folder_canvas.pack(side="top", fill="both", expand=True)
        self.folder_scrollbar = ctk.CTkScrollbar(self.folder_section, orientation="horizontal",
                                                 command=self.folder_canvas.xview)
        self.folder_scrollbar.pack(side="bottom", fill="x")
        self.folder_canvas.configure(xscrollcommand=self.folder_scrollbar.set)

        self.folder_inner_frame = ctk.CTkFrame(self.folder_canvas, fg_color="transparent")
        self.folder_canvas.create_window((0, 0), window=self.folder_inner_frame, anchor="nw")
        self.folder_inner_frame.bind("<Configure>", lambda e: self.folder_canvas.configure(
            scrollregion=self.folder_canvas.bbox("all")))

        # For each data folder (using your sorted get_trials method), create a folder box.
        folders = self.get_trials()  # e.g., ["20250124_0000_02", "20250127_1234_01", ...]
        print(f"Found folders: {folders}")
        self.folder_boxes = {}
        for folder in folders:
            folder_box = self.create_folder_box(folder)
            folder_box.pack(side="left", padx=10, pady=10)
            self.folder_boxes[folder] = folder_box

        # Initially draw the combined graph.
        self.update_combined_graph()

    def show_saved_figures(self):
        print("Saved Figures button pressed.")
        # Implement your saved figures display logic here.

    def cycle_bottom_height(self):
        """Cycle the bottom section height between full (100%), half (50%), and none (hidden)."""
        if self.bottom_height_mode == "half":
            self.bottom_height_mode = "full"
        elif self.bottom_height_mode == "full":
            self.bottom_height_mode = "none"
        else:
            self.bottom_height_mode = "half"
        self.adjust_bottom_section_height()

    def adjust_bottom_section_height(self):
        """Adjust the folder_section (bottom area) based on the mode."""
        if self.bottom_height_mode == "full":
            # Expand folder section to fill the main content area; hide the combined graph.
            self.combined_graph_frame.pack_forget()
            self.folder_section.pack(side="top", fill="both", expand=True)
        elif self.bottom_height_mode == "half":
            # Show both: combined graph on top and folder section below.
            if not self.combined_graph_frame.winfo_ismapped():
                self.combined_graph_frame.pack(side="top", fill="x", expand=False)
            self.folder_section.pack(side="bottom", fill="both", expand=True)
        elif self.bottom_height_mode == "none":
            # Hide folder section altogether.
            self.folder_section.pack_forget()

    def create_folder_box(self, folder):
        """
        Create a box for one folder that includes:
         - A checkbox with the folder name.
         - A small angle vs force graph (Matplotlib figure).
         - Information read from information.txt.
         - A set of small checkboxes for protocol steps from the folder’s CSV file.
        """
        box = ctk.CTkFrame(self.folder_inner_frame, width=250, height=400, fg_color="lightgray")

        # Folder selection checkbox (the one next to the folder name)
        folder_var = ctk.BooleanVar(value=False)
        folder_checkbox = ctk.CTkCheckBox(box, text=folder, variable=folder_var,
                                          command=lambda: self.on_folder_checkbox_toggle(folder, folder_var))
        folder_checkbox.pack(anchor="nw", padx=5, pady=5)

        # Small angle vs force graph (a placeholder Matplotlib figure)
        fig, ax = plt.subplots(figsize=(2, 1))
        ax.plot([0, 1, 2], [0, 1, 0])  # placeholder plot
        ax.set_title("Angle vs Force", fontsize=6)
        canvas = FigureCanvasTkAgg(fig, master=box)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(padx=5, pady=5)
        canvas.draw()
        # Save the canvas so we can update it later.
        box.graph_canvas = canvas

        # Folder information read from information.txt
        info_text = self.get_folder_info(folder)
        info_label = ctk.CTkLabel(box, text=info_text, wraplength=200)
        info_label.pack(padx=5, pady=5)

        # Protocol step checkboxes for the folder (read from data.csv)
        steps_frame = ctk.CTkFrame(box)
        steps_frame.pack(padx=5, pady=5)
        # (Optional: you may want to add a scrollbar here if there are many steps.)
        protocol_steps = self.get_protocol_steps_for_folder(folder)
        step_vars = {}
        for i, step in enumerate(protocol_steps):
            sv = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(steps_frame, text=f"Step {step}", variable=sv,
                                 command=lambda s=step, v=sv: self.on_folder_step_checkbox_toggle(folder, s, v))
            # Arrange in two columns
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=5)
            step_vars[step] = sv

        box.step_vars = step_vars
        box.folder_var = folder_var  # store the folder selection variable

        return box

    def get_folder_info(self, folder):
        """Read and return information from the folder’s information.txt file."""
        info_path = os.path.join("./data", folder, "information.txt")
        if os.path.exists(info_path):
            with open(info_path, "r") as f:
                return f.read()
        return "No information available"

    def get_protocol_steps_for_folder(self, folder):
        """Read the folder’s CSV file and return a list of unique protocol steps."""
        data_path = os.path.join("./data", folder)
        csv_files = [f for f in os.listdir(data_path) if f.endswith(".csv")]
        if not csv_files:
            return []
        data_csv = os.path.join(data_path, csv_files[0])
        try:
            headers = ['Time', 'Angle', 'Force', 'raw_Force', 'Motor_State', 'Direction', 'Protocol_Step']
            df = pd.read_csv(data_csv, header=None, names=headers)
            steps = sorted(df['Protocol_Step'].unique())
            return steps
        except Exception as e:
            print(f"Error reading protocol steps for {folder}: {e}")
            return []

    def on_folder_checkbox_toggle(self, folder, var):
        """
        Called when the folder checkbox is toggled.
        Changes the folder box color and refreshes both the combined graph and the mini graph.
        """
        if var.get():
            print(f"Folder {folder} selected.")
            # Change folder box color to indicate selection.
            self.folder_boxes[folder].configure(fg_color="blue")
        else:
            print(f"Folder {folder} deselected.")
            self.folder_boxes[folder].configure(fg_color="lightgray")
        self.update_combined_graph()
        self.update_folder_mini_graph(folder)

    def on_folder_step_checkbox_toggle(self, folder, step, var):
        """
        Called when a protocol step checkbox in a folder box is toggled.
        Updates the activated protocol steps for that folder and refreshes both graphs.
        """
        if var.get():
            print(f"In folder {folder}, step {step} added to graph.")
        else:
            print(f"In folder {folder}, step {step} removed from graph.")
        self.update_combined_graph()
        self.update_folder_mini_graph(folder)

    def get_folder_color(self, folder):
        """Return a color for a given folder (different folders get different colors)."""
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        folders = self.get_trials()  # Assuming this returns folders in a sorted order.
        try:
            index = folders.index(folder)
        except ValueError:
            index = 0
        return colors[index % len(colors)]

    def update_combined_graph(self):
        """
        Re-draw the combined angle vs force graph in the top section using data from every folder
        that is selected (folder checkbox is True). For each selected folder, only plot data for the
        protocol steps that are active.
        """
        # Clear the combined graph frame.
        for widget in self.combined_graph_frame.winfo_children():
            widget.destroy()

        # Create a new figure.
        fig, ax = plt.subplots(figsize=(6, 4))
        # Loop over all folder boxes.
        for folder, box in self.folder_boxes.items():
            if box.folder_var.get():
                # Get the active protocol steps from this folder.
                active_steps = [step for step, var in box.step_vars.items() if var.get()]
                data_path = os.path.join("./data", folder)
                csv_files = [f for f in os.listdir(data_path) if f.endswith(".csv")]
                if not csv_files:
                    return []
                data_csv = os.path.join(data_path, csv_files[0])
                try:
                    headers = ['Time', 'Angle', 'Force', 'raw_Force', 'Motor_State', 'Direction', 'Protocol_Step']
                    df = pd.read_csv(data_csv, header=None, names=headers)
                    #filter the data based on the active steps
                    df = df[df['Protocol_Step'].isin(active_steps)]
                except Exception as e:
                    continue
                color = self.get_folder_color(folder)
                if not df.empty:
                    x = df['Angle']
                    y = df['Force']
                    ax.plot(x, y, label=f"{folder}", color=color)
        ax.legend(fontsize=6)
        ax.set_title("Combined Angle vs Force Graph")
        # Embed the figure into the combined_graph_frame.
        canvas = FigureCanvasTkAgg(fig, master=self.combined_graph_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()

    def update_folder_mini_graph(self, folder):
        """
        Re-draw the mini graph for a specific folder based on its active protocol steps.
        """
        box = self.folder_boxes.get(folder)
        if not box:
            return

        # Remove the old mini graph canvas if it exists.
        if hasattr(box, "graph_canvas") and box.graph_canvas:
            try:
                box.graph_canvas.get_tk_widget().destroy()
            except Exception:
                pass

        active_steps = [step for step, var in box.step_vars.items() if var.get()]

        fig, ax = plt.subplots(figsize=(2, 1))
        if active_steps:
            for step in active_steps:
                try:
                    step_offset = int(step) * 0.1
                except Exception:
                    step_offset = 0
                x = [0, 1, 2, 3]
                y = [val + step_offset for val in [0, 1, 0, 1]]
                ax.plot(x, y, label=f"Step {step}", linewidth=1)
            ax.legend(fontsize=4)
        else:
            ax.text(0.5, 0.5, "No Active Steps", ha="center", va="center", fontsize=6)
        ax.set_title("Angle vs Force", fontsize=6)

        canvas = FigureCanvasTkAgg(fig, master=box)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(padx=5, pady=5)
        canvas.draw()
        box.graph_canvas = canvas  # Store the new canvas.


# Start the application
if __name__ == "__main__":
    app = App(demo_mode=True)  # Enable demo mode
    app.mainloop()
