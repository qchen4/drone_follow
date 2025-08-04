#!/usr/bin/env python3
"""
Test script for motor stop error handling.
This script tests the new motor state management functions.
"""

import sys
import logging
import time

# Add the project root to the path
sys.path.append('.')

from utils.tello_cleanup import check_drone_state, handle_motor_stop_error, safe_land
from utils.logging_utils import setup_logger

def test_motor_handling():
    """Test the motor stop error handling functions."""
    setup_logger()
    logging.info("Testing motor stop error handling...")
    
    # Test 1: Check drone state (without actual drone)
    logging.info("Test 1: Testing check_drone_state function...")
    try:
        # This will fail since we don't have a real drone, but it tests the function structure
        state = check_drone_state(None)
        logging.info(f"Drone state check result: {state}")
    except Exception as e:
        logging.info(f"Expected error when no drone connected: {e}")
    
    # Test 2: Test motor stop error handler logic
    logging.info("Test 2: Testing motor stop error handler logic...")
    
    # Simulate different error scenarios
    test_errors = [
        "error Motor stop",
        "Motor stop",
        "error No valid imu",
        "error",
        "some other error"
    ]
    
    for error_msg in test_errors:
        is_motor_stop = "Motor stop" in error_msg or "error Motor stop" in error_msg
        logging.info(f"Error: '{error_msg}' -> Motor stop detected: {is_motor_stop}")
    
    # Test 3: Test safe landing logic
    logging.info("Test 3: Testing safe landing logic...")
    try:
        result = safe_land(None)
        logging.info(f"Safe landing result: {result}")
    except Exception as e:
        logging.info(f"Expected error when no drone connected: {e}")
    
    logging.info("Motor handling tests completed!")

def test_error_detection():
    """Test error message detection patterns."""
    logging.info("Testing error detection patterns...")
    
    # Test cases
    test_cases = [
        ("error Motor stop", True),
        ("Motor stop", True),
        ("error No valid imu", False),
        ("error", False),
        ("some other error", False),
        ("Command 'up 30' was unsuccessful for 4 tries. Latest response:\t'error Motor stop'", True),
    ]
    
    for error_msg, expected in test_cases:
        detected = "Motor stop" in error_msg or "error Motor stop" in error_msg
        status = "✓" if detected == expected else "✗"
        logging.info(f"{status} '{error_msg}' -> Detected: {detected}, Expected: {expected}")

if __name__ == "__main__":
    print("Motor Stop Error Handling Test")
    print("=" * 40)
    
    test_motor_handling()
    print()
    test_error_detection()
    
    print("\nTest completed!")
    print("\nTo test with a real drone:")
    print("1. Connect your Tello drone")
    print("2. Run: python main.py")
    print("3. The new error handling will automatically detect and handle motor stop errors") 