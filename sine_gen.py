
import math
import argparse
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Function to calculate sine wave points based on parameters
def calculate_points(n_points, amplitude, mod_amp=0, mod_freq=1, period_mode="full", offset=0):
    """
    Calculates a set of sine wave points based on the provided parameters.

    This function generates a series of points representing a sine wave, optionally
    modulated by a second sine wave. The result is clamped based on period mode:
    - full: [-128, 127] (signed byte)
    - half: [0, 255] (unsigned byte, positive wave)
    - neg_half: [-255, 0] (negative wave)

    Args:
        n_points (int): The number of points to generate.
        amplitude (int): The amplitude of the primary sine wave.
        mod_amp (int, optional): The amplitude of the modulation sine wave. Defaults to 0.
        mod_freq (int, optional): The frequency multiplier for the modulation wave. Defaults to 1.
        period_mode (str, optional): The period mode ("full", "half", "neg_half"). Defaults to "full".
        offset (int, optional): Offset to shift the wave center. Defaults to 0.

    Returns:
        list: A list of integer values representing the sine wave points, clamped per mode.
    """
    # Initialize the list to hold the calculated points
    points = []
    
    # Define the starting angle for the sine wave
    start_angle = 0.0
    # Define the ending angle (default is full circle 2*PI)
    end_angle = 2.0 * math.pi
    
    # Adjust angles based on the period mode
    if period_mode == "half":
        # Half period (positive cycle only)
        end_angle = math.pi
    elif period_mode == "neg_half":
        # Negative half period (PI to 2*PI)
        start_angle = math.pi
        end_angle = 2.0 * math.pi
        
    # Calculate the total range of the angle
    angle_range = end_angle - start_angle
    
    # Determine clamping range based on period mode
    if period_mode == "half":
        # Unsigned byte range for positive half-wave
        clamp_min, clamp_max = 0, 255
    elif period_mode == "neg_half":
        # Negative range for negative half-wave
        clamp_min, clamp_max = -255, 0
    else:
        # Signed byte range for full wave
        clamp_min, clamp_max = -128, 127
    
    # Loop through the number of points requested
    for i in range(n_points):
        # Map the current index i from 0..n_points to start_angle..end_angle
        angle = start_angle + (i / n_points * angle_range)
        
        # Calculate the Primary Sine value
        val1 = math.sin(angle) * amplitude
        
        # Calculate the Modulation Sine value
        # Modulation usually continues based on the absolute angle to maintain phase continuity or
        # it can be relative to the window. 
        # For simplicity and predictability in "half" modes, let's keep it relative to the angle being sampled.
        val2 = math.sin(angle * mod_freq) * mod_amp
        
        # Combine the primary and modulation values, then add offset
        value_float = val1 + val2 + offset
        # Convert the float result to an integer
        value = int(value_float)
        
        # Clamp the value to the appropriate range based on period mode
        value = max(clamp_min, min(clamp_max, value))
        # Append the calculated value to the points list
        points.append(value)
        
    # Return the list of calculated points
    return points

# Function to generate Assembly source code
def generate_source_asm(label, points):
    """
    Generates 68000 Assembly source code for the sine table.

    Args:
        label (str): The label to use for the data table.
        points (list): The list of sine wave points.

    Returns:
        str: The generated Assembly code.
    """
    lines = []
    # Add the label
    lines.append(f"{label}:")
    
    current_line_parts = []
    # Iterate through points to format them for assembly output (dc.b)
    for i, p in enumerate(points):
        # Every 8 bytes, start a new line of data
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                lines.append(f"    dc.b {', '.join(current_line_parts)}")
                current_line_parts = []
        # Add the current point to the line buffer
        current_line_parts.append(str(p))
    
    # Add any remaining points in the buffer to the output
    if current_line_parts:
         lines.append(f"    dc.b {', '.join(current_line_parts)}")
    # Add the end label
    lines.append(f"end{label}:")
    
    # Join all lines and return
    return "\n".join(lines) + "\n"

