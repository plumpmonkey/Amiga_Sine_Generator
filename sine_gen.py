
import math
import argparse
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Logic ---

# ... (rest of file) ...



def calculate_points(n_points, amplitude):
    points = []
    for i in range(n_points):
        angle = i / n_points * (2.0 * math.pi)
        value_float = math.sin(angle) * amplitude
        value = int(value_float)
        # Clamp to 8-bit signed range [-128, 127]
        value = max(-128, min(127, value))
        points.append(value)
    return points

def generate_source(label, points):
    lines = []
    lines.append(f"{label}:")
    
    current_line_parts = []
    
    for i, p in enumerate(points):
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                lines.append(f"    dc.b {', '.join(current_line_parts)}")
                current_line_parts = []
        current_line_parts.append(str(p))
    
    if current_line_parts:
         lines.append(f"    dc.b {', '.join(current_line_parts)}")

    lines.append(f"end{label}:")
    
    return "\n".join(lines) + "\n"

def generate_sine_table(label, n_points, amplitude):
    points = calculate_points(n_points, amplitude)
    return generate_source(label, points)

# --- GUI ---

class SineApp:
    def __init__(self, root, args):
        self.root = root
        self.root.title("Sine Table Generator")
        self.root.geometry("600x700")
        
        # Variables
        self.label_var = tk.StringVar(value=args.label)
        self.points_var = tk.IntVar(value=args.points)
        self.amplitude_var = tk.IntVar(value=args.amplitude)
        
        self.create_widgets()
        self.update_all()

    def create_widgets(self):
        # Controls Frame
        controls_frame = ttk.LabelFrame(self.root, text="Settings", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 1: Label
        ttk.Label(controls_frame, text="ASM Label:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(controls_frame, textvariable=self.label_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Row 2: Points
        ttk.Label(controls_frame, text="Points:").grid(row=1, column=0, sticky=tk.W)
        self.points_slider = ttk.Scale(controls_frame, from_=0, to=255, variable=self.points_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.points_slider.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.points_label = ttk.Label(controls_frame, text=str(self.points_var.get()))
        self.points_label.grid(row=1, column=2, sticky=tk.W)
        
        # Row 3: Amplitude
        ttk.Label(controls_frame, text="Amplitude:").grid(row=2, column=0, sticky=tk.W)
        self.amplitude_slider = ttk.Scale(controls_frame, from_=0, to=255, variable=self.amplitude_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.amplitude_slider.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.amplitude_label = ttk.Label(controls_frame, text=str(self.amplitude_var.get()))
        self.amplitude_label.grid(row=2, column=2, sticky=tk.W)

        # Row 4: Execution Time
        self.time_label = ttk.Label(controls_frame, text="")
        self.time_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(5,0))

        controls_frame.columnconfigure(1, weight=1)

        # Buttons (Pack first to ensure visibility at bottom)
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.save_btn = ttk.Button(btn_frame, text="Save .s file", command=self.save_file)
        self.save_btn.pack(side=tk.RIGHT)

        # Plot Frame
        plot_frame = ttk.LabelFrame(self.root, text="Visualization", padding="10")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(plot_frame, bg="#2b2b2b", height=200)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Output Frame
        output_frame = ttk.LabelFrame(self.root, text="Generated Code", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_area = tk.Text(output_frame, height=12, width=50)
        self.text_area.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_area['yscrollcommand'] = scrollbar.set
        
        # Add trace to label to update on change
        self.label_var.trace_add("write", lambda *args: self.update_all())

    def on_change(self, *args):
        self.points_label.config(text=str(self.points_var.get()))
        self.amplitude_label.config(text=str(self.amplitude_var.get()))
        self.update_all()

    def update_all(self):
        try:
            points_count = self.points_var.get()
            amplitude = self.amplitude_var.get()
            label = self.label_var.get()
            
            if points_count == 0:
                self.text_area.delete(1.0, tk.END)
                self.canvas.delete("all")
                return

            # Calc points
            points = calculate_points(points_count, amplitude)
            
            # Update Code
            code = generate_source(label, points)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, code)
            
            # Update Plot
            self.draw_plot(points, amplitude)
            
            # Update Time Label
            time_50hz = points_count * 0.02
            time_60hz = points_count * (1/60)
            self.time_label.config(text=f"{time_50hz:.4f} seconds at 50hz, {time_60hz:.4f} seconds at 60hz")

            # Update button text
            self.save_btn.config(text=f"Save {label}.s")
            
        except Exception as e:
            pass

    def draw_plot(self, points, amplitude):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # If canvas isn't drawn yet, use default size estimate
        if w < 10: w = 550
        if h < 10: h = 200

        center_y = h / 2
        
        if not points:
            return

        # Scales
        x_step = w / len(points)
        y_scale = (h / 2) / 130 

        prev_x = 0
        prev_y = center_y + (points[0] * y_scale)
        
        # Guidelines
        self.canvas.create_line(0, center_y, w, center_y, fill="#555555", dash=(2, 4))

        for i in range(1, len(points)):
            x = i * x_step
            # For Amiga/screen coords, positive is down
            y = center_y + (points[i] * y_scale)
            self.canvas.create_line(prev_x, prev_y, x, y, fill="#00ff00", width=2)
            # Draw point
            self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="#ffff00", outline="")
            
            prev_x = x
            prev_y = y

    def save_file(self):
        filename = f"{self.label_var.get()}.s"
        file_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=".s", filetypes=[("Assembly Source", "*.s"), ("All Files", "*.*")])
        if file_path:
            try:
                code = self.text_area.get(1.0, tk.END)
                with open(file_path, "w") as f:
                    f.write(code)
                messagebox.showinfo("Success", f"Saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Sine Generator for 68000 Assembly")
    parser.add_argument("--label", default="sine", help="ASM label name (default: sine)")
    parser.add_argument("--points", type=int, default=64, help="Number of points (default: 64)")
    parser.add_argument("--amplitude", type=int, default=30, help="Amplitude (default: 30)")
    parser.add_argument("--output", help="Output file (optional)")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode")
    
    args = parser.parse_args()
    
    if args.cli:
        code = generate_sine_table(args.label, args.points, args.amplitude)
        
        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(code)
                print(f"Written to {args.output}")
            except IOError as e:
                print(f"Error writing to file: {e}", file=sys.stderr)
        else:
            print(code)
    else:
        try:
            root = tk.Tk()
            app = SineApp(root, args)
            root.bind("<Configure>", lambda e: app.update_all() if e.widget == app.canvas else None)
            root.mainloop()
        except Exception as e:
            print(f"GUI ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
