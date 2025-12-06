#!/usr/bin/env python3
"""
P#2-1: PID Controller Simulation (Python Implementation)

This script simulates the same PID controller designed in p2-1_pid_design.m
but using Python with control systems library.

Features:
- Auto-loads system parameters (tau, K) from data/1-3/
- Simulates PID controller response
- Optimizes PID gains using scipy.optimize
- Visualizes step response and performance metrics
- Exports results compatible with Matlab analysis

Requirements:
- pip install numpy scipy matplotlib control
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from pathlib import Path
import json

try:
    import control as ct
    HAS_CONTROL = True
except ImportError:
    print("Warning: 'control' library not found. Install with: pip install control")
    HAS_CONTROL = False


class PIDController:
    """PID Controller with anti-windup and filtering"""

    def __init__(self, Kp, Ki, Kd, dt=0.01):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt

        # State
        self.error_integral = 0.0
        self.error_prev = 0.0
        self.derivative_filtered = 0.0

        # Anti-windup
        self.integral_max = 100.0
        self.integral_min = -100.0

        # Derivative filter (low-pass)
        self.alpha = 0.2  # Filter coefficient

    def reset(self):
        """Reset controller state"""
        self.error_integral = 0.0
        self.error_prev = 0.0
        self.derivative_filtered = 0.0

    def update(self, error):
        """Compute PID output for given error"""
        # Proportional
        P = self.Kp * error

        # Integral (with anti-windup)
        self.error_integral += error * self.dt
        self.error_integral = np.clip(self.error_integral, self.integral_min, self.integral_max)
        I = self.Ki * self.error_integral

        # Derivative (with low-pass filter)
        derivative_raw = (error - self.error_prev) / self.dt
        self.derivative_filtered = self.alpha * derivative_raw + (1 - self.alpha) * self.derivative_filtered
        D = self.Kd * self.derivative_filtered

        # Update previous error
        self.error_prev = error

        # PID output
        control = P + I + D

        return control, (P, I, D)


def load_system_parameters():
    """Load tau and K from data/1-3/summary_*.json"""
    try:
        from data_loader import load_system_parameters as load_params
        return load_params("1-3", verbose=True)
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Using placeholder values.")
        return 0.4, 12.4  # Placeholder values


def simulate_pid_response(Kp, Ki, Kd, tau, K, reference=200, t_max=2.0, dt=0.001):
    """
    Simulate closed-loop PID response

    Args:
        Kp, Ki, Kd: PID gains
        tau: System time constant (s)
        K: System DC gain (deg/s)/PWM
        reference: Target position (degrees)
        t_max: Simulation duration (s)
        dt: Time step (s)

    Returns:
        t: Time array
        position: Position response
        error: Tracking error
        control: Control signal
    """
    # Time array
    t = np.arange(0, t_max, dt)
    N = len(t)

    # Initialize arrays
    position = np.zeros(N)
    velocity = np.zeros(N)
    error = np.zeros(N)
    control = np.zeros(N)

    # PID controller
    pid = PIDController(Kp, Ki, Kd, dt)

    # Simulate
    for i in range(1, N):
        # Error
        error[i] = reference - position[i-1]

        # PID control
        u, _ = pid.update(error[i])
        control[i] = u

        # Motor dynamics: dω/dt = (K*u - ω) / tau
        # Position: θ = integral of ω
        dv = (K * control[i] - velocity[i-1]) / tau
        velocity[i] = velocity[i-1] + dv * dt
        position[i] = position[i-1] + velocity[i] * dt

    return t, position, error, control


def calculate_performance(t, position, reference):
    """Calculate step response performance metrics"""
    # Normalize to unit step
    y_norm = position / reference

    # Find settling time (2% criterion)
    settling_threshold = 0.02
    settled = np.abs(y_norm - 1.0) < settling_threshold
    if np.any(settled):
        settling_idx = np.where(settled)[0][0]
        settling_time = t[settling_idx]
    else:
        settling_time = t[-1]

    # Find overshoot
    peak_value = np.max(y_norm)
    overshoot = (peak_value - 1.0) * 100  # Percentage

    # Steady-state error
    ess = reference - position[-1]

    # Rise time (10% to 90%)
    idx_10 = np.where(y_norm >= 0.1)[0]
    idx_90 = np.where(y_norm >= 0.9)[0]
    if len(idx_10) > 0 and len(idx_90) > 0:
        rise_time = t[idx_90[0]] - t[idx_10[0]]
    else:
        rise_time = np.nan

    return {
        'overshoot': overshoot,
        'settling_time': settling_time,
        'steady_state_error': ess,
        'rise_time': rise_time,
        'peak_value': peak_value * reference
    }


def pid_objective(gains, tau, K, Mp_max=0.15, ts_max=0.5):
    """
    Objective function for PID optimization

    Penalizes:
    - Overshoot > 15%
    - Settling time > 0.5s
    - Steady-state error
    - Large gains (control effort)
    - Large Kd (noise sensitivity)
    """
    Kp, Ki, Kd = gains

    # Check bounds
    if Kp < 0 or Ki < 0 or Kd < 0:
        return 1e10

    # Simulate
    try:
        t, pos, err, ctrl = simulate_pid_response(Kp, Ki, Kd, tau, K, reference=1.0, t_max=2.0)
    except:
        return 1e10

    # Performance metrics
    metrics = calculate_performance(t, pos, 1.0)

    overshoot = metrics['overshoot'] / 100  # Convert to fraction
    ts = metrics['settling_time']
    ess = abs(metrics['steady_state_error'])

    # Cost function
    cost = 0.0

    # Overshoot penalty
    cost += max(0, overshoot - Mp_max)**2 * 1000

    # Settling time penalty
    cost += max(0, ts - ts_max)**2 * 100

    # Steady-state error penalty
    cost += ess**2 * 500

    # Control effort penalty (prefer smaller gains)
    cost += (Kp**2 + Ki**2 + Kd**2) * 0.01

    # Noise sensitivity penalty (penalize large Kd)
    cost += max(0, Kd - 10)**2 * 10

    return cost


def optimize_pid_gains(tau, K):
    """Optimize PID gains using scipy.optimize"""
    print("=== PID Gain Optimization ===")

    # Design specifications
    Mp_max = 0.15  # 15% overshoot
    ts_max = 0.5   # 0.5s settling time

    # Calculate initial guess
    zeta_design = 0.6
    wn_min = 4.6 / (zeta_design * ts_max)

    Kp_init = 0.5 * wn_min**2 * tau / K
    Ki_init = 0.3 * wn_min**2 / K
    Kd_init = 0.5 * wn_min * tau / K

    print(f"Initial guess: Kp={Kp_init:.3f}, Ki={Ki_init:.3f}, Kd={Kd_init:.3f}")

    # Optimize
    result = minimize(
        lambda x: pid_objective(x, tau, K, Mp_max, ts_max),
        x0=[Kp_init, Ki_init, Kd_init],
        method='L-BFGS-B',
        bounds=[(0, 100), (0, 100), (0, 20)],
        options={'maxiter': 100, 'disp': True}
    )

    Kp_opt, Ki_opt, Kd_opt = result.x

    print(f"\n=== Optimized PID Gains ===")
    print(f"Kp = {Kp_opt:.3f}")
    print(f"Ki = {Ki_opt:.3f}")
    print(f"Kd = {Kd_opt:.3f}")
    print()

    return Kp_opt, Ki_opt, Kd_opt


def plot_step_response(t, position, reference, error, control, Kp, Ki, Kd, metrics):
    """Plot step response and performance"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Position response
    ax1 = axes[0]
    ax1.plot(t, position, 'b-', linewidth=2, label='Position')
    ax1.axhline(reference, color='r', linestyle='--', linewidth=1.5, label='Reference')
    ax1.axhline(reference * 1.15, color='g', linestyle='--', linewidth=1, label='+15% overshoot limit')
    ax1.axhline(reference * 0.98, color='k', linestyle=':', linewidth=0.5, label='±2% settling band')
    ax1.axhline(reference * 1.02, color='k', linestyle=':', linewidth=0.5)
    ax1.axvline(0.5, color='m', linestyle='--', linewidth=1, label='ts = 0.5s limit')
    ax1.grid(True)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Position (deg)')
    ax1.set_title(f'Step Response for R={reference:.0f} (Kp={Kp:.2f}, Ki={Ki:.2f}, Kd={Kd:.2f})')
    ax1.legend(loc='best')

    # Error
    ax2 = axes[1]
    ax2.plot(t, error, 'r-', linewidth=1.5)
    ax2.grid(True)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Error (deg)')
    ax2.set_title('Tracking Error')

    # Control signal
    ax3 = axes[2]
    ax3.plot(t, control, 'g-', linewidth=1.5)
    ax3.grid(True)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Control Signal (PWM)')
    ax3.set_title('Control Signal')

    plt.tight_layout()

    # Add text with metrics
    textstr = f"Overshoot: {metrics['overshoot']:.2f}% (spec: < 15%)\n"
    textstr += f"Settling time: {metrics['settling_time']:.3f} s (spec: < 0.5s)\n"
    textstr += f"Steady-state error: {metrics['steady_state_error']:.4f} deg\n"
    textstr += f"Rise time: {metrics['rise_time']:.3f} s"

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.65, 0.05, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='bottom', bbox=props)

    return fig


