import tkinter as tk
import os

class SimpleApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Use an absolute path for the icon file
        icon_path = os.path.abspath('./img/rat_icon_187523.png')
        try:
            self.iconbitmap(icon_path)
            print("Icon set successfully.")
        except Exception as e:
            print(f"Failed to set icon: {e}")

        self.title("Simple Tkinter App")
        self.geometry("300x200")

        label = tk.Label(self, text="Hello, Tkinter!")
        label.pack(pady=20)

if __name__ == "__main__":
    app = SimpleApp()
    app.mainloop()