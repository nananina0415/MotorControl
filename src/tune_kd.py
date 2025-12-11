#!/usr/bin/env python3
import serial
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Configuration
PORT = os.environ.get('COM_MEGA2560')
if not PORT:
    print("Error: COM_MEGA2560 not set")
    sys.exit(1)

BAUD = 115200

# Fixed Kp (Selected from previous step)
FIXED_KP = 50.0 

# Sweep Kd values
KD_VALUES = [0, 1, 3, 5, 8, 10, 15, 20, 25, 30, 40, 50]

TARGET_POS = 200
TEST_DURATION = 2.0

def calculate_metrics(time_data, pos_data, target):
    """Calculate Rise Time, Overshoot, and Steady-State Error"""
    if not pos_data or len(pos_data) < 10:
        return None, None, None
    
    t = np.array(time_data)
    y = np.array(pos_data)
    t = t - t[0]
    
    # 1. Rise Time (10% -> 90%)
    rt = None
    try:
        idx_low = np.where(y >= target * 0.1)[0][0]
        idx_high = np.where(y >= target * 0.9)[0][0]
        rt = t[idx_high] - t[idx_low]
    except IndexError:
        pass
        
    # 2. Overshoot (%)
    peak_val = np.max(y)
    overshoot = 0.0
    if peak_val > target:
        overshoot = (peak_val - target) / target * 100.0
        
    # 3. Steady-State Error (deg)
    num_samples = len(y)
    avg_final = np.mean(y[int(num_samples*0.9):])
    sse = target - avg_final
    
    return rt, overshoot, sse

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        print(f"Connected to {PORT}")
    except Exception as e:
        print(f"Connection error: {e}")
        return

    results = []
    all_responses = {}

    print(f"Starting Kd Tuning Sweep (Fixed Kp={FIXED_KP})...")
    
    for kd in KD_VALUES:
        print(f"\nTesting Kd = {kd}...")
        
        # 1. Reset
        ser.write(b"S\n")
        time.sleep(0.1)
        ser.write(b"Z\n")
        time.sleep(0.5)
        
        # 2. Set Gain (Kp Fixed, Kd Sweeping)
        cmd = f"G:{FIXED_KP},0,{kd}\n"
        ser.write(cmd.encode())
        time.sleep(0.1)
        
        # 3. Start Step
        ser.reset_input_buffer()
        ser.write(f"R:{TARGET_POS}\n".encode())
        
        # 4. Record Data
        start_time = time.time()
        t_data = []
        p_data = []
        
        while time.time() - start_time < TEST_DURATION:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode().strip()
                    if line.startswith("Data:"):
                        parts = line.split(":")[1].split(",")
                        t_data.append(float(parts[0]))
                        p_data.append(float(parts[1]))
                except:
                    continue
        
        # 5. Process
        rt, ov, sse = calculate_metrics(t_data, p_data, TARGET_POS)
        print(f"  -> Rise Time: {rt:.3f} s" if rt else "  -> Rise Time: N/A")
        print(f"  -> Overshoot: {ov:.1f} %")
        
        results.append({
            'Kd': kd, 
            'RiseTime': rt, 
            'Overshoot': ov, 
            'SSE': sse
        })
        if t_data:
            all_responses[kd] = (t_data, p_data)
            
        # 6. Return to 0
        ser.write(b"R:0\n")
        time.sleep(1.5)

    ser.write(b"S\n")
    ser.close()
    
    # --- Plotting ---
    if not results:
        print("No valid data collected.")
        return

    print("\nPlotting results...")
    # Use 3 subplots for Kd tuning (Focus on Overshoot)
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))
    
    # Plot 1: Step Responses
    ax1 = axes[0]
    for kd, (t, p) in all_responses.items():
        if len(t) > 0:
            t_norm = np.array(t) - t[0]
            ax1.plot(t_norm, p, label=f'Kd={kd}')
    
    ax1.axhline(TARGET_POS, color='k', linestyle='--', label='Target')
    ax1.set_title(f'Step Responses (Fixed Kp={FIXED_KP})')
    ax1.set_ylabel('Position (deg)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Kd vs Overshoot (Primary Metric)
    ax2 = axes[1]
    x_vals = [r['Kd'] for r in results]
    y_vals = [r['Overshoot'] for r in results]
    ax2.plot(x_vals, y_vals, 'o-', color='red')
    ax2.axhline(15, color='b', linestyle='--', label='Limit (15%)')
    ax2.set_title('Sensitivity: Kd vs Overshoot')
    ax2.set_ylabel('Overshoot (%)')
    ax2.legend()
    ax2.grid(True)

    # Plot 3: Kd vs Rise Time (Side Effect)
    ax3 = axes[2]
    y_vals = [r['RiseTime'] for r in results]
    ax3.plot(x_vals, y_vals, 'o-', color='purple')
    ax3.set_title('Sensitivity: Kd vs Rise Time')
    ax3.set_xlabel('Kd')
    ax3.set_ylabel('Rise Time (s)')
    ax3.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
