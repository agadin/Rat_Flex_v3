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
from PIL import ImageGrab

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
    print("Running calibration...")


class App(ctk.CTk):
    def __init__(self, demo_mode=True):
        super().__init__()
        self.demo_mode = demo_mode

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

        for btn in (self.home_button, self.protocol_builder_button, self.inspector_button, self.settings_button):
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
            self.step_display.configure(text="Steps: 100")
            self.angle_display.configure(text="Angle: 45.0°")
            self.force_display.configure(text="Force: 10.5N")
    def show_protocol_builder(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Protocol Builder (Coming Soon)").pack(pady=20)

    def get_trials(self):
        data_dir = "./data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return [folder for folder in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, folder))] or [
            "No Trials Found"]

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

        # Clear existing checkboxes if exist
        if hasattr(self, "checkbox_frame") and self.checkbox_frame.winfo_exists():
            self.checkbox_frame.destroy()

        # Frame for checkboxes at the bottom of main_content
        checkbox_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        checkbox_frame.pack(side="bottom", fill="x", pady=10)

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
                checkbox_frame, text=f"Step {step}", variable=var, command=checkbox_callback
            )
            checkbox.grid(row=i // num_columns, column=i % num_columns, padx=5, pady=5, sticky="w")

        # Add "Remove Wait" checkbox for all even Protocol_Steps
        remove_wait_var = ctk.BooleanVar(value=False)
        self.checkbox_states["Remove Wait"] = remove_wait_var
        remove_wait_checkbox = ctk.CTkCheckBox(
            checkbox_frame, text="Remove Wait", variable=remove_wait_var, command=checkbox_callback
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
        """Add tables to display general statistics and detailed calculations."""

        # Frame for the tables
        table_frame = ttk.Frame(self.canvas_frame)
        table_frame.grid(row=0, column=2, rowspan=rowspan, padx=5, pady=5, sticky="nsew")

        # General statistics table
        general_stats_frame = ttk.Frame(table_frame)
        general_stats_frame.pack(fill="x", pady=10)

        # Extract general stats
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

        # General statistics data
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

        # Setup general stats table
        general_tree = ttk.Treeview(general_stats_frame, columns=list(general_stats.columns), show="headings",
                                    height=10)
        for col in general_stats.columns:
            general_tree.heading(col, text=col)
            general_tree.column(col, anchor="center", width=150)

        # Add rows to general stats table
        for _, row in general_stats.iterrows():
            general_tree.insert("", "end", values=list(row))

        general_tree.pack(fill="x")

        # Detailed statistics table
        detailed_stats_frame = ttk.Frame(table_frame)
        detailed_stats_frame.pack(fill="x", pady=10)

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

        # Add summary row as a new row in the DataFrame
        summary_row = pd.DataFrame([{
            "Protocol_Step": "Summary",
            "RoM": f"{angle_diff.mean():.1f} | {angle_diff.std():.1f}",
            "Points in IQR": f"{points_within_iqr.mean():.1f} | {points_within_iqr.std():.1f}"
        }])
        custom_data = pd.concat([custom_data, summary_row], ignore_index=True)

        # Sort rows by Protocol_Step (numerically, except for "Summary")
        custom_data["Protocol_Step_Numeric"] = pd.to_numeric(custom_data["Protocol_Step"], errors="coerce")
        custom_data = custom_data.sort_values(
            by=["Protocol_Step_Numeric", "Protocol_Step"],
            ascending=[True, True]
        ).drop(columns=["Protocol_Step_Numeric"])

        # Dynamically calculate the height of the detailed stats table
        table_height = len(custom_data)

        # Setup detailed stats table
        detailed_tree = ttk.Treeview(detailed_stats_frame, columns=list(custom_data.columns), show="headings",
                                     height=table_height)
        for col in custom_data.columns:
            detailed_tree.heading(col, text=col)
            detailed_tree.column(col, anchor="center", width=150)

        # Add rows to detailed stats table
        for _, row in custom_data.iterrows():
            detailed_tree.insert("", "end", values=list(row))

        detailed_tree.pack(fill="x")

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
        import os
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        import pandas as pd
        import matplotlib.pyplot as plt

        # Create a folder for saving
        save_dir = os.path.join(self.trial_path, "screenshots")
        os.makedirs(save_dir, exist_ok=True)

        # Save each matplotlib figure
        for i, fig in enumerate(plt.get_fignums()):
            plt.figure(fig)
            fig_path = os.path.join(save_dir, f"figure_{i + 1}.png")
            plt.savefig(fig_path, dpi=300)
            print(f"Saved figure: {fig_path}")

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

        # Clear the graph by redrawing it with empty data

# Start the application
if __name__ == "__main__":
    app = App(demo_mode=True)  # Enable demo mode
    app.mainloop()
