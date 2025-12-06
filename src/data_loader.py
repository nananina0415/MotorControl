#!/usr/bin/env python3
"""
Data Loader Utility

Provides functions to load the latest measurement data from data/ folder.
Used by Matlab (via Python bridge), Python simulations, and analysis scripts.

Usage:
    from data_loader import load_latest_summary, load_latest_raw_data

    # Load system parameters (tau, K)
    tau, K, metadata = load_latest_summary("1-3")

    # Load raw measurement data
    time, velocity, duty = load_latest_raw_data("1-3")
"""

import json
import csv
from pathlib import Path
from typing import Tuple, Dict, List, Optional


def load_latest_summary(task_name: str, verbose: bool = True) -> Tuple[float, float, Dict]:
    """
    Load the latest summary file from data/<task_name>/ folder.

    Args:
        task_name: Task identifier (e.g., "1-1", "1-2", "1-3", "2-1")
        verbose: Print loading information

    Returns:
        Tuple of (tau, K, metadata)
        - tau: Time constant (seconds)
        - K: DC gain (deg/s)/PWM
        - metadata: Full JSON data including std, timestamp, etc.

    Raises:
        FileNotFoundError: If no summary files found
        ValueError: If data is invalid or missing required fields

    Example:
        >>> tau, K, meta = load_latest_summary("1-3")
        >>> print(f"τ = {tau:.4f} s, K = {K:.4f}")
    """
    # Get project root (parent of src/)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}\n"
            f"Please run: python run.py {task_name}"
        )

    # Find all summary files
    summary_files = list(data_dir.glob("summary_*.json"))

    if not summary_files:
        raise FileNotFoundError(
            f"No summary files found in {data_dir}\n"
            f"Please run: python run.py {task_name}\n"
            f"Then press 'p' to save data"
        )

    # Get most recent file (by modification time)
    latest_file = max(summary_files, key=lambda p: p.stat().st_mtime)

    # Load JSON
    with open(latest_file, 'r') as f:
        data = json.load(f)

    # Extract required fields
    if 'tau_average' not in data or 'K_average' not in data:
        raise ValueError(
            f"Invalid summary file: {latest_file}\n"
            f"Missing required fields: tau_average or K_average"
        )

    tau = data['tau_average']
    K = data['K_average']

    if verbose:
        print(f"=== Auto-loaded from {latest_file.name} ===")
        print(f"Time constant τ = {tau:.4f} ± {data.get('tau_std', 0):.4f} s")
        print(f"DC gain K = {K:.4f} ± {data.get('K_std', 0):.4f} (deg/s)/PWM")
        print(f"Data points: {data.get('data_points', 'N/A')}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        print()

    return tau, K, data


def load_latest_raw_data(task_name: str, verbose: bool = True) -> Tuple[List[float], List[float], List[float]]:
    """
    Load the latest raw data CSV from data/<task_name>/ folder.

    Args:
        task_name: Task identifier (e.g., "1-1", "1-2", "1-3")
        verbose: Print loading information

    Returns:
        Tuple of (time, velocity, duty)
        - time: List of time values (seconds)
        - velocity: List of velocity values (deg/s)
        - duty: List of PWM duty cycle values

    Raises:
        FileNotFoundError: If no raw data files found

    Example:
        >>> time, vel, duty = load_latest_raw_data("1-3")
        >>> print(f"Loaded {len(time)} data points")
    """
    # Get project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}\n"
            f"Please run: python run.py {task_name}"
        )

    # Find all raw data files
    raw_files = list(data_dir.glob("raw_data_*.csv"))

    if not raw_files:
        raise FileNotFoundError(
            f"No raw data files found in {data_dir}\n"
            f"Please run: python run.py {task_name}\n"
            f"Then press 'p' to save data"
        )

    # Get most recent file
    latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)

    if verbose:
        print(f"=== Loading raw data from {latest_file.name} ===")

    # Load CSV
    time_data = []
    velocity_data = []
    duty_data = []

    with open(latest_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        for row in reader:
            if len(row) >= 3:
                time_data.append(float(row[0]))
                velocity_data.append(float(row[1]))
                duty_data.append(float(row[2]))

    if verbose:
        print(f"Loaded {len(time_data)} data points")
        print()

    return time_data, velocity_data, duty_data


def load_latest_pid_data(task_name: str, verbose: bool = True) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
    """
    Load the latest PID controller data from data/<task_name>/ folder.

    Args:
        task_name: Task identifier (e.g., "2-1")
        verbose: Print loading information

    Returns:
        Tuple of (time, position, reference, error, control)

    Raises:
        FileNotFoundError: If no PID data files found

    Example:
        >>> t, pos, ref, err, ctrl = load_latest_pid_data("2-1")
    """
    # Get project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}\n"
            f"Please run: python run.py {task_name}"
        )

    # Find all PID data files
    pid_files = list(data_dir.glob("pid_data_*.csv"))

    if not pid_files:
        raise FileNotFoundError(
            f"No PID data files found in {data_dir}\n"
            f"Please run: python run.py {task_name}\n"
            f"Then press 'p' to save data"
        )

    # Get most recent file
    latest_file = max(pid_files, key=lambda p: p.stat().st_mtime)

    if verbose:
        print(f"=== Loading PID data from {latest_file.name} ===")

    # Load CSV
    time_data = []
    position_data = []
    reference_data = []
    error_data = []
    control_data = []

    with open(latest_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        for row in reader:
            if len(row) >= 5:
                time_data.append(float(row[0]))
                position_data.append(float(row[1]))
                reference_data.append(float(row[2]))
                error_data.append(float(row[3]))
                control_data.append(float(row[4]))

    if verbose:
        print(f"Loaded {len(time_data)} data points")
        print()

    return time_data, position_data, reference_data, error_data, control_data


def list_all_summaries(task_name: str) -> List[Dict]:
    """
    List all summary files for a given task.

    Args:
        task_name: Task identifier

    Returns:
        List of dictionaries with file info and loaded data

    Example:
        >>> summaries = list_all_summaries("1-3")
        >>> for s in summaries:
        ...     print(f"{s['filename']}: τ={s['tau']:.3f}, K={s['K']:.3f}")
    """
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / task_name

    if not data_dir.exists():
        return []

    summary_files = list(data_dir.glob("summary_*.json"))
    results = []

    for file_path in summary_files:
        with open(file_path, 'r') as f:
            data = json.load(f)

        results.append({
            'filename': file_path.name,
            'path': str(file_path),
            'timestamp': data.get('timestamp', 'N/A'),
            'tau': data.get('tau_average', None),
            'K': data.get('K_average', None),
            'data_points': data.get('data_points', 0),
            'mtime': file_path.stat().st_mtime
        })

    # Sort by modification time (newest first)
    results.sort(key=lambda x: x['mtime'], reverse=True)

    return results


def get_task_data_dir(task_name: str) -> Path:
    """
    Get the data directory path for a given task.

    Args:
        task_name: Task identifier

    Returns:
        Path object for data/<task_name>/

    Example:
        >>> data_dir = get_task_data_dir("1-3")
        >>> print(data_dir)
        /path/to/MotorControl/data/1-3
    """
    project_root = Path(__file__).parent.parent
    return project_root / "data" / task_name


# For backward compatibility and convenience
def load_system_parameters(task_name: str = "1-3", verbose: bool = True) -> Tuple[float, float]:
    """
    Convenience function to load tau and K only.

    Args:
        task_name: Task identifier (default: "1-3")
        verbose: Print loading information

    Returns:
        Tuple of (tau, K)

    Example:
        >>> tau, K = load_system_parameters()
    """
    tau, K, _ = load_latest_summary(task_name, verbose)
    return tau, K


if __name__ == "__main__":
    # Test/demo code
    print("=" * 60)
    print("Data Loader Test")
    print("=" * 60)
    print()

    # Test 1: Load summary
    try:
        tau, K, meta = load_latest_summary("1-3")
        print(f"✓ Successfully loaded: τ={tau:.4f}, K={K:.4f}")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")

    print()

    # Test 2: List all summaries
    print("All available summaries for task 1-3:")
    summaries = list_all_summaries("1-3")
    for i, s in enumerate(summaries, 1):
        print(f"  {i}. {s['filename']}: τ={s['tau']:.4f}, K={s['K']:.4f}")

    print()
    print("=" * 60)
