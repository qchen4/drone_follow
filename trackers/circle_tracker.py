# trackers/circle_tracker.py

import cv2
import numpy as np
from .base_tracker import TrackerBase

class CircleTracker(TrackerBase):
    def __init__(self, min_radius=20, max_radius=100, param1=50, param2=30, area_range=None, circularity_min=0.6):
        # Support both old radius-based and new area-based parameters
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.param1 = param1
        self.param2 = param2
        
        # Auto-calculate area range from radius if not provided
        if area_range is None:
            # Estimate area range from radius (area = π * r²)
            min_area = int(3.14 * min_radius * min_radius * 0.3)  # More conservative estimate
            max_area = int(3.14 * max_radius * max_radius * 3)    # More liberal estimate
            self.area_range = (min_area, max_area)
        else:
            self.area_range = area_range
            
        self.circularity_min = circularity_min

    def process_frame(self, frame, **kwargs):
        # Get frame dimensions for adaptive parameters
        h, w = frame.shape[:2]
        
        # Adaptive area range based on frame size
        frame_area = h * w
        adaptive_min_area = frame_area // 2000  # 0.05% of frame (more permissive)
        adaptive_max_area = frame_area // 10    # 10% of frame (more permissive)
        
        # Use adaptive range if it makes sense
        if adaptive_min_area < self.area_range[0]:
            adaptive_min_area = self.area_range[0]
        if adaptive_max_area > self.area_range[1]:
            adaptive_max_area = self.area_range[1]
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Try multiple thresholding methods for better detection
        # Method 1: OTSU
        _, binary_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Method 2: Adaptive threshold (better for varying lighting)
        binary_adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Method 3: Simple threshold (for high contrast objects like white logos)
        _, binary_simple = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        
        # Combine methods - use the one that gives the most contours
        binaries = [binary_otsu, binary_adaptive, binary_simple]
        best_binary = None
        max_contours = 0
        
        for binary in binaries:
            morph_temp = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            contours_temp, _ = cv2.findContours(morph_temp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours_temp) > max_contours:
                max_contours = len(contours_temp)
                best_binary = binary
        
        # Use the best binary image
        binary = best_binary if best_binary is not None else binary_otsu
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_circle = None
        best_circularity = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < adaptive_min_area or area > adaptive_max_area:
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0: continue
            circularity = 4 * np.pi * area / (perimeter ** 2)
            if circularity > self.circularity_min and circularity > best_circularity:
                M = cv2.moments(cnt)
                if M["m00"] == 0: continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(cnt)
                best_circle = {
                    "cnt": cnt, "center": (cx, cy), "bbox": (x, y, w, h),
                    "circularity": circularity, "area": area
                }
                best_circularity = circularity

        frame_annotated = frame.copy()
        previews = [
            self._label_img(frame.copy(), "Original"),
            self._label_img(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), "Gray"),
            self._label_img(cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR), "Blurred"),
            self._label_img(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), "Binary"),
            self._label_img(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR), "Morph"),
        ]
        
        # Add debug info about contours found
        debug_contour_info = f"Contours: {len(contours)}"
        if len(contours) > 0:
            areas = [cv2.contourArea(cnt) for cnt in contours]
            debug_contour_info += f" | Areas: {[int(a) for a in areas[:3]]}"
        previews.append(self._label_img(frame_annotated, debug_contour_info))

        if best_circle:
            cnt = best_circle["cnt"]
            x, y, w, h = best_circle["bbox"]
            cv2.drawContours(frame_annotated, [cnt], -1, (0, 255, 0), 2)
            cv2.circle(frame_annotated, best_circle["center"], 5, (0, 0, 255), -1)
            previews.append(self._label_img(frame_annotated, "Circle Detected"))
            h, w = frame.shape[:2]
            img_center = (w // 2, h // 2)
            error_x = int(best_circle["center"][0] - img_center[0])
            error_y = int(best_circle["center"][1] - img_center[1])
            error_z = 0
            debug = {
                "status": f"Circle detected (area: {best_circle['area']:.0f}, circularity: {best_circle['circularity']:.2f})",
                "center": best_circle["center"],
                "bbox": best_circle["bbox"],
                "area": best_circle["area"],
                "circularity": best_circle["circularity"],
                "frame_size": f"{w}x{h}",
                "adaptive_area_range": (adaptive_min_area, adaptive_max_area),
                "previews": previews
            }
            return True, (error_x, error_y, error_z), debug
        else:
            # Analyze why detection failed
            debug_reasons = []
            if len(contours) == 0:
                debug_reasons.append("No contours found")
            else:
                # Check each contour to see why it was rejected
                for i, cnt in enumerate(contours[:3]):  # Check first 3 contours
                    area = cv2.contourArea(cnt)
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter ** 2)
                    else:
                        circularity = 0
                    
                    if area < adaptive_min_area:
                        debug_reasons.append(f"Contour {i}: too small (area={area:.0f})")
                    elif area > adaptive_max_area:
                        debug_reasons.append(f"Contour {i}: too large (area={area:.0f})")
                    elif circularity < self.circularity_min:
                        debug_reasons.append(f"Contour {i}: not circular enough (C={circularity:.2f})")
            
            debug_status = "No Circle Detected"
            if debug_reasons:
                debug_status += f" - {', '.join(debug_reasons[:2])}"  # Show first 2 reasons
            
            previews.append(self._label_img(frame_annotated, debug_status))
            debug = {
                "status": debug_status,
                "bbox": None,
                "frame_size": f"{w}x{h}",
                "adaptive_area_range": (adaptive_min_area, adaptive_max_area),
                "contours_found": len(contours),
                "previews": previews
            }
            return False, (0, 0, 0), debug

    def _label_img(self, img, text):
        h, w = img.shape[:2]
        img_center = (w // 2, h // 2)
        cv2.putText(img, text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        return img

    def draw_debug_info(self, frame, debug_info):
        """
        Draw debug information on the frame.
        
        Args:
            frame: Input frame to draw on
            debug_info: Debug information from process_frame
        """
        if debug_info.get("status", "").startswith("Circle detected"):
            center = debug_info.get("center")
            bbox = debug_info.get("bbox")
            
            if center and bbox:
                x, y, w, h = bbox
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Draw center point
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                # Draw a cross at the center
                cv2.drawMarker(frame, center, (255, 0, 0), 
                              markerType=cv2.MARKER_CROSS, markerSize=10, thickness=2)
                
                # Add text with circle info
                area = debug_info.get("area", 0)
                circularity = debug_info.get("circularity", 0)
                cv2.putText(frame, f"Area:{area:.0f} C:{circularity:.2f}", 
                           (x + w + 10, y + h//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)