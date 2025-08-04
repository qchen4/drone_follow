# landing_protocols/precision_landing.py

import time
import logging
import numpy as np
import cv2
from .base_landing import LandingProtocolBase

class PrecisionLandingProtocol(LandingProtocolBase):
    """
    Dynamic precision landing protocol with target detection.
    
    Features:
    - Align: Uses marker corner positions to estimate pose and compute lateral error and orientation
    - Approach: Follows a slowly converging spiral or straight-line path toward the marker
    - Touchdown: Lands when marker fills a certain percentage of the frame
    """
    
    def __init__(self, tracker, control_protocol, visual_protocol,
                 target_area_percentage=15.0,  # Percentage of frame the marker should fill
                 min_distance=20.0,  # Minimum distance in cm before landing
                 spiral_radius=50.0,  # Initial spiral radius in cm
                 spiral_tightening_rate=0.95,  # How quickly spiral tightens
                 alignment_threshold=5.0,  # Degrees for yaw alignment
                 position_threshold=10.0,  # Pixels for position alignment
                 max_landing_time=30.0):  # Maximum time for landing sequence
        
        self.tracker = tracker
        self.control_protocol = control_protocol
        self.visual_protocol = visual_protocol
        
        # Landing parameters
        self.target_area_percentage = target_area_percentage
        self.min_distance = min_distance
        self.spiral_radius = spiral_radius
        self.spiral_tightening_rate = spiral_tightening_rate
        self.alignment_threshold = np.radians(alignment_threshold)
        self.position_threshold = position_threshold
        self.max_landing_time = max_landing_time
        
        # State variables
        self.landing_start_time = None
        self.current_phase = "SEARCH"
        self.spiral_angle = 0.0
        self.last_detection_time = None
        self.detection_timeout = 2.0  # Seconds without detection before timeout
        
        # PID controllers for smooth movement
        self.position_pid = None
        self.yaw_pid = None
        self._initialize_pids()
    
    def _initialize_pids(self):
        """Initialize PID controllers for position and yaw control."""
        try:
            from control_protocols.pid_control import PIDControl
            # Position control (x, y) - using single PID for both axes
            self.position_pid = PIDControl(
                Kp=0.3,  # Proportional gain
                Ki=0.01,  # Integral gain
                Kd=0.1,  # Derivative gain
                vmax=50  # Speed limit
            )
            
            # Yaw control
            self.yaw_pid = PIDControl(
                Kp=0.5,
                Ki=0.01,
                Kd=0.1,
                vmax=30
            )
        except ImportError:
            logging.warning("PIDControl not available, using simple proportional control")
            self.position_pid = None
            self.yaw_pid = None
    
    def land(self, tello, **kwargs):
        """Execute precision landing sequence."""
        self.finished = False
        self.landing_start_time = time.time()
        self.current_phase = "SEARCH"
        
        logging.info("Starting precision landing sequence")
        
        try:
            while not self.finished and (time.time() - self.landing_start_time) < self.max_landing_time:
                # Get current frame
                frame_read = kwargs.get('frame_read')
                if frame_read is None:
                    logging.error("No frame_read provided for precision landing")
                    break
                
                frame = frame_read.frame
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Process frame with tracker
                found, error_data, debug_info = self.tracker.process_frame(frame)
                
                if found:
                    self.last_detection_time = time.time()
                    self._handle_target_detected(tello, error_data, debug_info, frame)
                else:
                    self._handle_no_target(tello, frame)
                
                # Update visualization
                if hasattr(self.visual_protocol, 'update'):
                    self.visual_protocol.update(frame, debug_info)
                
                time.sleep(0.05)  # 20 FPS control loop
            
            if not self.finished:
                logging.warning("Landing timeout reached, executing emergency landing")
                tello.land()
                self.finished = True
                
        except Exception as e:
            logging.exception(f"Error during precision landing: {e}")
            tello.land()
            self.finished = True
    
    def _handle_target_detected(self, tello, error_data, debug_info, frame):
        """Handle target detection and execute appropriate landing phase."""
        if len(error_data) >= 5:  # Precision tracker returns 5 values
            error_x, error_y, yaw_error, distance, area_percentage = error_data
        else:
            # Fallback for basic trackers
            error_x, error_y = error_data[:2]
            yaw_error = 0
            distance = 100  # Default distance
            area_percentage = 5  # Default area percentage
        
        # Update debug info
        debug_info.update({
            "landing_phase": self.current_phase,
            "area_percentage": area_percentage,
            "distance": distance,
            "yaw_error": np.degrees(yaw_error)
        })
        
        # Phase transitions
        if self.current_phase == "SEARCH":
            self.current_phase = "ALIGN"
            logging.info("Target detected, transitioning to ALIGN phase")
        
        elif self.current_phase == "ALIGN":
            if (abs(error_x) < self.position_threshold and 
                abs(error_y) < self.position_threshold and 
                abs(yaw_error) < self.alignment_threshold):
                self.current_phase = "APPROACH"
                logging.info("Alignment achieved, transitioning to APPROACH phase")
        
        elif self.current_phase == "APPROACH":
            if area_percentage >= self.target_area_percentage and distance <= self.min_distance:
                self.current_phase = "TOUCHDOWN"
                logging.info("Touchdown conditions met, executing landing")
        
        # Execute phase-specific control
        if self.current_phase == "ALIGN":
            self._execute_alignment(tello, error_x, error_y, yaw_error)
        elif self.current_phase == "APPROACH":
            self._execute_approach(tello, error_x, error_y, yaw_error, distance, area_percentage)
        elif self.current_phase == "TOUCHDOWN":
            self._execute_touchdown(tello)
    
    def _handle_no_target(self, tello, frame):
        """Handle cases when no target is detected."""
        current_time = time.time()
        
        if (self.last_detection_time is not None and 
            current_time - self.last_detection_time > self.detection_timeout):
            # Lost target, return to search mode
            self.current_phase = "SEARCH"
            logging.warning("Target lost, returning to SEARCH phase")
        
        # Execute search pattern
        if self.current_phase == "SEARCH":
            self._execute_search_pattern(tello)
        
        # Draw search indicator on frame
        h, w = frame.shape[:2]
        cv2.putText(frame, "SEARCHING", (w//2 - 50, h//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def _execute_alignment(self, tello, error_x, error_y, yaw_error):
        """Execute alignment phase - center on target and align yaw."""
        # Use PID controllers if available
        if self.position_pid is not None:
            # PIDControl expects (error_x, error_y) and returns (vy, vx, 0, 0)
            pos_cmd = self.position_pid.compute_control((error_x, error_y))
            vy, vx, _, _ = pos_cmd
            tello.send_rc_control(int(vx), int(vy), 0, 0)
        else:
            # Simple proportional control
            x_cmd = np.clip(error_x * 0.3, -30, 30)
            y_cmd = np.clip(error_y * 0.3, -30, 30)
            tello.send_rc_control(int(x_cmd), int(y_cmd), 0, 0)
        
        # Yaw alignment
        if self.yaw_pid is not None:
            # For yaw, we need to create a simple proportional control since PIDControl is for x,y
            yaw_cmd = np.clip(yaw_error * 0.5, -20, 20)
            tello.send_rc_control(0, 0, 0, int(yaw_cmd))
        else:
            yaw_cmd = np.clip(yaw_error * 0.5, -20, 20)
            tello.send_rc_control(0, 0, 0, int(yaw_cmd))
    
    def _execute_approach(self, tello, error_x, error_y, yaw_error, distance, area_percentage):
        """Execute approach phase - spiral descent toward target."""
        # Calculate spiral movement
        self.spiral_angle += 0.1  # Increment spiral angle
        spiral_radius = self.spiral_radius * (self.spiral_tightening_rate ** (self.spiral_angle / (2*np.pi)))
        
        # Combine spiral movement with target centering
        spiral_x = spiral_radius * np.cos(self.spiral_angle)
        spiral_y = spiral_radius * np.sin(self.spiral_angle)
        
        # Blend spiral and centering commands
        blend_factor = min(area_percentage / self.target_area_percentage, 1.0)
        x_cmd = (1 - blend_factor) * spiral_x + blend_factor * error_x * 0.2
        y_cmd = (1 - blend_factor) * spiral_y + blend_factor * error_y * 0.2
        
        # Add downward movement
        z_cmd = -10  # Slow descent
        
        # Apply commands
        tello.send_rc_control(int(x_cmd), int(y_cmd), int(z_cmd), 0)
        
        logging.debug(f"Approach: area={area_percentage:.1f}%, distance={distance:.1f}cm")
    
    def _execute_approach_straight(self, tello, error_x, error_y, yaw_error, distance, area_percentage):
        """Execute straight-line approach (alternative to spiral)."""
        # Simple proportional control with downward movement
        x_cmd = np.clip(error_x * 0.2, -20, 20)
        y_cmd = np.clip(error_y * 0.2, -20, 20)
        z_cmd = -15  # Moderate descent
        
        tello.send_rc_control(int(x_cmd), int(y_cmd), int(z_cmd), 0)
    
    def _execute_search_pattern(self, tello):
        """Execute search pattern when target is not detected."""
        # Gentle circular search pattern
        search_angle = time.time() * 0.5  # Slow rotation
        x_cmd = 20 * np.cos(search_angle)
        y_cmd = 20 * np.sin(search_angle)
        
        tello.send_rc_control(int(x_cmd), int(y_cmd), 0, 0)
    
    def _execute_touchdown(self, tello):
        """Execute final touchdown phase."""
        logging.info("Executing touchdown")
        tello.land()
        self.finished = True 