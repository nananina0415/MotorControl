#!/usr/bin/env python3
# Universal plotter for motor control experiments
# Reads "Data:Duty,Time,Velocity" format from Arduino

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
import sys

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
    print("Reading data from Arduino...")
except Exception as e:
    print(f"Error: Failed to connect to {PORT}")
    print(f"Details: {e}")
    sys.exit(1)

# --- Data storage ---
time_data = []
velocity_data = []
duty_data = []
tau_labels = []  # Store tau annotations: [(time, tau_value, duty, annotation_object)]
K_labels = []    # Store K annotations: [(time, K_value, duty, annotation_object)]
paused = False  # Flag to pause updating

# --- Setup plot ---
fig, ax = plt.subplots(figsize=(12, 6))
line_velocity, = ax.plot([], [], 'r-', linewidth=1.5, label='Velocity (deg/s)')
line_duty, = ax.plot([], [], 'b-', linewidth=1.0, alpha=0.7, label='Duty × 10')

ax.set_xlabel('Time (s)')
ax.set_ylabel('Angular Velocity (deg/s) / PWM Duty (×10)')
ax.set_title('Motor Speed Response (Press "c" to clear / "p" to pause)')
ax.legend(loc='upper left')
ax.grid(True)

def on_key(event):
    """Handle keyboard events"""
    global paused

    if event.key == 'c':
        time_data.clear()
        velocity_data.clear()
        duty_data.clear()
        # Remove all tau annotations
        for _, _, _, ann in tau_labels:
            ann.remove()
        tau_labels.clear()
        # Remove all K annotations
        for _, _, _, ann in K_labels:
            ann.remove()
        K_labels.clear()
        print("Data cleared")
    elif event.key == 'p':
        if not paused:
            paused = True
            print("\nPlotter paused. Close window to exit.")
            ax.set_title('Motor Speed Response - PAUSED (close window to exit)')
            #ser.close()
        else:
            print("Already paused")

fig.canvas.mpl_connect('key_press_event', on_key)

def update_plot(frame):
    """Read serial data and update plot"""
    # If paused, still read serial to prevent buffer overflow, but don't update plot
    if paused:
        # Clear buffer without processing
        while ser.in_waiting > 0:
            try:
                ser.readline()  # Just read and discard
            except:
                pass
        return line_velocity, line_duty

    # Read all available data
    while ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8', errors='ignore').strip()

            # Parse data format: "Data:Duty,Time,Velocity"
            if raw_data.startswith("Data:"):
                values = raw_data.split(":")[1].split(",")
                if len(values) == 3:
                    duty = int(values[0])
                    time_val = float(values[1])
                    velocity = float(values[2])

                    time_data.append(time_val)
                    velocity_data.append(velocity)
                    duty_data.append(duty * 10)  # Scale for visibility

            # Parse tau format: "Tau:Duty,Time,TauValue"
            elif raw_data.startswith("Tau:"):
                values = raw_data.split(":")[1].split(",")
                if len(values) == 3:
                    duty = int(values[0])
                    time_val = float(values[1])
                    tau_val = float(values[2])

                    # Add annotation at this time position
                    ann = ax.annotate(
                        f'τ={tau_val:.3f}s\n(d={duty})',
                        xy=(time_val, 0),
                        xytext=(time_val, -200),
                        fontsize=9,
                        ha='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='black')
                    )
                    tau_labels.append((time_val, tau_val, duty, ann))
                    print(f"Tau calculated: d={duty}, τ={tau_val:.3f}s at t={time_val:.3f}s")

            # Parse K format: "K:Duty,Time,K_value,SteadyVelocity"
            elif raw_data.startswith("K:"):
                values = raw_data.split(":")[1].split(",")
                if len(values) == 4:
                    duty = int(values[0])
                    time_val = float(values[1])
                    K_val = float(values[2])
                    steady_vel = float(values[3])

                    # Add annotation at this time position
                    ann = ax.annotate(
                        f'K={K_val:.3f}\n(d={duty})',
                        xy=(time_val, steady_vel),
                        xytext=(time_val, steady_vel + 200),
                        fontsize=9,
                        ha='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='black')
                    )
                    K_labels.append((time_val, K_val, duty, ann))
                    print(f"K calculated: d={duty}, K={K_val:.3f} (ω_ss={steady_vel:.1f} deg/s)")

            else:
                # Print status messages from Arduino
                print(raw_data)

        except (ValueError, IndexError) as e:
            continue

    # Update plot if we have data
    if len(time_data) > 0:
        line_velocity.set_data(time_data, velocity_data)
        line_duty.set_data(time_data, duty_data)

        # Auto-scale axes
        ax.set_xlim(0, max(time_data) + 0.5)

        all_values = velocity_data + duty_data
        if all_values:
            y_min = min(all_values) - 50
            y_max = max(all_values) + 50
            ax.set_ylim(y_min, y_max)

    return line_velocity, line_duty

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