# Function to generate C source code
def generate_source_c(label, points):
    """
    Generates C source code for the sine table.

    Args:
        label (str): The variable name to use for the array.
        points (list): The list of sine wave points.

    Returns:
        str: The generated C code.
    """
    lines = []
    # Start the C array definition
    lines.append(f"signed char {label}[] = {{")
    
    current_line_parts = []
    # Iterate through points to format them for C array
    for i, p in enumerate(points):
        # Break lines every 8 elements for readability
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                lines.append(f"    {', '.join(current_line_parts)},")
                current_line_parts = []
        # Add the current point to the line buffer
        current_line_parts.append(str(p))
    
    # Add any remaining points
    if current_line_parts:
         lines.append(f"    {', '.join(current_line_parts)}")

    # Close the C array
    lines.append(f"}};")
    return "\n".join(lines) + "\n"

# Function to generate Blitz Basic source code
def generate_source_blitz(label, points):
    """
    Generates Blitz Basic source code for the sine table.

    Args:
        label (str): The label to use for the data statement.
        points (list): The list of sine wave points.

    Returns:
        str: The generated Blitz Basic code.
    """
    lines = []
    # Example blitz load 
    lines.append(f"Dim List Sintab.w({len(points)})\n")
    lines.append(f"Restore {label}\nFor i = 0 To {len(points)}\n\tRead Sintab(i)\n\tNPrint Sintab(i)\nNext\n")

    # Blitz data tag
    lines.append(f"{label}:")
    
    current_line_parts = []
    # Iterate through points
    for i, p in enumerate(points):
        # Break lines every 8 elements
        if i > 0 and i % 8 == 0:
            if current_line_parts:
                # Use Data.b for byte data
                lines.append(f"    Data.b {', '.join(current_line_parts)}")
                current_line_parts = []
        current_line_parts.append(str(p))
    
    # Add remaining points
    if current_line_parts:
         lines.append(f"    Data.b {', '.join(current_line_parts)}")

    return "\n".join(lines) + "\n"

# Dispatcher function to generate source based on format
def generate_source(label, points, fmt="asm"):
    """
    Dispatches generation to the correct function based on format.

    Args:
        label (str): The label/name for the dataset.
        points (list): The data points.
        fmt (str, optional): The format ('asm', 'c', 'blitz'). Defaults to "asm".

    Returns:
        str: The generated source code.
    """
    if fmt == "c":
        return generate_source_c(label, points)
    elif fmt == "blitz":
        return generate_source_blitz(label, points)
    else:
        return generate_source_asm(label, points)

# Wrapper to calculate points and then generate source code
def generate_sine_table(label, n_points, amplitude, mod_amp=0, mod_freq=1, period_mode="full", fmt="asm", offset=0):
    """
    High-level function to generate the complete sine table source code.

    Args:
        label (str): The label for the data.
        n_points (int): Number of points.
        amplitude (int): Amplitude of the wave.
        mod_amp (int, optional): Modulation amplitude.
        mod_freq (int, optional): Modulation frequency.
        period_mode (str, optional): Period mode.
        fmt (str, optional): Output format.
        offset (int, optional): Offset to shift wave center.

    Returns:
        str: The complete generated source code.
    """
    # First, calculate the raw data points
    points = calculate_points(n_points, amplitude, mod_amp, mod_freq, period_mode, offset)
    # Then generate and return the formatted source code
    return generate_source(label, points, fmt)

# --- GUI ---

