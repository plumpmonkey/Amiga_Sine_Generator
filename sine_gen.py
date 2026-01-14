
import math
import argparse
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def calculate_points(n_points, amplitude, mod_amp=0, mod_freq=1, period_mode="full"):
    points = []
    
    start_angle = 0.0
    end_angle = 2.0 * math.pi
    
    if period_mode == "half":
        end_angle = math.pi
    elif period_mode == "neg_half":
        start_angle = math.pi
        end_angle = 2.0 * math.pi
        
    angle_range = end_angle - start_angle
    
    for i in range(n_points):
        # Map i from 0..n_points to start_angle..end_angle
        angle = start_angle + (i / n_points * angle_range)
        
        # Primary Sine
        val1 = math.sin(angle) * amplitude
        
        # Modulation Sine
        # Modulation usually continues based on the absolute angle to maintain phase continuity or
        # it can be relative to the window. 
        # For simplicity and predictability in "half" modes, let's keep it relative to the angle being sampled.
        val2 = math.sin(angle * mod_freq) * mod_amp
        
        value_float = val1 + val2
        value = int(value_float)
        
        # Clamp to 8-bit signed range [-128, 127]
        value = max(-128, min(127, value))
        points.append(value)
    return points

def generate_source_asm(label, points):
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

    lines.append(f"endsine:") # Fixed label usage elsewhere if needed, but endsine is legacy from original
    # Actually, original code used f"end{label}:". Let's preserve that.
    lines[-1] = f"end{label}:"
    
    return "\n".join(lines) + "\n"

def generate_source_c(label, points):
    lines = []
    lines.append(f"signed char {label}[] = {{")
    
    current_line_parts = []
    for i, p in enumerate(points):
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                lines.append(f"    {', '.join(current_line_parts)},")
                current_line_parts = []
        current_line_parts.append(str(p))
    
    if current_line_parts:
         lines.append(f"    {', '.join(current_line_parts)}")

    lines.append(f"}};")
    return "\n".join(lines) + "\n"

def generate_source_blitz(label, points):
    lines = []
    lines.append(f".{label}")
    
    current_line_parts = []
    for i, p in enumerate(points):
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                lines.append(f"    Data.b {', '.join(current_line_parts)}")
                current_line_parts = []
        current_line_parts.append(str(p))
    
    if current_line_parts:
         lines.append(f"    Data.b {', '.join(current_line_parts)}")

    lines.append(f".end{label}")
    return "\n".join(lines) + "\n"

def generate_source(label, points, fmt="asm"):
    if fmt == "c":
        return generate_source_c(label, points)
    elif fmt == "blitz":
        return generate_source_blitz(label, points)
    else:
        return generate_source_asm(label, points)

def generate_sine_table(label, n_points, amplitude, mod_amp=0, mod_freq=1, period_mode="full", fmt="asm"):
    points = calculate_points(n_points, amplitude, mod_amp, mod_freq, period_mode)
    return generate_source(label, points, fmt)

# --- GUI ---

