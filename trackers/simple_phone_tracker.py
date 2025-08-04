# trackers/simple_phone_tracker.py

import cv2
import numpy as np
from .base_tracker import TrackerBase

class SimplePhoneTracker(TrackerBase):
    """Detects phone-like objects using basic computer vision techniques."""
    
    def __init__(self, min_area=1000, max_area=50000, aspect_ratio_range=(1.5, 3.0)):
        """
        Initialize the simple phone tracker.
        
        Args:
            min_area: Minimum area for phone detection
            max_area: Maximum area for phone detection
            aspect_ratio_range: Range of aspect ratios for phones (width/height)
        """
        self.min_area = min_area
        self.max_area = max_area
        self.aspect_ratio_range = aspect_ratio_range
        
        print("✅ SimplePhoneTracker initialized successfully")
    
    def process_frame(self, frame, **kwargs):
        """
        Process a frame to detect phone-like objects.
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            tuple: (found, (error_x, error_y, error_z), debug_info)
        """
        # Get frame dimensions
        h, w = frame.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive thresholding for better detection
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours for phone-like objects
        phone_candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area or area > self.max_area:
                continue
            
            # Get bounding rectangle
            x, y, w_rect, h_rect = cv2.boundingRect(cnt)
            
            # Calculate aspect ratio
            aspect_ratio = w_rect / h_rect if h_rect > 0 else 0
            
            # Check if aspect ratio is in phone range
            if (aspect_ratio >= self.aspect_ratio_range[0] and 
                aspect_ratio <= self.aspect_ratio_range[1]):
                
                # Calculate center
                center = (x + w_rect // 2, y + h_rect // 2)
                
                phone_candidates.append({
                    "contour": cnt,
                    "bbox": (x, y, w_rect, h_rect),
                    "center": center,
                    "area": area,
                    "aspect_ratio": aspect_ratio
                })
        
        # Find the best phone candidate (closest to center)
        frame_center = (w // 2, h // 2)
        best_phone = None
        min_distance = float('inf')
        
        for candidate in phone_candidates:
            distance = np.sqrt((candidate["center"][0] - frame_center[0])**2 + 
                             (candidate["center"][1] - frame_center[1])**2)
            
            if distance < min_distance:
                min_distance = distance
                best_phone = candidate
        
        # Create debug information
        debug = {
            "status": "No Phone Detected",
            "frame_size": f"{w}x{h}",
            "contours_found": len(contours),
            "phone_candidates": len(phone_candidates),
            "previews": []
        }
        
        if best_phone:
            # Calculate error from center
            error_x = int(best_phone["center"][0] - frame_center[0])
            error_y = int(best_phone["center"][1] - frame_center[1])
            error_z = 0
            
            debug.update({
                "status": f"Phone detected (area: {best_phone['area']:.0f}, aspect: {best_phone['aspect_ratio']:.2f})",
                "center": best_phone["center"],
                "bbox": best_phone["bbox"],
                "area": best_phone["area"],
                "aspect_ratio": best_phone["aspect_ratio"],
                "error": (error_x, error_y, error_z)
            })
            
            return True, (error_x, error_y, error_z), debug
        else:
            return False, (0, 0, 0), debug
    
    def draw_debug_info(self, frame, debug_info):
        """
        Draw debug information on the frame.
        
        Args:
            frame: Input frame to draw on
            debug_info: Debug information from process_frame
        """
        if debug_info.get("status", "").startswith("Phone detected"):
            bbox = debug_info.get("bbox")
            center = debug_info.get("center")
            
            if bbox and center:
                x, y, w, h = bbox
                
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Draw center point
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                
                # Draw cross marker
                cv2.drawMarker(frame, center, (255, 0, 0), 
                              markerType=cv2.MARKER_CROSS, markerSize=10, thickness=2)
                
                # Add text with phone info
                area = debug_info.get("area", 0)
                aspect_ratio = debug_info.get("aspect_ratio", 0)
                cv2.putText(frame, f"Area:{area:.0f} AR:{aspect_ratio:.2f}", 
                           (x + w + 10, y + h//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Add status text
        status = debug_info.get("status", "No status")
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)
        
        # Add detection count
        contours_found = debug_info.get("contours_found", 0)
        phone_candidates = debug_info.get("phone_candidates", 0)
        count_text = f"Contours: {contours_found} | Phones: {phone_candidates}"
        cv2.putText(frame, count_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, (255, 255, 0), 2) 