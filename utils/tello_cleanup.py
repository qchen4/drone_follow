#!/usr/bin/env python3
"""
Tello Cleanup Utility
This script helps clean up any existing Tello processes and free up ports.
"""

import subprocess
import sys
import time
import logging

def check_tello_ports():
    """Check if Tello ports are in use."""
    tello_ports = [8889, 8890, 11111]  # Control, state, video ports

    for port in tello_ports:
        try:
            result = subprocess.run(
                ['sudo', 'netstat', '-tulpn'],
                capture_output=True,
                text=True,
                check=True
            )

            if f':{port}' in result.stdout:
                print(f"⚠️  Port {port} is in use")
                return True
            else:
                print(f"✅ Port {port} is free")

        except subprocess.CalledProcessError:
            print(f"❌ Could not check port {port}")
            return True

    return False

def kill_tello_processes():
    """Kill any existing Tello-related processes."""
    print("\n=== Cleaning up Tello processes ===")

    try:
        # Find Python processes that might be using Tello ports
        result = subprocess.run(
            ['sudo', 'netstat', '-tulpn'],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.split('\n')
        killed_count = 0

        for line in lines:
            if any(f':{port}' in line for port in [8889, 8890, 11111]):
                # Extract PID from the line
                parts = line.split()
                if len(parts) >= 7:
                    pid_part = parts[6]
                    if '/' in pid_part:
                        pid = pid_part.split('/')[0]
                        try:
                            print(f"Killing process {pid}...")
                            subprocess.run(['sudo', 'kill', pid], check=True)
                            killed_count += 1
                            time.sleep(0.5)  # Give it time to die
                        except subprocess.CalledProcessError:
                            print(f"Could not kill process {pid}")

        if killed_count > 0:
            print(f"✅ Killed {killed_count} Tello-related processes")
        else:
            print("✅ No Tello processes found to kill")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during cleanup: {e}")

def wait_for_ports_to_free():
    """Wait for ports to become available."""
    print("\n=== Waiting for ports to free up ===")

    for attempt in range(10):
        if not check_tello_ports():
            print("✅ All ports are now free!")
            return True

        print(f"Waiting... (attempt {attempt + 1}/10)")
        time.sleep(1)

    print("❌ Ports are still in use after waiting")
    return False

def main():
    """Main cleanup function."""
    print("Tello Cleanup Utility")
    print("=" * 30)

    # Check current status
    print("=== Checking current port status ===")
    ports_in_use = check_tello_ports()

    if ports_in_use:
        print("\n⚠️  Tello ports are in use. Cleaning up...")
        kill_tello_processes()

        if wait_for_ports_to_free():
            print("\n✅ Cleanup successful! You can now run the drone application.")
        else:
            print("\n❌ Cleanup failed. You may need to:")
            print("1. Restart your computer")
            print("2. Check for other Tello applications")
            print("3. Restart the Tello drone")
            sys.exit(1)
    else:
        print("\n✅ All ports are free! You can run the drone application.")

if __name__ == "__main__":
    main()
