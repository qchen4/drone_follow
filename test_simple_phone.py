#!/usr/bin/env python3
"""
Test Simple Phone Tracker
This script tests the SimplePhoneTracker with a sample image.
"""

import cv2
import numpy as np
from trackers.simple_phone_tracker import SimplePhoneTracker

def test_simple_phone_tracker():
    """Test the SimplePhoneTracker with a sample image."""
    print("Testing Simple Phone Tracker")
    print("=" * 35)

    try:
        # Create SimplePhoneTracker
        tracker = SimplePhoneTracker(min_area=500, max_area=10000, aspect_ratio_range=(1.5, 3.0))
        print("✅ SimplePhoneTracker created successfully")

        # Create a test image with phone-like rectangles
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add phone-like rectangles (rectangular shapes)
        cv2.rectangle(test_image, (200, 150), (300, 200), (255, 255, 255), -1)  # Phone-like rectangle
        cv2.rectangle(test_image, (400, 200), (500, 250), (128, 128, 128), -1)  # Another phone-like rectangle

        print(f"✅ Test image created: {test_image.shape}")

        # Process frame
        found, error, debug = tracker.process_frame(test_image)

        # Display results
        print(f"Found: {found}")
        print(f"Error: {error}")
        print(f"Status: {debug.get('status', 'Unknown')}")
        print(f"Frame size: {debug.get('frame_size', 'Unknown')}")
        print(f"Contours found: {debug.get('contours_found', 0)}")
        print(f"Phone candidates: {debug.get('phone_candidates', 0)}")

        if found:
            print(f"✅ Phone detected successfully!")
            print(f"Area: {debug.get('area', 'Unknown')}")
            print(f"Aspect ratio: {debug.get('aspect_ratio', 'Unknown')}")
        else:
            print(f"❌ No phone detected")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_phone_tracker()
    if success:
        print("\n✅ SimplePhoneTracker test completed!")
    else:
        print("\n❌ SimplePhoneTracker test failed!")
