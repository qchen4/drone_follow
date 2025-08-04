#!/usr/bin/env python3
"""
Test script for precision landing with ArUco markers.

This script demonstrates the dynamic precision landing functionality:
1. Uses PrecisionArucoTracker for pose estimation
2. Implements PrecisionLandingProtocol with spiral approach
3. Shows the three phases: SEARCH, ALIGN, APPROACH, TOUCHDOWN

Usage:
    python test_precision_landing.py

Requirements:
    - ArUco marker attached to landing target
    - Tello drone connected
    - OpenCV with ArUco support
"""

import cv2
import numpy as np
import time
import logging
from utils.logging_utils import setup_logger
from connectors.tello_connector import TelloConnector
from trackers.precision_aruco_tracker import PrecisionArucoTracker
from landing_protocols.precision_landing import PrecisionLandingProtocol
from landing_protocols.continuous_glide_landing import ContinuousGlideLanding
from control_protocols.pid_control import PIDControl
from visual_protocols.opencv_visual import OpenCVVisualProtocol
from visual_protocols.grid_visual import GridVisualProtocol

def create_test_aruco_marker():
    """Create a test ArUco marker image for demonstration."""
    # Create ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Generate marker image
    marker_size = 200
    marker_img = np.zeros((marker_size, marker_size), dtype=np.uint8)
    cv2.aruco.generateImageMarker(aruco_dict, 0, marker_size, marker_img, 1)
    
    # Add border and save
    bordered_img = cv2.copyMakeBorder(marker_img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=255)
    cv2.imwrite("test_aruco_marker.png", bordered_img)
    print("Test ArUco marker saved as 'test_aruco_marker.png'")
    print("Print this image and place it on your landing target.")

