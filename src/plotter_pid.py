#!/usr/bin/env python3
# PID Controller Plotter for P#2-1
# Reads "Data:Time,Position,Reference,Error,ControlSignal" format from Arduino

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
import sys
from datetime import datetime
from pathlib import Path
import csv
import json

# --- Configuration ---
PORT = os.environ.get('COM_MEGA2560')
if not PORT:
    print("Error: COM_MEGA2560 environment variable not set.")
    print("\nPlease set it using:")
    print("  PowerShell: $env:COM_MEGA2560=\"COM4\"")
    print("  CMD:        set COM_MEGA2560=COM4")
    print("  Linux/Mac:  export COM_MEGA2560=/dev/ttyUSB0")
    sys.exit(1)

BAUD_RATE = 115200

# --- Connect to Arduino ---
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    ser.reset_input_buffer()
    print(f"Connected to {PORT}")
    print("Reading PID data from Arduino...")
except Exception as e:
    print(f"Error: Failed to connect to {PORT}")
    print(f"Details: {e}")
    sys.exit(1)

# --- Data storage ---
time_data = []
position_data = []
reference_data = []
error_data = []
control_data = []
paused = False
task_name = None

# --- Setup plot ---
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Position plot
ax1 = axes[0]
line_position, = ax1.plot([], [], 'b-', linewidth=2, label='Position')
line_reference, = ax1.plot([], [], 'r--', linewidth=1.5, label='Reference')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Position (deg)')
ax1.set_title('PID Position Control (Press "c" to clear / "p" to pause & save)')
ax1.legend(loc='upper right')
ax1.grid(True)

# Error plot
ax2 = axes[1]
line_error, = ax2.plot([], [], 'r-', linewidth=1.5)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Error (deg)')
ax2.set_title('Tracking Error')
ax2.grid(True)

# Control signal plot
ax3 = axes[2]
line_control, = ax3.plot([], [], 'g-', linewidth=1.5)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Control Signal (PWM)')
ax3.set_title('PID Output')
ax3.grid(True)

plt.tight_layout()

# --- Save functions ---
def save_plot(save_task):
    """Save current plot as image"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / save_task
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save plot
    filename = data_dir / f"pid_response_{timestamp}.png"
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved: {filename}")

    return filename

def save_raw_data(save_task, time_vals, pos_vals, ref_vals, err_vals, ctrl_vals):
    """Save PID data to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / save_task
    data_dir.mkdir(parents=True, exist_ok=True)

    filename = data_dir / f"pid_data_{timestamp}.csv"

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time(s)', 'Position(deg)', 'Reference(deg)', 'Error(deg)', 'Control(PWM)'])

        for t, pos, ref, err, ctrl in zip(time_vals, pos_vals, ref_vals, err_vals, ctrl_vals):
            writer.writerow([t, pos, ref, err, ctrl])

    print(f"Raw data saved: {filename}")
    return filename

