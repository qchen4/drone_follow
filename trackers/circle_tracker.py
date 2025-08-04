"""
CircleTracker implementation compatible with the current TrackerBase interface,
adapted from a legacy contour‑based circle detector that performed well on the user's target.

This version wraps the simple contour detection logic in the signature expected
by ``TrackerBase.process_frame`` and provides a ``draw_debug_info`` method to
visualise detections on the live feed.  The detection works by converting the
frame to grayscale, applying Gaussian blur, using Otsu’s threshold to binarise,
performing morphological closing to fill gaps, then extracting contours.  Each
contour is filtered by area and circularity, and the most circular candidate
within the specified area range is chosen as the detected circle.

Attributes
----------
area_range : tuple[int, int]
    Minimum and maximum contour area (in pixels) for candidate circles.
circularity_min : float
    Minimum circularity threshold (range 0–1) used to filter contours; a value
    closer to 1 requires more perfectly round shapes.

Returns
-------
found : bool
    ``True`` if a circle is detected; otherwise ``False``.
error : tuple[int, int, int]
    Pixel error vector (dx, dy, dz), where ``dz`` is always 0 because depth
    estimation is not performed.
debug : dict
    A dictionary with keys ``status``, ``bbox`` and ``previews``.  The ``status``
    string describes whether a circle was detected, ``bbox`` contains the
    bounding box of the detected circle (or ``None``), and ``previews`` is a list
    of annotated images showing the processing pipeline.  Additional keys
    ``center``, ``area`` and ``circularity`` are included when a circle is
    detected.
"""

from __future__ import annotations

import cv2
import numpy as np

from trackers.base_tracker import TrackerBase


