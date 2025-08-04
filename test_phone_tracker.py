#!/usr/bin/env python3
"""
Test Phone Tracker
This script tests the PhoneTracker with a sample image.
"""

import cv2
import numpy as np
from trackers.phone_tracker import PhoneTracker

def test_phone_tracker():
    """Test the PhoneTracker with a sample image."""
    print("Testing Phone Tracker")
    print("=" * 30)
    
    try:
        # Create PhoneTracker
        tracker = PhoneTracker(confidence=0.3, iou_threshold=0.5)
        print("✅ PhoneTracker created successfully")
        
        # Create a test image (you can replace this with a real image)
        # For now, create a simple test image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some rectangles that might look like phones
        cv2.rectangle(test_image, (200, 150), (300, 250), (255, 255, 255), -1)  # White rectangle
        cv2.rectangle(test_image, (400, 200), (500, 300), (128, 128, 128), -1)  # Gray rectangle
        
        print(f"✅ Test image created: {test_image.shape}")
        
        # Process frame
        found, error, debug = tracker.process_frame(test_image)
        
        # Display results
        print(f"Found: {found}")
        print(f"Error: {error}")
        print(f"Status: {debug.get('status', 'Unknown')}")
        print(f"Frame size: {debug.get('frame_size', 'Unknown')}")
        print(f"Total detections: {debug.get('total_detections', 0)}")
        print(f"Phone detections: {debug.get('phone_detections', 0)}")
        
        if found:
            print(f"✅ Phone detected successfully!")
            print(f"Confidence: {debug.get('confidence', 'Unknown')}")
            print(f"Tracker ID: {debug.get('tracker_id', 'Unknown')}")
        else:
            print(f"❌ No phone detected (this is expected with a synthetic image)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phone_tracker()
    if success:
        print("\n✅ PhoneTracker test completed!")
    else:
        print("\n❌ PhoneTracker test failed!") 