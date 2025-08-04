import cv2
import numpy as np
import supervision as sv
from trackers.base_tracker import TrackerBase

class DarkRectTracker(TrackerBase):
    """Detects the largest dark rectangle on bright background."""

    def __init__(self):
        self.box_annot = sv.RoundBoxAnnotator(thickness=2)
        self.label_annot = sv.LabelAnnotator(text_scale=1)

    # ------------------------------------------------------------------
    def process_frame(self, frame, **kwargs):  # noqa: D401
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE,
                                 cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
        best_rect, center = self._find_best_rect(morph)

        debug = {}
        if not center:
            debug["status"] = "NO RECT"
            return False, (0, 0, 0), debug

        x, y, w, h = best_rect
        h_img, w_img = frame.shape[:2]
        img_center = (w_img // 2, h_img // 2)
        err_x = center[0] - img_center[0]
        err_y = center[1] - img_center[1]

        debug.update(status="DARK RECT", bbox=best_rect)
        return True, (err_x, err_y, 0), debug

    # ------------------------------------------------------------------
    @staticmethod
    def _find_best_rect(binary):
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_rect = None
        center = None
        max_area = 0
        h_img, w_img = binary.shape
        img_area = h_img * w_img
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (500 < area < 0.6 * img_area):
                continue
            epsilon = 0.03 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) != 4:
                continue
            x, y, w, h = cv2.boundingRect(approx)
            aspect = w / h
            if 0.5 < aspect < 2.0 and area > max_area:
                max_area = area
                best_rect = (x, y, w, h)
                center = (x + w // 2, y + h // 2)
        return best_rect, center