def save_performance_metrics(save_task, time_vals, pos_vals, ref_vals):
    """Calculate and save performance metrics"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / save_task
    data_dir.mkdir(parents=True, exist_ok=True)

    if len(pos_vals) < 10:
        print("Not enough data for performance calculation")
        return

    # Calculate metrics
    reference = ref_vals[-1] if ref_vals else 0
    final_position = pos_vals[-1]
    steady_state_error = reference - final_position

    # Find peak overshoot
    peak_position = max(pos_vals)
    overshoot = ((peak_position - reference) / reference * 100) if reference > 0 else 0

    # Find settling time (2% criterion)
    settling_threshold = 0.02 * reference
    settling_time = None
    for i in range(len(pos_vals) - 1, 0, -1):
        if abs(pos_vals[i] - reference) > settling_threshold:
            if i < len(time_vals) - 1:
                settling_time = time_vals[i + 1]
            break

    # Find rise time (10% to 90%)
    threshold_10 = 0.1 * reference
    threshold_90 = 0.9 * reference
    rise_start = None
    rise_end = None

    for i, pos in enumerate(pos_vals):
        if rise_start is None and pos >= threshold_10:
            rise_start = time_vals[i]
        if rise_end is None and pos >= threshold_90:
            rise_end = time_vals[i]
            break

    rise_time = (rise_end - rise_start) if (rise_start and rise_end) else None

    # Save metrics
    metrics = {
        'timestamp': timestamp,
        'task': save_task,
        'reference': reference,
        'final_position': final_position,
        'steady_state_error': steady_state_error,
        'overshoot_percent': overshoot,
        'settling_time': settling_time,
        'rise_time': rise_time,
        'peak_position': peak_position,
        'data_points': len(time_vals)
    }

    filename = data_dir / f"pid_metrics_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"Performance metrics saved: {filename}")
    print(f"  Overshoot: {overshoot:.2f}%")
    print(f"  Settling time: {settling_time:.3f} s" if settling_time else "  Settling time: N/A")
    print(f"  Steady-state error: {steady_state_error:.4f} deg")

    return filename

def on_key(event):
    """Handle keyboard events"""
    global paused

    if event.key == 'c':
        time_data.clear()
        position_data.clear()
        reference_data.clear()
        error_data.clear()
        control_data.clear()
        print("Data cleared")

    elif event.key == 'p':
        if not paused:
            paused = True
            print("\n=== Plotter paused ===")

            # Determine task name
            if task_name is None:
                print("Warning: Task name not detected. Using 'unknown'")
                save_task = "unknown"
            else:
                save_task = task_name

            # Save all data
            print("\nSaving data...")

            # 1. Save plot image
            plot_file = save_plot(save_task)

            # 2. Save raw data
            if time_data:
                raw_file = save_raw_data(save_task, time_data, position_data,
                                         reference_data, error_data, control_data)
                # 3. Calculate and save performance metrics
                metrics_file = save_performance_metrics(save_task, time_data,
                                                        position_data, reference_data)
            else:
                print("No data to save")

            print("\n=== All data saved successfully ===")
            print("Close window to exit.")

            ax1.set_title('PID Position Control - PAUSED & SAVED (close window to exit)')
        else:
            print("Already paused")

fig.canvas.mpl_connect('key_press_event', on_key)

def update_plot(frame):
    """Read serial data and update plot"""
    global task_name

    # If paused, clear buffer but don't update
    if paused:
        while ser.in_waiting > 0:
            try:
                ser.readline()
            except:
                pass
        return line_position, line_reference, line_error, line_control

    # Read all available data
    while ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8', errors='ignore').strip()

            # Parse task identifier
            if raw_data.startswith("TASK:"):
                task_name = raw_data.split(":")[1]
                print(f"Task detected: {task_name}")

            # Parse data format: "Data:Time,Position,Reference,Error,ControlSignal"
            elif raw_data.startswith("Data:"):
                values = raw_data.split(":")[1].split(",")
                if len(values) == 5:
                    time_val = float(values[0])
                    position = float(values[1])
                    reference = float(values[2])
                    error = float(values[3])
                    control = float(values[4])

                    time_data.append(time_val)
                    position_data.append(position)
                    reference_data.append(reference)
                    error_data.append(error)
                    control_data.append(control)

            else:
                # Print status messages
                print(raw_data)

        except (ValueError, IndexError) as e:
            continue

    # Update plot
    if len(time_data) > 0:
        # Position plot
        line_position.set_data(time_data, position_data)
        line_reference.set_data(time_data, reference_data)

        ax1.set_xlim(0, max(time_data) + 0.1)
        pos_min = min(min(position_data), min(reference_data)) - 10
        pos_max = max(max(position_data), max(reference_data)) + 10
        ax1.set_ylim(pos_min, pos_max)

        # Error plot
        line_error.set_data(time_data, error_data)
        ax2.set_xlim(0, max(time_data) + 0.1)
        if error_data:
            err_min = min(error_data) - 5
            err_max = max(error_data) + 5
            ax2.set_ylim(err_min, err_max)

        # Control plot
        line_control.set_data(time_data, control_data)
        ax3.set_xlim(0, max(time_data) + 0.1)
        if control_data:
            ctrl_min = min(control_data) - 10
            ctrl_max = max(control_data) + 10
            ax3.set_ylim(ctrl_min, ctrl_max)

    return line_position, line_reference, line_error, line_control

# --- Animation ---
ani = FuncAnimation(fig, update_plot, interval=20, blit=False, cache_frame_data=False)

try:
    plt.show()
except KeyboardInterrupt:
    print("\nPlotter stopped by user")
finally:
    if not paused:
        ser.close()
    print("Serial connection closed")
