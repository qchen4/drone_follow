# trackers/aruco_tracker.py

import cv2
import numpy as np
from .base_tracker import TrackerBase

class ArucoTracker(TrackerBase):
    def __init__(self, marker_size=15.0, marker_dict=cv2.aruco.DICT_4X4_50):
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
        self.params.minOtsuStdDev = 5.0
        self.params.errorCorrectionRate = 0.6
        self.marker_size = marker_size  # Marker size in cm

    def process_frame(self, frame, **kwargs):
        detector = cv2.aruco.ArucoDetector(self.dictionary, self.params)
        corners, ids, _ = detector.detectMarkers(frame)

        debug_info = {"status": "No Marker Detected"}
        if ids is not None and len(ids) > 0:
            corner = corners[0][0]
            center = np.mean(corner, axis=0)
            frame_center = np.array([frame.shape[1]/2, frame.shape[0]/2])
            error_x, error_y = center - frame_center

            debug_info = {
                "status": f"ArUco Marker {ids[0][0]} detected",
                "marker_id": int(ids[0][0]),
                "center": center.tolist()
            }

            return True, (error_x, error_y, 0), debug_info

        return False, (0, 0, 0), debug_info