class SineApp:
    def __init__(self, root, args):
        self.root = root
        self.root.title("Sine Table Generator")
        self.root.geometry("600x825")
        
        # Variables
        self.label_var = tk.StringVar(value=args.label)
        self.points_var = tk.IntVar(value=args.points)
        self.amplitude_var = tk.IntVar(value=args.amplitude)
        self.format_var = tk.StringVar(value=args.format)
        
        # Advanced Variables
        self.mod_amp_var = tk.IntVar(value=args.mod_amp)
        self.mod_freq_var = tk.IntVar(value=args.mod_freq)
        
        # Map args to period string
        p_val = "Full (360°)"
        if args.period == "half": p_val = "Half (Positive)"
        elif args.period == "neg_half": p_val = "Half (Negative)"
        
        self.period_var = tk.StringVar(value=p_val)
        
        self.create_widgets()
        self.update_all()

    def create_widgets(self):
        # --- Primary Frame ---
        primary_frame = ttk.LabelFrame(self.root, text="Primary Wave", padding="10")
        primary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 0: Label
        ttk.Label(primary_frame, text="Label:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(primary_frame, textvariable=self.label_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Row 1: Points
        ttk.Label(primary_frame, text="Points:").grid(row=1, column=0, sticky=tk.W)
        self.points_slider = ttk.Scale(primary_frame, from_=0, to=255, variable=self.points_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.points_slider.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.points_label = ttk.Label(primary_frame, text=str(self.points_var.get()))
        self.points_label.grid(row=1, column=2, sticky=tk.W)
        
        # Row 2: Amplitude
        ttk.Label(primary_frame, text="Amplitude:").grid(row=2, column=0, sticky=tk.W)
        self.amplitude_slider = ttk.Scale(primary_frame, from_=0, to=255, variable=self.amplitude_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.amplitude_slider.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.amplitude_label = ttk.Label(primary_frame, text=str(self.amplitude_var.get()))
        self.amplitude_label.grid(row=2, column=2, sticky=tk.W)

        # Row 3: Format
        ttk.Label(primary_frame, text="Format:").grid(row=3, column=0, sticky=tk.W)
        self.format_combo = ttk.Combobox(primary_frame, textvariable=self.format_var, values=["asm", "c", "blitz"], state="readonly")
        self.format_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self.update_all())
        
        # Row 4: Period
        ttk.Label(primary_frame, text="Period:").grid(row=4, column=0, sticky=tk.W)
        self.period_combo = ttk.Combobox(primary_frame, textvariable=self.period_var, values=["Full (360°)", "Half (Positive)", "Half (Negative)"], state="readonly")
        self.period_combo.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.period_combo.bind("<<ComboboxSelected>>", lambda e: self.update_all())

        primary_frame.columnconfigure(1, weight=1)
        
        # --- Modulation Frame ---
        mod_frame = ttk.LabelFrame(self.root, text="Modulation (Add Second Sine)", padding="10")
        mod_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 0: Mod Amp
        ttk.Label(mod_frame, text="Mod Amp:").grid(row=0, column=0, sticky=tk.W)
        self.mod_amp_slider = ttk.Scale(mod_frame, from_=0, to=128, variable=self.mod_amp_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.mod_amp_slider.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.mod_amp_label = ttk.Label(mod_frame, text=str(self.mod_amp_var.get()))
        self.mod_amp_label.grid(row=0, column=2, sticky=tk.W)
        
        # Row 1: Mod Freq
        ttk.Label(mod_frame, text="Mod Freq:").grid(row=1, column=0, sticky=tk.W)
        self.mod_freq_slider = ttk.Scale(mod_frame, from_=1, to=10, variable=self.mod_freq_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.mod_freq_slider.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.mod_freq_label = ttk.Label(mod_frame, text=str(self.mod_freq_var.get()))
        self.mod_freq_label.grid(row=1, column=2, sticky=tk.W)
        
        mod_frame.columnconfigure(1, weight=1)

        # Execution Time (Moved to own simple frame or pack directly)
        info_frame = ttk.Frame(self.root, padding="5")
        info_frame.pack(fill=tk.X, padx=10)
        self.time_label = ttk.Label(info_frame, text="")
        self.time_label.pack(anchor=tk.W)

        # Buttons (Pack first to ensure visibility at bottom)
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.save_btn = ttk.Button(btn_frame, text="Save file", command=self.save_file)
        self.save_btn.pack(side=tk.RIGHT)

        # Plot Frame
        plot_frame = ttk.LabelFrame(self.root, text="Visualization", padding="10")
        plot_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        self.canvas = tk.Canvas(plot_frame, bg="#2b2b2b", height=200)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Output Frame
        output_frame = ttk.LabelFrame(self.root, text="Generated Code", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_area = tk.Text(output_frame, height=10, width=50)
        self.text_area.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_area['yscrollcommand'] = scrollbar.set
        
        # Add trace to label to update on change
        self.label_var.trace_add("write", lambda *args: self.update_all())

    def on_change(self, *args):
        self.points_label.config(text=str(self.points_var.get()))
        self.amplitude_label.config(text=str(self.amplitude_var.get()))
        self.mod_amp_label.config(text=str(self.mod_amp_var.get()))
        self.mod_freq_label.config(text=str(self.mod_freq_var.get()))
        self.update_all()

    def update_all(self):
        try:
            points_count = self.points_var.get()
            amplitude = self.amplitude_var.get()
            label = self.label_var.get()
            fmt = self.format_var.get()
            
            mod_amp = self.mod_amp_var.get()
            mod_freq = self.mod_freq_var.get()
            
            p_gui = self.period_var.get()
            period_mode = "full"
            if "Positive" in p_gui: period_mode = "half"
            elif "Negative" in p_gui: period_mode = "neg_half"
            
            if points_count == 0:
                self.text_area.delete(1.0, tk.END)
                self.canvas.delete("all")
                return

            # Calc points
            points = calculate_points(points_count, amplitude, mod_amp, mod_freq, period_mode)
            
            # Update Code
            code = generate_source(label, points, fmt)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, code)
            
            # Update Plot
            self.draw_plot(points, amplitude)
            
            # Update Time Label
            time_50hz = points_count * 0.02
            time_60hz = points_count * (1/60)
            self.time_label.config(text=f"{time_50hz:.4f} seconds at 50hz, {time_60hz:.4f} seconds at 60hz")

            # Update button text
            ext = ".s"
            if fmt == "c": ext = ".c"
            if fmt == "blitz": ext = ".bb"
            self.save_btn.config(text=f"Save {label}{ext}")
            
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
        fmt = self.format_var.get()
        ext = ".s"
        filetypes = [("Assembly Source", "*.s"), ("All Files", "*.*")]
        
        if fmt == "c": 
            ext = ".c"
            filetypes = [("C Source", "*.c"), ("All Files", "*.*")]
        elif fmt == "blitz":
            ext = ".bb"
            filetypes = [("Blitz Basic", "*.bb"), ("All Files", "*.*")]
            
        filename = f"{self.label_var.get()}{ext}"
        file_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=ext, filetypes=filetypes)
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
    parser.add_argument("--format", choices=["asm", "c", "blitz"], default="asm", help="Output format (asm, c, blitz). Default: asm")
    parser.add_argument("--mod-amp", type=int, default=0, help="Modulation amplitude (default: 0)")
    parser.add_argument("--mod-freq", type=int, default=1, help="Modulation frequency (default: 1)")
    parser.add_argument("--period", choices=["full", "half", "neg_half"], default="full", help="Period mode: full, half, neg_half. Default: full")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode")
    
    args = parser.parse_args()
    
    if args.cli:
        code = generate_sine_table(args.label, args.points, args.amplitude, args.mod_amp, args.mod_freq, args.period, args.format)
        
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