def main():
    """Main simulation script"""
    print("=" * 60)
    print("P#2-1: PID Controller Design (Python Implementation)")
    print("=" * 60)
    print()

    # Load system parameters
    tau, K = load_system_parameters()

    print("=== System Parameters ===")
    print(f"Time constant τ = {tau:.3f} s")
    print(f"DC gain K = {K:.3f} (deg/s)/PWM")
    print()

    # Optimize PID gains
    Kp, Ki, Kd = optimize_pid_gains(tau, K)

    # Simulate with optimized gains
    print("=== Simulating Step Response ===")
    reference = 200
    t, pos, err, ctrl = simulate_pid_response(Kp, Ki, Kd, tau, K, reference=reference)

    # Calculate metrics
    metrics = calculate_performance(t, pos, reference)

    print(f"Overshoot: {metrics['overshoot']:.2f}% (spec: < 15%)")
    print(f"Settling time: {metrics['settling_time']:.3f} s (spec: < 0.5s)")
    print(f"Steady-state error: {metrics['steady_state_error']:.4f} deg (spec: = 0)")
    print(f"Rise time: {metrics['rise_time']:.3f} s")
    print()

    # Check specifications
    specs_met = (metrics['overshoot'] < 15 and
                 metrics['settling_time'] <= 0.5 and
                 abs(metrics['steady_state_error']) < 0.01 * reference)

    if specs_met:
        print("✓ All specifications MET!")
    else:
        print("✗ Specifications NOT MET. Adjust gains.")
    print()

    # Plot
    fig = plot_step_response(t, pos, reference, err, ctrl, Kp, Ki, Kd, metrics)

    # Save results
    results = {
        'tau': tau,
        'K': K,
        'Kp': Kp,
        'Ki': Ki,
        'Kd': Kd,
        'overshoot': metrics['overshoot'],
        'settling_time': metrics['settling_time'],
        'steady_state_error': metrics['steady_state_error'],
        'rise_time': metrics['rise_time']
    }

    results_file = Path("p2-1_python_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {results_file}")

    # Save figure
    fig_file = Path("p2-1_python_response.png")
    fig.savefig(fig_file, dpi=300, bbox_inches='tight')
    print(f"Figure saved to {fig_file}")

    plt.show()


if __name__ == "__main__":
    main()
