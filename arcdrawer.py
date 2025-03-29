import tkinter as tk
import math
import os
import customtkinter as ctk

class AdvancedCurvedSlider(tk.Canvas):
    def __init__(self, master, width=300, height=200, min_val=10, max_val=170, parent_app=None, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.parent_app = parent_app
        self.min_val = min_val
        self.max_val = max_val
        self.value = min_val  # Starting value is 10
        self.user_typing = False  # Flag to track if the user is typing

        # Arc parameters
        self.radius = 100
        self.center_x = width // 2
        self.center_y = height - 20

        # Initialize the blue handle at the left end (angle = π) so its value is 10.
        self.blue_angle = math.pi

        # Draw the 180° arc (from right (angle 0) to left (angle π))
        self.create_arc(self.center_x - self.radius, self.center_y - self.radius,
                        self.center_x + self.radius, self.center_y + self.radius,
                        start=0, extent=180, style='arc', width=2)

        # Create the blue (draggable) circle.
        self.handle_radius = 10
        self.blue_circle = self.create_oval(0, 0, 0, 0, fill="blue", outline="", tags="blue_circle")

        # Bind mouse events for the blue circle.
        self.tag_bind("blue_circle", "<ButtonPress-1>", self.on_blue_press)
        self.tag_bind("blue_circle", "<B1-Motion>", self.on_blue_drag)
        self.tag_bind("blue_circle", "<ButtonRelease-1>", self.on_blue_release)
        # Bind canvas click for setting a target marker.
        self.bind("<Button-1>", self.on_canvas_click)

        self.dragging = False

        # Target marker (orange circle) and its angle.
        self.target_circle = None
        self.target_angle = None

        # Control frame for Jog button and value entry.
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=10)
        self.jog_button = ctk.CTkButton(self.control_frame, text="Jog", command=self.on_jog, state="disabled")
        self.jog_button.pack(side="left", padx=5)
        self.angle_var = tk.StringVar()
        self.angle_entry = ctk.CTkEntry(self.control_frame, textvariable=self.angle_var, width=50)
        self.angle_entry.pack(side="left", padx=5)
        self.angle_entry.bind("<Return>", self.on_entry_return)
        self.angle_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.angle_entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.target_text = ctk.CTkLabel(self.control_frame, text="", text_color="orange")

        self.update_blue_position()

    def on_entry_focus_in(self, event):
        self.user_typing = True

    def on_entry_focus_out(self, event):
        self.user_typing = False

    def value_from_angle(self, angle):
        """
        Map an angle (π to 0) to a value between min_val and max_val.
        With this function:
          - When angle = π (left), value = min_val (10)
          - When angle = 0 (right), value = max_val (170)
        """
        return angle * (180 / math.pi)

    def angle_from_value(self, value):
        """
        Inverse of value_from_angle: compute the angle (in radians) from a given value.
        """
        return value * (math.pi / 180)

    def update_blue_position(self):
        """
        Update the blue circle's (handle) position on the canvas based on its current angle.
        """
        if not self.user_typing:
            print(f"self.blue_angle={self.blue_angle}")
            blue_angle = math.pi - self.blue_angle
            x = self.center_x + self.radius * math.cos(blue_angle)
            y = self.center_y - self.radius * math.sin(blue_angle)
            self.coords(self.blue_circle,
                        x - self.handle_radius, y - self.handle_radius,
                        x + self.handle_radius, y + self.handle_radius)
            self.angle_var.set(str(self.value_from_angle(self.blue_angle)))

    def set_blue_angle(self, angle_degrees):
        """
        Set the blue circle's position using an angle in degrees.
        """
        self.blue_angle = math.radians(angle_degrees)
        self.update_blue_position()

    def on_blue_press(self, event):
        self.dragging = True

    def on_blue_drag(self, event):
        if self.dragging:
            dx = event.x - self.center_x
            dy = self.center_y - event.y  # Invert y (because canvas y increases downward)
            angle = math.atan2(dy, dx)
            # Clamp the angle between 0 and π so the value stays between 10 and 170.
            angle = max(0, min(math.pi, angle))
            self.blue_angle = angle
            self.update_blue_position()

    def on_blue_release(self, event):
        if self.dragging:
            self.dragging = False
            self.send_command(self.blue_angle)

    def on_canvas_click(self, event):
        # Ignore the click if it's on the blue circle.
        items = self.find_overlapping(event.x, event.y, event.x, event.y)
        if self.blue_circle in items:
            return
        dx = event.x - self.center_x
        dy = self.center_y - event.y
        angle = math.atan2(dy, dx)
        angle = max(0, min(math.pi, angle))
        self.target_angle = angle
        x = self.center_x + self.radius * math.cos(angle)
        y = self.center_y - self.radius * math.sin(angle)
        if self.target_circle is None:
            self.target_circle = self.create_oval(
                x - self.handle_radius, y - self.handle_radius,
                x + self.handle_radius, y + self.handle_radius,
                fill="orange", outline=""
            )
        else:
            self.coords(self.target_circle,
                        x - self.handle_radius, y - self.handle_radius,
                        x + self.handle_radius, y + self.handle_radius)
        self.jog_button.config(state="normal")
        target_value = round(180 - self.target_angle * (180 / math.pi), 1)
        self.target_text.configure(text=str(target_value))
        if not self.target_text.winfo_ismapped():
            self.target_text.pack(side="left", padx=5)

    def on_jog(self):
        if self.target_angle is None:
            return
        self.jog_button.config(state="disabled")
        # target_value=round(self.target_angle * (180 / math.pi), 2)
        #convert target_value to radians
        # target_value = math.radians(target_value)
        print(f"Jogging to {self.target_angle}")
        self.send_command(self.target_angle)
        self.on_jog_complete()

    def on_jog_complete(self):
        if self.target_circle:
            self.delete(self.target_circle)
            self.target_circle = None
        self.target_angle = None
        if self.target_text.winfo_ismapped():
            self.target_text.pack_forget()

    def on_entry_return(self, event):
        try:
            val = float(self.angle_var.get())
        except ValueError:
            return
        val = max(self.min_val, min(self.max_val, val))
        adjusted_val = val - 180  # Subtract 180 from the user input
        self.blue_angle = self.angle_from_value(adjusted_val)
        self.update_blue_position()
        self.angle_var.set(f"{val:.1f}")  # Round the input display to 1 decimal place
        self.send_command(self.blue_angle)

    def send_command(self, angle):
        """
        Send a command by writing to a temporary file and (if set) calling the parent app's protocol runner.
        The command is formatted with the angle (in degrees).
        """
        angle_deg = round(180 - math.degrees(angle))
        print(f"Sending command: {angle_deg}")
        command_string = f"no_save\nMove_to_angle_jog: {angle_deg}"
        temp_file = os.path.join("protocols", "temp.txt")
        try:
            with open(temp_file, "w") as f:
                f.write(command_string)
        except Exception as e:
            print("Error writing to temp.txt:", e)
        if self.parent_app is not None:
            # remove ./protocols/ from the path
            temp_file = temp_file[10:]
            self.parent_app.run_protocol(temp_file)
        else:
            print("Parent app not set. Cannot run protocol.")