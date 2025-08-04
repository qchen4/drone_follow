# trackers/precision_aruco_tracker.py

import cv2
import numpy as np
from .base_tracker import TrackerBase

class PrecisionArucoTracker(TrackerBase):
    def __init__(self, marker_size=15.0, marker_dict=cv2.aruco.DICT_4X4_50, 
                 camera_matrix=None, dist_coeffs=None):
        self.dictionary = cv2.aruco.getPredefinedDictionary(marker_dict)
        self.params = cv2.aruco.DetectorParameters()
        
        # Adjust parameters for better detection
        self.params.adaptiveThreshWinSizeMin = 3
        self.params.adaptiveThreshWinSizeMax = 23
        self.params.adaptiveThreshWinSizeStep = 10
        self.params.adaptiveThreshConstant = 7
        self.params.minMarkerPerimeterRate = 0.03
        self.params.maxMarkerPerimeterRate = 4.0
        self.params.polygonalApproxAccuracyRate = 0.03
        self.params.minCornerDistanceRate = 0.05
        self.params.minDistanceToBorder = 3
        self.params.minOtsuStdDev = 5.0
        self.params.perspectiveRemovePixelPerCell = 4
        self.params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        self.params.maxErroneousBitsInBorderRate = 0.35
        self.params.errorCorrectionRate = 0.6
        
        self.marker_size = marker_size  # Marker size in cm
        
        # Camera calibration parameters (if not provided, use default Tello camera)
        if camera_matrix is None:
            # Default Tello camera matrix (approximate)
            self.camera_matrix = np.array([
                [800, 0, 320],
                [0, 800, 240],
                [0, 0, 1]
            ], dtype=np.float32)
        else:
            self.camera_matrix = camera_matrix
            
        if dist_coeffs is None:
            # Default distortion coefficients (minimal distortion)
            self.dist_coeffs = np.zeros((4, 1), dtype=np.float32)
        else:
            self.dist_coeffs = dist_coeffs

    def process_frame(self, frame, **kwargs):
        detector = cv2.aruco.ArucoDetector(self.dictionary, self.params)
        corners, ids, _ = detector.detectMarkers(frame)

        debug_info = {"status": "No Marker Detected"}
        
        if ids is not None and len(ids) > 0:
            corner = corners[0][0]
            center = np.mean(corner, axis=0)
            frame_center = np.array([frame.shape[1]/2, frame.shape[0]/2])
            
            # Calculate lateral error
            error_x, error_y = center - frame_center
            
            # Estimate pose and calculate relative orientation
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, self.marker_size, self.camera_matrix, self.dist_coeffs
            )
            
            if rvecs is not None and tvecs is not None:
                rvec = rvecs[0][0]
                tvec = tvecs[0][0]
                
                # Convert rotation vector to rotation matrix
                R, _ = cv2.Rodrigues(rvec)
                
                # Calculate yaw angle (rotation around Z-axis)
                yaw = np.arctan2(R[1, 0], R[0, 0])
                
                # Calculate distance to marker
                distance = np.linalg.norm(tvec)
                
                # Calculate marker area percentage in frame
                marker_area = cv2.contourArea(corner.astype(np.int32))
                frame_area = frame.shape[0] * frame.shape[1]
                area_percentage = (marker_area / frame_area) * 100
                
                # Calculate marker size in pixels for landing decision
                marker_width_px = np.linalg.norm(corner[1] - corner[0])
                marker_height_px = np.linalg.norm(corner[3] - corner[0])
                marker_size_px = max(marker_width_px, marker_height_px)
                
                debug_info = {
                    "status": f"ArUco Marker {ids[0][0]} detected",
                    "marker_id": int(ids[0][0]),
                    "center": center.tolist(),
                    "distance": float(distance),
                    "yaw": float(yaw),
                    "area_percentage": float(area_percentage),
                    "marker_size_px": float(marker_size_px),
                    "pose": {
                        "translation": tvec.tolist(),
                        "rotation": rvec.tolist()
                    }
                }

                return True, (error_x, error_y, yaw, distance, area_percentage), debug_info

        return False, (0, 0, 0, 0, 0), debug_info

    def draw_debug_info(self, frame, debug_info):
        """Draw debug information on the frame."""
        if debug_info.get("status", "").startswith("ArUco Marker"):
            # Draw marker corners
            if "center" in debug_info:
                center = np.array(debug_info["center"])
                cv2.circle(frame, tuple(center.astype(int)), 5, (0, 255, 0), -1)
            
            # Draw distance and angle info
            if "distance" in debug_info:
                distance = debug_info["distance"]
                yaw = debug_info.get("yaw", 0)
                area_pct = debug_info.get("area_percentage", 0)
                
                text_lines = [
                    f"Distance: {distance:.1f}cm",
                    f"Yaw: {np.degrees(yaw):.1f}deg",
                    f"Area: {area_pct:.1f}%"
                ]
                
                for i, line in enumerate(text_lines):
                    cv2.putText(frame, line, (10, 30 + i*25), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2) 