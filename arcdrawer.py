import tkinter as tk
import math
import os

class AdvancedCurvedSlider(tk.Canvas):
    def __init__(self, master, width=300, height=200, min_val=10, max_val=170, parent_app=None, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.parent_app = parent_app  # Reference to the main app (used to call run_protocol)
        self.min_val = min_val
        self.max_val = max_val
        self.value = min_val

        # Parameters for the arc
        self.radius = 100                   # Radius of the circle that defines the arc
        self.center_x = width // 2          # Center of the circle (x-coordinate)
        self.center_y = height - 20         # Adjust center_y so that the arc (top half) fits well

        # Blue circle starting position (angle = π radians)
        self.blue_angle = math.pi

        # Draw the 180° arc (open downward)
        self.create_arc(self.center_x - self.radius, self.center_y - self.radius,
                        self.center_x + self.radius, self.center_y + self.radius,
                        start=0, extent=180, style='arc', width=2)

        # Create the blue (draggable) circle.
        self.handle_radius = 10
        self.blue_circle = self.create_oval(0, 0, 0, 0, fill="blue", outline="", tags="blue_circle")
        self.update_blue_position()

        # Bind mouse events for the blue circle.
        self.tag_bind("blue_circle", "<ButtonPress-1>", self.on_blue_press)
        self.tag_bind("blue_circle", "<B1-Motion>", self.on_blue_drag)
        self.tag_bind("blue_circle", "<ButtonRelease-1>", self.on_blue_release)
        # Bind canvas click for target marker.
        self.bind("<Button-1>", self.on_canvas_click)

        self.dragging = False

        # Target marker (orange circle) and its angle.
        self.target_circle = None
        self.target_angle = None

        # Control frame for Jog button and value entry – not part of the slider itself,
        # but left here for completeness. (You may choose to integrate this elsewhere.)
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(pady=10)
        self.jog_button = tk.Button(self.control_frame, text="Jog", command=self.on_jog, state="disabled")
        self.jog_button.pack(side="left", padx=5)
        self.angle_var = tk.StringVar()
        self.angle_entry = tk.Entry(self.control_frame, textvariable=self.angle_var, width=5)
        self.angle_entry.pack(side="left", padx=5)
        self.angle_entry.bind("<Return>", self.on_entry_return)
        # Label for displaying target value (in orange)
        self.target_text = tk.Label(self.control_frame, text="", fg="orange")
        # Not packed initially

    def value_from_angle(self, angle):
        """Map an angle (0 to π) to a value between min_val and max_val."""
        val = self.min_val + (self.max_val - self.min_val) * ((math.pi - angle) / math.pi)
        return round(val, 2)

    def angle_from_value(self, value):
        """Map a value between min_val and max_val back to an angle (in radians)."""
        angle = math.pi - ((value - self.min_val) / (self.max_val - self.min_val)) * math.pi
        return angle

    def update_blue_position(self):
        """Update the blue circle's position based on its current angle."""
        x = self.center_x + self.radius * math.cos(self.blue_angle)
        y = self.center_y - self.radius * math.sin(self.blue_angle)
        self.coords(self.blue_circle,
                    x - self.handle_radius, y - self.handle_radius,
                    x + self.handle_radius, y + self.handle_radius)
        self.angle_var.set(str(self.value_from_angle(self.blue_angle)))

    def set_blue_angle(self, angle_degrees):
        """Update the blue circle's position using an angle in degrees.
           Converts degrees (0–180) to radians and updates the position.
        """
        angle_radians = math.radians(angle_degrees)
        self.blue_angle = angle_radians
        self.update_blue_position()

    def on_blue_press(self, event):
        self.dragging = True

    def on_blue_drag(self, event):
        if self.dragging:
            dx = event.x - self.center_x
            dy = self.center_y - event.y  # Invert y (canvas y increases downward)
            angle = math.atan2(dy, dx)
            angle = max(0, min(math.pi, angle))
            self.blue_angle = angle
            self.update_blue_position()

    def on_blue_release(self, event):
        if self.dragging:
            self.dragging = False
            # Send command after dragging stops
            self.send_command(self.blue_angle)

    def on_canvas_click(self, event):
        # If click is on blue circle, ignore it
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
        # Update target text with value
        target_value = self.value_from_angle(self.target_angle)
        self.target_text.config(text=str(target_value))
        if not self.target_text.winfo_ismapped():
            self.target_text.pack(side="left", padx=5)

    def on_jog(self):
        if self.target_angle is None:
            return
        self.jog_button.config(state="disabled")
        self.animate_move(self.blue_angle, self.target_angle, callback=self.on_jog_complete)

    def on_jog_complete(self):
        self.send_command(self.blue_angle)
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
        target_angle = self.angle_from_value(val)
        self.animate_move(self.blue_angle, target_angle,
                          callback=lambda: self.send_command(self.blue_angle))

    def animate_move(self, start_angle, target_angle, steps=20, delay=20, callback=None):
        delta = (target_angle - start_angle) / steps
        def step(i, current_angle):
            if i >= steps:
                self.blue_angle = target_angle
                self.update_blue_position()
                if callback:
                    callback()
                return
            current_angle += delta
            self.blue_angle = current_angle
            self.update_blue_position()
            self.after(delay, lambda: step(i+1, current_angle))
        step(0, start_angle)

    def send_command(self, angle):
        """Send command: wipe out temp.txt and write the command, then run the protocol.
           The command string is:
               no_save
               Move_to_angle_jog: {angle}
        """
        command_string = f"no_save\nMove_to_angle_jog: {angle}"
        temp_file = os.path.join("protocols", "temp.txt")
        try:
            # Open temp.txt in write mode to wipe and then write new command
            with open(temp_file, "w") as f:
                f.write(command_string)
        except Exception as e:
            print("Error writing to temp.txt:", e)
        # Call the parent app's run_protocol method with temp.txt.
        if self.parent_app is not None:
            self.parent_app.run_protocol(temp_file)
        else:
            print("Parent app not set. Cannot run protocol.")

# Example usage:
# When creating the slider in your show_home method, pass the main app reference:
# self.advanced_slider = AdvancedCurvedSlider(slider_container, width=300, height=200, min_val=10, max_val=170, parent_app=self)
