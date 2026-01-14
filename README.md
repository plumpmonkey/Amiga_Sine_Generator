# Sine Generator for 68000 Assembly

A Python-based tool to generate sine wave look-up tables (LUTs) for Motorola 68000 assembly projects. This is a port of the [original Rust implementation](https://github.com/rdoetjes/sine_generator) by rdoetjes, offering both a Command Line Interface (CLI) and a Graphical User Interface (GUI).

![Sine Generator GUI](screenshot.png)

## Overview

This tool calculates sine wave values and outputs them as `dc.b` (Define Constant Byte) directives, ready to be included in your Amiga or other 68k assembly source code. It handles:
-   **Amplitude scaling**: Adjust the height of the wave.
-   **Step count**: Define the resolution of the table (number of points per period).
-   **Visual preview**: Real-time graphical view of the waveform (GUI only).
-   **Execution time estimation**: Estimates the time per frame at 50Hz (PAL) and 60Hz (NTSC) based on the number of points.

## Installation

Ensure you have Python 3.x installed. The tool uses standard libraries and `tkinter` for the GUI, so no additional `pip install` commands are typically required.

## Usage

### Graphical User Interface (GUI)

To use the GUI (default):

```bash
python sine_gen.py
```

**Features:**
-   **ASM Label**: Set the label name for the table (e.g., `sine:`).
-   **Points**: Slider to adjust the number of steps (0-255).
-   **Amplitude**: Slider to adjust the magnitude (0-255).
-   **Visualization**: Green dots on a dark background show the waveform.
    -   *Note*: The visualization uses screen coordinates where positive values (down) correspond to increasing memory addresses/screen lines, matching typical copper list or sprite y-positioning logic.
-   **Real-time Code**: The generated assembly code updates instantly in the text box.
-   **Execution Time**: Displays the theoretical execution time for the given number of points at 50Hz and 60Hz.
-   **Save**: Export the code to a `.s` file.

### Command Line Interface (CLI)

To use the CLI for batch processing or scripting, add the `--cli` flag:

```bash
python sine_gen.py --cli [options]
```

**Arguments:**
-   `--cli`: **Required** to run in CLI mode.
-   `--label`: ASM label name (default: `sine`).
-   `--points`: Number of points (default: `64`).
-   `--amplitude`: Amplitude of the wave (default: `30`).
-   `--output`: Output filename (optional). If omitted, prints to stdout.

**Example:**
Generate a table with 128 points and amplitude of 50, saved to `wave.s`:
```bash
python sine_gen.py --cli --label wave --points 128 --amplitude 50 --output wave.s
```

## Output Format

The output is formatted for 68k assemblers (like VASM):

```asm
sine:
    dc.b 0, 3, 5, 8, 11, 13, 16, 18
    dc.b 20, 22, 24, 26, 27, 28, 29, 30
    ...
endsine:
```