class SineApp:
    """
    The main application class for the Tkinter GUI.
    Handles window creation, widget layout, and event processing.
    """
    def __init__(self, root, args):
        """
        Initialize the SineApp.

        Args:
            root (tk.Tk): The root Tkinter window.
            args (argparse.Namespace): Command line arguments used for defaults.
        """
        self.root = root
        # Set window title and size
        self.root.title("Amiga Sine Table Generator")
        self.root.geometry("600x835")
        
        # Try to set the window icon
        try:
            icon = tk.PhotoImage(file="amiga_icon.png")
            self.root.iconphoto(False, icon)
        except Exception:
            pass # Icon not found or invalid, just ignore
        
        # --- Initialize Variables ---
        # These variables are bound to UI widgets
        self.label_var = tk.StringVar(value=args.label)
        self.points_var = tk.IntVar(value=args.points)
        self.amplitude_var = tk.IntVar(value=args.amplitude)
        self.format_var = tk.StringVar(value=args.format)
        
        # --- Advanced Variables ---
        self.mod_amp_var = tk.IntVar(value=args.mod_amp)
        self.mod_freq_var = tk.IntVar(value=args.mod_freq)
        
        # --- Offset Variable ---
        self.offset_var = tk.IntVar(value=args.offset)
        
        # --- Map command line args to GUI period string ---
        p_val = "Full (360°)"
        if args.period == "half": p_val = "Half (Positive)"
        elif args.period == "neg_half": p_val = "Half (Negative)"
        
        self.period_var = tk.StringVar(value=p_val)
        
        # Create the UI layout
        self.create_widgets()
        # Perform initial calculation and update
        self.update_all()

    def create_widgets(self):
        """
        Creates and arranges all widgets in the main window.
        """
        # --- Primary Wave Settings Frame ---
        # LabelFrame groups related controls visually
        primary_frame = ttk.LabelFrame(self.root, text="Primary Wave", padding="10")
        primary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 0: Label Entry
        ttk.Label(primary_frame, text="Label:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(primary_frame, textvariable=self.label_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Row 1: Points Slider
        ttk.Label(primary_frame, text="Points:").grid(row=1, column=0, sticky=tk.W)
        # Scale widget for dragging a slider
        self.points_slider = ttk.Scale(primary_frame, from_=0, to=255, variable=self.points_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.points_slider.grid(row=1, column=1, sticky=tk.EW, padx=5)
        # Label to show the numeric value of the slider
        self.points_label = ttk.Label(primary_frame, text=str(self.points_var.get()))
        self.points_label.grid(row=1, column=2, sticky=tk.W)
        
        # Row 2: Amplitude Slider
        ttk.Label(primary_frame, text="Amplitude:").grid(row=2, column=0, sticky=tk.W)
        self.amplitude_slider = ttk.Scale(primary_frame, from_=0, to=255, variable=self.amplitude_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.amplitude_slider.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.amplitude_label = ttk.Label(primary_frame, text=str(self.amplitude_var.get()))
        self.amplitude_label.grid(row=2, column=2, sticky=tk.W)

        # Row 3: Output Format Combobox
        ttk.Label(primary_frame, text="Format:").grid(row=3, column=0, sticky=tk.W)
        self.format_combo = ttk.Combobox(primary_frame, textvariable=self.format_var, values=["asm", "c", "blitz"], state="readonly")
        self.format_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        # Bind event to update when selection changes
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self.update_all())
        
        # Row 4: Period Combobox
        ttk.Label(primary_frame, text="Period:").grid(row=4, column=0, sticky=tk.W)
        self.period_combo = ttk.Combobox(primary_frame, textvariable=self.period_var, values=["Full (360°)", "Half (Positive)", "Half (Negative)"], state="readonly")
        self.period_combo.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.period_combo.bind("<<ComboboxSelected>>", lambda e: self.update_all())
        
        # Row 5: Offset Slider
        ttk.Label(primary_frame, text="Offset:").grid(row=5, column=0, sticky=tk.W)
        self.offset_slider = ttk.Scale(primary_frame, from_=-128, to=127, variable=self.offset_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.offset_slider.grid(row=5, column=1, sticky=tk.EW, padx=5)
        self.offset_label = ttk.Label(primary_frame, text=str(self.offset_var.get()))
        self.offset_label.grid(row=5, column=2, sticky=tk.W)

        # Allow the middle column to expand
        primary_frame.columnconfigure(1, weight=1)
        
        # --- Modulation Settings Frame ---
        mod_frame = ttk.LabelFrame(self.root, text="Modulation (Add Second Sine)", padding="10")
        mod_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 0: Modulation Amplitude Slider
        ttk.Label(mod_frame, text="Mod Amp:").grid(row=0, column=0, sticky=tk.W)
        self.mod_amp_slider = ttk.Scale(mod_frame, from_=0, to=128, variable=self.mod_amp_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.mod_amp_slider.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.mod_amp_label = ttk.Label(mod_frame, text=str(self.mod_amp_var.get()))
        self.mod_amp_label.grid(row=0, column=2, sticky=tk.W)
        
        # Row 1: Modulation Frequency Multiplier Slider
        ttk.Label(mod_frame, text="Mod Freq:").grid(row=1, column=0, sticky=tk.W)
        self.mod_freq_slider = ttk.Scale(mod_frame, from_=1, to=10, variable=self.mod_freq_var, orient=tk.HORIZONTAL, command=self.on_change)
        self.mod_freq_slider.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.mod_freq_label = ttk.Label(mod_frame, text=str(self.mod_freq_var.get()))
        self.mod_freq_label.grid(row=1, column=2, sticky=tk.W)
        
        mod_frame.columnconfigure(1, weight=1)

        # Execution Time Information
        info_frame = ttk.Frame(self.root, padding="5")
        info_frame.pack(fill=tk.X, padx=10)
        self.time_label = ttk.Label(info_frame, text="")
        self.time_label.pack(anchor=tk.W)

        # Buttons (Pack first to ensure visibility at bottom)
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.save_btn = ttk.Button(btn_frame, text="Save file", command=self.save_file)
        self.save_btn.pack(side=tk.RIGHT)

        # --- Visualization Plot Frame ---
        plot_frame = ttk.LabelFrame(self.root, text="Visualization", padding="10")
        plot_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Canvas for drawing the sine wave graph
        self.canvas = tk.Canvas(plot_frame, bg="#2b2b2b", height=200)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Generated Code Output Frame ---
        output_frame = ttk.LabelFrame(self.root, text="Generated Code", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Text area to display the generated code
        self.text_area = tk.Text(output_frame, height=10, width=50)
        self.text_area.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar for the text area
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_area['yscrollcommand'] = scrollbar.set
        
        # Add trace listener to the label variable to trigger updates when the user types
        self.label_var.trace_add("write", lambda *args: self.update_all())

    def on_change(self, *args):
        """
        Callback for when any slider value changes.
        Updates labels and triggers a recalculation.
        """
        # Update the numeric labels next to sliders
        self.points_label.config(text=str(self.points_var.get()))
        self.amplitude_label.config(text=str(self.amplitude_var.get()))
        self.mod_amp_label.config(text=str(self.mod_amp_var.get()))
        self.mod_freq_label.config(text=str(self.mod_freq_var.get()))
        self.offset_label.config(text=str(self.offset_var.get()))
        # Trigger full update
        self.update_all()

    def update_all(self):
        """
        Recalculates points, updates the generated code, and redraws the plot.
        Called whenever any parameter changes.
        """
        try:
            # Get values from UI variables
            points_count = self.points_var.get()
            amplitude = self.amplitude_var.get()
            label = self.label_var.get()
            fmt = self.format_var.get()
            
            mod_amp = self.mod_amp_var.get()
            mod_freq = self.mod_freq_var.get()
            
            # Determine period mode from dropdown string
            p_gui = self.period_var.get()
            period_mode = "full"
            if "Positive" in p_gui: period_mode = "half"
            elif "Negative" in p_gui: period_mode = "neg_half"
            
            # Get offset value
            offset = self.offset_var.get()
            
            # Handle empty points case to avoid errors
            if points_count == 0:
                self.text_area.delete(1.0, tk.END)
                self.canvas.delete("all")
                return

            # Calculate the points
            points = calculate_points(points_count, amplitude, mod_amp, mod_freq, period_mode, offset)
            
            # Generate the source code
            code = generate_source(label, points, fmt)
            # Update the text area with new code
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, code)
            
            # Redraw the visualization plot
            self.draw_plot(points, amplitude, period_mode)
            
            # Update estimated execution time strings (just for reference)
            time_50hz = points_count * 0.02
            time_60hz = points_count * (1/60)
            self.time_label.config(text=f"{time_50hz:.4f} seconds at 50hz, {time_60hz:.4f} seconds at 60hz")

            # Update the Save Button text to show filename extension
            ext = ".s"
            if fmt == "c": ext = ".c"
            if fmt == "blitz": ext = ".bb"
            self.save_btn.config(text=f"Save {label}{ext}")
            
        except Exception as e:
            # Silently ignore errors during update (e.g. typing incomplete numbers)
            pass

    def draw_plot(self, points, amplitude, period_mode="full"):
        """
        Draws the visualization of the sine wave on the canvas.

        Args:
            points (list): The list of sine values.
            amplitude (int): The amplitude (used for scaling/reference).
            period_mode (str): The period mode to adjust visualization.
        """
        # Clear the canvas
        self.canvas.delete("all")
        # Get current canvas dimensions
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # If canvas isn't drawn yet (first run), use default size estimate
        if w < 10: w = 550
        if h < 10: h = 200

        if not points:
            return

        # Calculate scales and baseline based on period mode
        x_step = w / len(points)
        padding = 10  # Pixels padding from top/bottom edges
        
        # All modes use sign = +1 for Amiga screen coords:
        # Negative values go UP (smaller y/vpos), positive values go DOWN (larger y/vpos)
        sign = 1
        
        if period_mode == "half":
            # Half-positive: values 0-255, baseline at TOP
            # Zero line at top, positive values go DOWN (Amiga screen coords)
            baseline_y = padding
            y_scale = (h - 2 * padding) / 260  # 260 gives slight headroom for 255
            # Draw zero guideline at top
            self.canvas.create_line(0, baseline_y, w, baseline_y, fill="#555555", dash=(2, 4))
        elif period_mode == "neg_half":
            # Half-negative: values -255 to 0, baseline at BOTTOM
            # Zero line at bottom, negative values go UP (Amiga screen coords)
            baseline_y = h - padding
            y_scale = (h - 2 * padding) / 260
            # Draw zero guideline at bottom
            self.canvas.create_line(0, baseline_y, w, baseline_y, fill="#555555", dash=(2, 4))
        else:
            # Full wave: values -128 to 127, baseline at center
            # Positive goes UP, negative goes DOWN
            baseline_y = h / 2
            y_scale = (h / 2 - padding) / 130  # 130 gives slight headroom for ±128
            # Draw center guideline
            self.canvas.create_line(0, baseline_y, w, baseline_y, fill="#555555", dash=(2, 4))

        # Calculate first point position
        prev_x = 0
        prev_y = baseline_y + (sign * points[0] * y_scale)

        # Loop through points and draw lines connecting them
        for i in range(1, len(points)):
            x = i * x_step
            # Map value to y position
            y = baseline_y + (sign * points[i] * y_scale)
            
            # Draw line segment
            self.canvas.create_line(prev_x, prev_y, x, y, fill="#00ff00", width=2)
            # Draw point dot
            self.canvas.create_oval(x-2, y-2, x+2, y+2, fill="#ffff00", outline="")
            
            prev_x = x
            prev_y = y

    def save_file(self):
        """
        Opens a file dialog to save the generated code to a file.
        """
        # Determine file extension based on format
        fmt = self.format_var.get()
        ext = ".s"
        filetypes = [("Assembly Source", "*.s"), ("All Files", "*.*")]
        
        if fmt == "c": 
            ext = ".c"
            filetypes = [("C Source", "*.c"), ("All Files", "*.*")]
        elif fmt == "blitz":
            ext = ".bb"
            filetypes = [("Blitz Basic", "*.bb"), ("All Files", "*.*")]
            
        # Construct default filename
        filename = f"{self.label_var.get()}{ext}"
        # Open Save As dialog
        file_path = filedialog.asksaveasfilename(initialfile=filename, defaultextension=ext, filetypes=filetypes)
        
        # If user selected a file, write content
        if file_path:
            try:
                code = self.text_area.get(1.0, tk.END)
                with open(file_path, "w") as f:
                    f.write(code)
                messagebox.showinfo("Success", f"Saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

# --- Main Entry Point ---

def main():
    """
    Main function to parse arguments and launch the application or CLI mode.
    """
    # Set up argument parser for CLI usage
    parser = argparse.ArgumentParser(description="Sine Generator for 68000 Assembly")
    parser.add_argument("--label", default="sine", help="ASM label name (default: sine)")
    parser.add_argument("--points", type=int, default=50, help="Number of points (default: 50)")
    parser.add_argument("--amplitude", type=int, default=80, help="Amplitude (default: 80)")
    parser.add_argument("--output", help="Output file (optional)")
    parser.add_argument("--format", choices=["asm", "c", "blitz"], default="asm", help="Output format (asm, c, blitz). Default: asm")
    parser.add_argument("--mod-amp", type=int, default=0, help="Modulation amplitude (default: 0)")
    parser.add_argument("--mod-freq", type=int, default=1, help="Modulation frequency (default: 1)")
    parser.add_argument("--period", choices=["full", "half", "neg_half"], default="full", help="Period mode: full, half, neg_half. Default: full")
    parser.add_argument("--offset", type=int, default=0, help="Offset to shift wave center (default: 0)")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if CLI mode is requested
    if args.cli:
        # Generate code directly without GUI
        code = generate_sine_table(args.label, args.points, args.amplitude, args.mod_amp, args.mod_freq, args.period, args.format, args.offset)
        
        # Output to file or stdout
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
        # Launch GUI
        try:
            root = tk.Tk()
            app = SineApp(root, args)
            # Bind configure event to update plot when window resizes (only if canvas affected)
            root.bind("<Configure>", lambda e: app.update_all() if e.widget == app.canvas else None)
            root.mainloop()
        except Exception as e:
            print(f"GUI ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
