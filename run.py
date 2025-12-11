#!/usr/bin/env python3
"""
Arduino Upload Script
Usage: python run.py <n-m>
       python run.py stop
Example: python run.py 1-1     (uploads code/p1-1.cpp)
         python run.py 1-2     (uploads code/p1-2.cpp)
         python run.py stop    (uploads code/stop.cpp)
"""

import sys
import os
import shutil
import subprocess
import time
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def kill_plotter():
    """Kill any running plotter.py process"""
    if not HAS_PSUTIL:
        print("  → Skipping (psutil not installed)")
        print("  → Please close plotter manually if it's running")
        return False

    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('plotter.py' in str(arg) for arg in cmdline):
                print(f"  → Found running plotter (PID: {proc.info['pid']})")
                proc.kill()
                proc.wait(timeout=3)
                print("  → Plotter terminated")
                killed = True
                time.sleep(0.5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

    if not killed:
        print("  → No plotter running")

    return killed

def find_platformio():
    """Find PlatformIO executable"""
    # Try common locations
    possible_paths = [
        "pio",  # In PATH
        os.path.expanduser("~/.platformio/penv/Scripts/pio.exe"),
        os.path.expanduser("~/.platformio/penv/Scripts/platformio.exe"),
        "C:\\Users\\" + os.getenv('USERNAME', '') + "\\.platformio\\penv\\Scripts\\pio.exe",
        "platformio",
    ]

    for pio_path in possible_paths:
        # Skip if path doesn't exist (for file paths)
        if os.path.sep in pio_path and not os.path.exists(pio_path):
            continue

        try:
            result = subprocess.run(
                [pio_path, "--version"],
                capture_output=True,
                timeout=5,
                shell=False
            )
            if result.returncode == 0:
                print(f"    Version: {result.stdout.decode().strip()}")
                return pio_path
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue

    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <n-m>")
        print("       python run.py stop")
        print("Example: python run.py 1-1")
        print("         python run.py stop")
        sys.exit(1)

    arg = sys.argv[1]

    # File paths
    script_dir = Path(__file__).parent
    code_dir = script_dir / "code"
    src_dir = script_dir / "src"

    # Find source file
    # Special case: "stop" command
    if arg.lower() == "stop":
        source_file = code_dir / "stop.cpp"
    # Special case: "kp" command (Automation)
    elif arg.lower() == "kp":
        source_file = code_dir / "kp.cpp"
    else:
        # Parse n-m format
        if '-' not in arg:
            print("Error: Invalid format. Expected 'n-m' (e.g., 1-1)")
            print("Usage: python run.py <n-m>")
            print("Example: python run.py 1-1")
            sys.exit(1)

        parts = arg.split('-')
        if len(parts) != 2:
            print("Error: Invalid format. Expected 'n-m' (e.g., 1-1)")
            print("Usage: python run.py <n-m>")
            sys.exit(1)

        n, m = parts
        source_file = code_dir / f"p{n}-{m}.cpp"

    if not source_file.exists():
        print(f"Error: {source_file} not found")
        sys.exit(1)

    print(f"Found: {source_file}")

    # Kill any running plotter
    print("\nChecking for running plotter...")
    kill_plotter()

    # Find PlatformIO
    print("\nLooking for PlatformIO...")
    pio_cmd = find_platformio()
    if not pio_cmd:
        print("\n" + "!"*60)
        print("ERROR: PlatformIO not found!")
        print("Please use PlatformIO IDE to upload manually:")
        print("  1. Copy code to src/main.cpp")
        print("  2. Click 'Upload' button in PlatformIO")
        print("!"*60)
        sys.exit(1)

    print(f"  → Found: {pio_cmd}")

    # Clean src directory (remove all .cpp files)
    print("\nCleaning src directory...")
    for cpp_file in src_dir.glob("*.cpp"):
        cpp_file.unlink()
        print(f"  Removed: {cpp_file.name}")

    # Copy to src/main.cpp
    dest_file = src_dir / "main.cpp"
    shutil.copy2(source_file, dest_file)
    print(f"\nCopied to: {dest_file}")

    # Build and upload
    print("\n" + "="*60)
    print("Building and uploading to Arduino...")
    print("="*60 + "\n")

    try:
        result = subprocess.run(
            [pio_cmd, "run", "-t", "upload"],
            cwd=script_dir,
            check=True,
            text=True
        )
        print("\n" + "="*60)
        print("Upload successful!")
        print("="*60)
    except subprocess.CalledProcessError as e:
        print("\n" + "="*60)
        print("Upload failed!")
        print("Make sure Arduino is connected and no other program is using the port.")
        print("="*60)
        sys.exit(1)

    # Clean up
    print("\nCleaning up...")
    dest_file.unlink()
    print(f"  Removed: {dest_file.name}")

    # Skip plotter for stop command
    if arg.lower() == "stop":
        print("\n" + "="*60)
        print("Motor stopped. Exiting without plotter.")
        print("="*60)
        print("\nDone!")
        return

    # Automation script for KP tuning
    if arg.lower() == "kp":
        print("\n" + "="*60)
        print("Launching KP Tuning Automation...")
        print("="*60)
        print("waiting for reset...")
        time.sleep(3)
        
        src_path = str(script_dir / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            
        try:
            import tune_kp
            tune_kp.main()
        except Exception as e:
            print(f"Error running automation: {e}")
        return

    # Launch plotter
    print("\n" + "="*60)
    print("Launching plotter...")
    print("="*60)

    # Give Arduino time to reset
    print("Waiting for Arduino to reset...")
    time.sleep(3)

    # Add src directory to Python path
    src_path = str(script_dir / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        # Determine which plotter to use based on task
        # P#2 tasks use PID plotter, others use standard plotter
        if arg.startswith('2-'):
            plotter_name = "plotter_pid"
            print("  → Starting PID plotter...")
        else:
            plotter_name = "plotter"
            print("  → Starting plotter...")

        print("  → Press 'c' to clear data")
        print("  → Press 'p' to pause & save data")
        print("  → Close plot window to exit\n")

        # Import appropriate plotter module
        if plotter_name == "plotter_pid":
            import plotter_pid
        else:
            import plotter

    except ImportError as e:
        print(f"  → Failed to import {plotter_name}: {e}")
        print(f"  → Please check if src/{plotter_name}.py exists")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nPlotter stopped by user")
    except Exception as e:
        print(f"\n\nPlotter error: {e}")

    print("\nDone!")

if __name__ == "__main__":
    main()