def test_precision_tracker():
    """Test the precision ArUco tracker with a webcam or video file."""
    print("Testing Precision ArUco Tracker...")
    
    # Initialize tracker
    tracker = PrecisionArucoTracker(marker_size=15.0)
    
    # Try to open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Webcam not available. Please ensure you have a camera connected.")
        return
    
    print("Press 'q' to quit, 's' to save current frame")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame
        found, error_data, debug_info = tracker.process_frame(frame)
        
        # Draw debug info
        if hasattr(tracker, 'draw_debug_info'):
            tracker.draw_debug_info(frame, debug_info)
        
        # Display status
        status_text = debug_info.get("status", "No marker detected")
        cv2.putText(frame, status_text, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show frame
        cv2.imshow("Precision ArUco Tracker Test", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite("test_frame.png", frame)
            print("Frame saved as 'test_frame.png'")
    
    cap.release()
    cv2.destroyAllWindows()

def test_precision_landing_simulation():
    """Simulate precision landing without actual drone control."""
    print("Simulating Precision Landing Protocol...")
    
    # Initialize components
    tracker = PrecisionArucoTracker(marker_size=15.0)
    control_protocol = PIDControl(Kp=0.5, Ki=0.01, Kd=0.05, vmax=25)
    visual_protocol = GridVisualProtocol(
        window_name="Precision Landing Simulation",
        grid_shape=(2, 2),
        cell_size=(320, 240)
    )
    
    landing_protocol = PrecisionLandingProtocol(
        tracker=tracker,
        control_protocol=control_protocol,
        visual_protocol=visual_protocol,
        target_area_percentage=15.0,
        min_distance=20.0,
        spiral_radius=50.0,
        alignment_threshold=5.0,
        position_threshold=10
    )
    
    print("Precision Landing Protocol initialized with:")
    print(f"  - Target area percentage: {landing_protocol.target_area_percentage}%")
    print(f"  - Minimum distance: {landing_protocol.min_distance}cm")
    print(f"  - Spiral radius: {landing_protocol.spiral_radius}cm")
    print(f"  - Alignment threshold: {np.degrees(landing_protocol.alignment_threshold)}°")
    print(f"  - Position threshold: {landing_protocol.position_threshold}px")
    
    # Simulate landing phases
    phases = ["SEARCH", "ALIGN", "APPROACH", "TOUCHDOWN"]
    for phase in phases:
        print(f"\nSimulating {phase} phase...")
        time.sleep(1)
        print(f"  - Phase: {phase}")
        print(f"  - Current spiral angle: {landing_protocol.spiral_angle:.2f}")
        print(f"  - Detection timeout: {landing_protocol.detection_timeout}s")
    
    print("\nSimulation complete!")

def test_continuous_glide_landing_simulation():
    """Simulate continuous glide landing without actual drone control."""
    print("Simulating Continuous Glide Landing Protocol...")
    
    # Initialize components
    tracker = PrecisionArucoTracker(marker_size=15.0)
    control_protocol = PIDControl(Kp=0.5, Ki=0.01, Kd=0.05, vmax=25)
    
    landing_protocol = ContinuousGlideLanding(
        descent_gain=0.3,
        min_vz=10,
        max_vz=25,
        height_threshold=20.0,
        timeout=30.0,
        tracker=tracker,
        control_protocol=control_protocol
    )
    
    print("Continuous Glide Landing Protocol initialized with:")
    print(f"  - Descent gain: {landing_protocol.descent_gain}")
    print(f"  - Min descent speed: {landing_protocol.min_vz} cm/s")
    print(f"  - Max descent speed: {landing_protocol.max_vz} cm/s")
    print(f"  - Height threshold: {landing_protocol.height_threshold} cm")
    print(f"  - Timeout: {landing_protocol.timeout} seconds")
    
    # Simulate descent with different error scenarios
    test_errors = [(0, 0), (10, 5), (50, 30), (100, 80)]
    print("\nSimulating descent with different alignment errors:")
    
    for error in test_errors:
        descent_speed = landing_protocol._compute_descent_speed(error)
        print(f"  - Error {error}: descent speed = {descent_speed} cm/s")
        time.sleep(0.5)
    
    print("\nSimulation complete!")

def test_grid_visual_protocol():
    """Test the grid visual protocol with sample data."""
    print("Testing Grid Visual Protocol...")
    
    # Create a sample frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some test content to the frame
    cv2.rectangle(frame, (100, 100), (300, 200), (0, 255, 0), 2)
    cv2.circle(frame, (320, 240), 50, (255, 0, 0), 2)
    cv2.putText(frame, "Test Frame", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Create sample debug data
    debug_data = {
        "status": "Testing Grid Visual",
        "candidates": [
            (150, 150, 30, 0.8),
            (400, 300, 25, 0.6),
            (200, 350, 40, 0.4)
        ],
        "bbox": [100, 100, 200, 100],
        "center": [320, 240],
        "landing_phase": "TEST",
        "area_percentage": 15.5,
        "distance": 25.3,
        "yaw_error": 2.1
    }
    
    # Initialize grid visual protocol
    grid_visual = GridVisualProtocol(
        window_name="Grid Visual Test",
        grid_shape=(2, 2),
        cell_size=(320, 240)
    )
    
    # Initialize window and show the grid
    grid_visual.initialize_window()
    
    print("Grid visual protocol initialized with:")
    print(f"  - Window name: {grid_visual.window_name}")
    print(f"  - Grid shape: {grid_visual.grid_shape}")
    print(f"  - Cell size: {grid_visual.cell_size}")
    print("\nDisplaying grid view...")
    print("Press any key to close the window")
    
    # Show the grid
    grid_visual.show(frame, debug_data)
    
    # Wait for key press
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("Grid visual test complete!")

def main():
    """Main function to run precision landing tests."""
    setup_logger()
    logging.info("Starting Precision Landing Tests")
    
    print("=" * 60)
    print("PRECISION LANDING TEST SUITE")
    print("=" * 60)
    
    while True:
        print("\nChoose test option:")
        print("1. Create test ArUco marker")
        print("2. Test Precision ArUco Tracker (webcam)")
        print("3. Simulate Precision Landing Protocol")
        print("4. Simulate Continuous Glide Landing Protocol")
        print("5. Test Grid Visual Protocol")
        print("6. Run full precision landing (requires Tello)")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            create_test_aruco_marker()
        elif choice == "2":
            test_precision_tracker()
        elif choice == "3":
            test_precision_landing_simulation()
        elif choice == "4":
            test_continuous_glide_landing_simulation()
        elif choice == "5":
            test_grid_visual_protocol()
        elif choice == "6":
            print("Full precision landing requires a connected Tello drone.")
            print("Please run 'python main.py' and select:")
            print("  - Tracker: 6 (Precision ArUco)")
            print("  - Landing: 3 (Precision) or 4 (Continuous Glide)")
            print("  - Visual: 3 (Grid Debug)")
            break
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please enter 1-7.")

if __name__ == "__main__":
    main() 