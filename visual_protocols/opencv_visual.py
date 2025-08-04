# visual_protocols/opencv_visual.py

import cv2
import logging
from .base_visual import VisualProtocol

class OpenCVVisualProtocol(VisualProtocol):
    """OpenCV-based visual protocol for real-time drone tracking display."""
    
    def __init__(self, window_name="Tello Debug", debug_level="detailed"):
        self.window_name = window_name
        self.debug_level = debug_level
        self.window_created = False
        self._frame_buffer = None
        self._debug_buffer = None
        
    def initialize_window(self):
        """Initialize the OpenCV window in the main thread."""
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 640, 480)
            self.window_created = True
            logging.info(f"OpenCV window '{self.window_name}' created successfully")
        except Exception as e:
            logging.error(f"Failed to create OpenCV window: {e}")
        
    def show(self, frame, debug=None):
        """Store frame and debug info for the main thread to display."""
        if frame is None:
            return
            
        # Store frame and debug info for the main thread to display
        self._frame_buffer = frame.copy()
        self._debug_buffer = debug
        
        # Note: Window creation and display are handled in main thread
        
    def _display_frame(self):
        """Actually display the frame (called from main thread)."""
        if self._frame_buffer is None:
            return
            
        if not self.window_created:
            logging.warning("OpenCV window not created yet")
            return
            
        try:
            # Create a copy for drawing
            display_frame = self._frame_buffer.copy()
            
            # Add debug information overlay
            if self._debug_buffer and self.debug_level == "detailed":
                self._draw_debug_info(display_frame, self._debug_buffer)
            
            # Display the frame
            cv2.imshow(self.window_name, display_frame)
            cv2.waitKey(1)  # Update window
            
            # Log frame display for debugging
            logging.debug(f"Displayed frame shape: {display_frame.shape}")
            
        except Exception as e:
            logging.error(f"Error displaying frame: {e}")
            logging.error(f"Frame buffer shape: {self._frame_buffer.shape if self._frame_buffer is not None else 'None'}")
            logging.error(f"Window created: {self.window_created}")
        
    def show_previews(self, previews):
        """Display additional preview windows if needed."""
        if not previews:
            return
            
        for i, (name, img) in enumerate(previews.items()):
            window_name = f"{self.window_name}_{name}"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.imshow(window_name, img)
            cv2.waitKey(1)
    
    def close(self):
        """Close all OpenCV windows."""
        cv2.destroyAllWindows()
        self.window_created = False
        
    def _draw_debug_info(self, frame, debug):
        """Draw debug information on the frame."""
        # Add status text
        status = debug.get('status', 'No status')
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)
        
        # Add marker information if available
        if 'marker_id' in debug:
            marker_text = f"Marker ID: {debug['marker_id']}"
            cv2.putText(frame, marker_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 0), 2)
        
        # Add center coordinates if available
        if 'center' in debug:
            center = debug['center']
            center_text = f"Center: ({center[0]:.1f}, {center[1]:.1f})"
            cv2.putText(frame, center_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 0), 2)
        
        # Add circle-specific information if available
        if 'bbox' in debug and debug['bbox'] is not None:
            x, y, w, h = debug['bbox']
            area = debug.get('area', 0)
            circularity = debug.get('circularity', 0)
            info_text = f"Area: {area:.0f} | C: {circularity:.2f}"
            cv2.putText(frame, info_text, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (255, 255, 0), 2)