class CircleTracker(TrackerBase):  # pylint: disable=too-few-public-methods
    """Contour‑based circle detector with ``TrackerBase`` interface."""

    def __init__(
        self,
        area_range: tuple[int, int] = (50, 5_000),
        circularity_min: float = 0.8,
    ) -> None:
        """
        Initialise a ``CircleTracker``.

        Parameters
        ----------
        area_range : tuple[int, int], optional
            The (min_area, max_area) range for candidate contours.  Contours
            outside this range are ignored.  Defaults to ``(50, 5000)``.
        circularity_min : float, optional
            The minimum circularity threshold (0–1).  A perfectly circular
            contour has circularity ~1.0.  Defaults to ``0.8``.
        """
        self.area_range = area_range
        self.circularity_min = circularity_min

    def process_frame(self, frame: np.ndarray, **kwargs) -> tuple[bool, tuple[int, int, int], dict]:
        """
        Analyse a frame and attempt to locate a circular target.

        This function implements a simple contour‑based circle detector:

        1. Convert the frame to grayscale and apply Gaussian blur.
        2. Compute a binary image using Otsu’s thresholding.
        3. Apply morphological closing to join fragmented regions.
        4. Find contours and filter them by area and circularity.
        5. Choose the most circular contour as the best candidate.

        The returned ``debug`` dictionary includes annotated preview images of
        each processing stage, which can be displayed by the visual protocol.

        Returns
        -------
        (found, error, debug)
            A tuple containing a boolean indicating detection, the
            (dx, dy, dz) error vector and a debug dictionary.
        """
        # Pre‑allocate debug preview list
        previews: list[np.ndarray] = []

        # 1. Grayscale conversion and Gaussian blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Otsu’s threshold to create a binary image
        _, binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # 3. Morphological closing to reduce holes and noise
        morph = cv2.morphologyEx(
            binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)
        )

        # 4. Find contours from the processed mask
        contours, _ = cv2.findContours(
            morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Track the best candidate by circularity
        best_circle: dict | None = None
        best_circularity = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter by area
            if area < self.area_range[0] or area > self.area_range[1]:
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter ** 2)
            # Filter by circularity
            if (
                circularity > self.circularity_min
                and circularity > best_circularity
            ):
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(cnt)
                best_circle = {
                    "cnt": cnt,
                    "center": (cx, cy),
                    "bbox": (x, y, w, h),
                    "circularity": circularity,
                    "area": area,
                }
                best_circularity = circularity

        # 5. Prepare debug previews
        # Original frame
        previews.append(self._label_img(frame.copy(), "Original"))
        # Grayscale
        previews.append(
            self._label_img(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), "Gray")
        )
        # Blurred
        previews.append(
            self._label_img(
                cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR), "Blurred"
            )
        )
        # Binary thresholded
        previews.append(
            self._label_img(
                cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), "Binary"
            )
        )
        # Morphology result
        previews.append(
            self._label_img(
                cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR), "Morph"
            )
        )

        h_img, w_img = frame.shape[:2]
        img_center = (w_img // 2, h_img // 2)

        if best_circle:
            # Annotate the best contour on a copy of the frame
            frame_annotated = frame.copy()
            cnt = best_circle["cnt"]
            bbox = best_circle["bbox"]
            cx, cy = best_circle["center"]
            # Draw contour outline and centre point
            cv2.drawContours(frame_annotated, [cnt], -1, (0, 255, 0), 2)
            cv2.circle(frame_annotated, (cx, cy), 5, (0, 0, 255), -1)
            # Include annotated image in previews
            previews.append(self._label_img(frame_annotated, "Circle Detected"))
            # Compute error relative to image centre
            error_x = cx - img_center[0]
            error_y = cy - img_center[1]
            error_z = 0
            debug = {
                "status": f"Circle detected (area: {best_circle['area']:.0f}, C: {best_circle['circularity']:.2f})",
                "bbox": bbox,
                "center": (cx, cy),
                "area": best_circle["area"],
                "circularity": best_circle["circularity"],
                "previews": previews,
            }
            return True, (error_x, error_y, error_z), debug
        else:
            # No circle found – include an annotated image explaining failure
            frame_annotated = frame.copy()
            previews.append(self._label_img(frame_annotated, "No Circle"))
            debug = {
                "status": "No Circle Detected",
                "bbox": None,
                "previews": previews,
            }
            return False, (0, 0, 0), debug

    def draw_debug_info(self, frame: np.ndarray, debug_info: dict) -> None:
        """
        Draw debug annotations on a frame.

        This method can be called by the visual protocol to overlay circle
        detection information on the live video feed.  It expects that the
        ``debug_info`` dictionary returned by ``process_frame`` contains a
        ``status`` key and, when a circle is detected, keys ``center``, ``bbox``,
        ``area`` and ``circularity``.
        """
        status = debug_info.get("status", "")
        # Always draw status text at the top-left
        cv2.putText(
            frame,
            status,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        # If a circle was detected, draw its bounding box and centre
        if status.startswith("Circle detected"):
            bbox = debug_info.get("bbox")
            center = debug_info.get("center")
            area = debug_info.get("area")
            circularity = debug_info.get("circularity")
            if bbox and center:
                x, y, w, h = bbox
                # Draw bounding rectangle
                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), (0, 255, 0), 2
                )
                # Draw centre point and cross
                cv2.drawMarker(
                    frame,
                    center,
                    (255, 0, 0),
                    markerType=cv2.MARKER_CROSS,
                    markerSize=10,
                    thickness=2,
                )
                # Add area and circularity text next to the box
                cv2.putText(
                    frame,
                    f"Area:{area:.0f} C:{circularity:.2f}",
                    (x + w + 10, y + h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                )

    @staticmethod
    def _label_img(img: np.ndarray, text: str) -> np.ndarray:
        """
        Draw a label on an image for preview purposes.

        The label is drawn at the top-left corner of the image using a green
        font.  This helper is used to create the ``previews`` list returned
        by ``process_frame``.
        """
        cv2.putText(
            img,
            text,
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        return img