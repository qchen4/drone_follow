import cv2
import numpy as np
from trackers.base_tracker import TrackerBase

class ColorPatchTracker(TrackerBase):
    """Detects a red rectangle on yellow background & returns pixel error."""

    def process_frame(self, frame, **kwargs):  # noqa: D401
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = self._red_mask(hsv)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        debug = {}
        if not contours:
            debug["status"] = "NO PATCH"
            return False, (0, 0, 0), debug

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 100:  # tiny noise
            debug["status"] = "NO PATCH"
            return False, (0, 0, 0), debug

        x, y, w, h = cv2.boundingRect(largest)
        best_center = (x + w // 2, y + h // 2)
        h_img, w_img = frame.shape[:2]
        img_center = (w_img // 2, h_img // 2)

        err_x = best_center[0] - img_center[0]
        err_y = best_center[1] - img_center[1]

        debug.update(status="RED RECT DETECTED", bbox=(x, y, w, h))
        return True, (err_x, err_y, 0), debug

    # ------------------------------------------------------------------
    @staticmethod
    def _red_mask(hsv):
        lower1 = np.array([0, 80, 80])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([160, 80, 80])
        upper2 = np.array([179, 255, 255])
        mask  = cv2.inRange(hsv, lower1, upper1)
        mask |= cv2.inRange(hsv, lower2, upper2)
        return mask
