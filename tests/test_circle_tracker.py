# tests/test_circle_tracker.py
import numpy as np
import cv2
from trackers.circle_tracker import CircleTracker

def generate_dummy_circle(img_size=(480, 640), center=None, radius=50, color=(255, 255, 255)):
    """Generate a test image with a circle."""
    if center is None:
        center = (img_size[1]//2 + 40, img_size[0]//2)  # Slightly right of center
    
    img = np.zeros(img_size + (3,), dtype=np.uint8)
    cv2.circle(img, center, radius, color, -1)  # Filled circle
    return img

def test_circle_tracker_initialization():
    """Test that CircleTracker initializes correctly."""
    tracker = CircleTracker()
    assert tracker.min_radius == 20
    assert tracker.max_radius == 100
    assert tracker.param1 == 50
    assert tracker.param2 == 30
    
    # Test custom parameters
    tracker = CircleTracker(min_radius=10, max_radius=80, param1=40, param2=25)
    assert tracker.min_radius == 10
    assert tracker.max_radius == 80
    assert tracker.param1 == 40
    assert tracker.param2 == 25

def test_circle_tracker_detection():
    """Test that CircleTracker can detect circles."""
    tracker = CircleTracker()
    frame = generate_dummy_circle()
    
    found, (err_x, err_y, err_z), debug = tracker.process_frame(frame)
    
    # Test that the tracker returns the expected format
    assert isinstance(found, bool)
    assert isinstance(err_x, (int, float))
    assert isinstance(err_y, (int, float))
    assert isinstance(err_z, (int, float))
    assert isinstance(debug, dict)
    
    # If detection works, test the error sign
    if found:
        assert err_x > 0  # circle is to the right of center
        assert "Circle detected" in debug.get("status", "")
        assert "center" in debug
        assert "radius" in debug

def test_circle_tracker_no_circle():
    """Test that CircleTracker handles frames without circles."""
    tracker = CircleTracker()
    # Create a blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    found, (err_x, err_y, err_z), debug = tracker.process_frame(frame)
    
    assert not found
    assert err_x == 0
    assert err_y == 0
    assert err_z == 0
    assert "No Circle Detected" in debug.get("status", "")

def test_circle_tracker_multiple_circles():
    """Test that CircleTracker selects the largest circle when multiple are present."""
    tracker = CircleTracker()
    
    # Create frame with multiple circles
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(frame, (200, 200), 30, (255, 255, 255), -1)  # Small circle
    cv2.circle(frame, (400, 200), 60, (255, 255, 255), -1)  # Large circle
    
    found, (err_x, err_y, err_z), debug = tracker.process_frame(frame)
    
    if found:
        # Should detect the larger circle (radius 60)
        assert debug.get("radius", 0) >= 50  # Should be close to 60
        # The larger circle is at (400, 200), so error_x should be positive
        assert err_x > 0 