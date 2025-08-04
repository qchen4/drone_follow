#!/usr/bin/env python3
"""
Tello Cleanup Utility
This script helps clean up any existing Tello processes and free up ports.
"""

import subprocess
import sys
import time
import logging
from djitellopy import Tello

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

def cleanup_tello(tello: Tello):
    """Clean up Tello resources safely."""
    try:
        logging.info("Cleaning up Tello resources …")
        tello.streamoff()
        tello.end()
        logging.info("Tello cleanup done.")
    except Exception as e:
        logging.error(f"Error during Tello cleanup: {e}")

def check_drone_state(tello: Tello) -> dict:
    """Check the current state of the drone and return status information."""
    state = {
        "connected": False,
        "battery": 0,
        "motors_on": False,
        "flying": False,
        "height": 0,
        "temperature": 0
    }
    
    try:
        # Check basic connection
        tello.get_battery()
        state["connected"] = True
        state["battery"] = tello.get_battery()
        
        # Check if motors are on (this is a heuristic based on height)
        try:
            height = tello.get_height()
            state["height"] = height
            # If height > 0, motors are likely on
            state["motors_on"] = height > 0
            state["flying"] = height > 10  # Consider flying if above 10cm
        except Exception as e:
            logging.debug(f"Could not get height: {e}")
            state["motors_on"] = False
            state["flying"] = False
            
        # Try to get temperature
        try:
            state["temperature"] = tello.get_temperature()
        except Exception as e:
            logging.debug(f"Could not get temperature: {e}")
            
    except Exception as e:
        logging.warning(f"Could not check drone state: {e}")
        state["connected"] = False
        
    return state

def handle_motor_stop_error(tello: Tello, operation: str) -> bool:
    """
    Handle motor stop errors gracefully.
    
    Args:
        tello: Tello instance
        operation: Description of the operation that failed
        
    Returns:
        bool: True if the operation should be retried, False if we should give up
    """
    logging.warning(f"Motor stop error during {operation}")
    
    # Check drone state
    state = check_drone_state(tello)
    
    if not state["connected"]:
        logging.error("Drone not connected. Cannot proceed.")
        return False
        
    if state["battery"] < 10:
        logging.error(f"Battery too low ({state['battery']}%). Cannot proceed.")
        return False
        
    if state["temperature"] > 80:
        logging.error(f"Drone temperature too high ({state['temperature']}°C). Cannot proceed.")
        return False
    
    # If motors are off but we're trying to fly, we need to take off first
    if not state["motors_on"] and operation in ["up", "down", "land"]:
        logging.info("Motors are off. Attempting to start motors...")
        try:
            # Try to take off to start motors
            tello.takeoff()
            time.sleep(2)  # Wait for motors to start
            return True
        except Exception as e:
            logging.error(f"Failed to start motors: {e}")
            return False
    
    # If we're already flying, the motor stop might be temporary
    if state["flying"]:
        logging.info("Drone is flying but motors stopped. This might be temporary.")
        time.sleep(1)  # Wait a bit
        return True
    
    # If we're on the ground and motors are off, we can't proceed
    logging.error("Drone is on the ground with motors off. Cannot perform flight operations.")
    return False

def safe_land(tello: Tello) -> bool:
    """
    Safely land the drone with proper error handling.
    
    Returns:
        bool: True if landing was successful or drone is already on ground
    """
    try:
        state = check_drone_state(tello)
        
        # If already on ground, we're done
        if not state["flying"]:
            logging.info("Drone is already on the ground.")
            return True
            
        # Try to land
        logging.info("Attempting to land...")
        tello.land()
        time.sleep(3)  # Wait for landing to complete
        
        # Check if landing was successful
        final_state = check_drone_state(tello)
        if not final_state["flying"]:
            logging.info("Landing successful.")
            return True
        else:
            logging.warning("Landing may not have completed successfully.")
            return False
            
    except Exception as e:
        logging.error(f"Error during landing: {e}")
        if handle_motor_stop_error(tello, "land"):
            # Retry landing
            return safe_land(tello)
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
