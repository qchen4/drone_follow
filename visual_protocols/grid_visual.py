# visual_protocols/grid_visual_protocol.py
"""
Grid-based visual protocol for multi-pane debugging.

This class arranges multiple diagnostic views into a grid.  Each cell can
display a different view: the raw frame, tracker candidates, alignment
indicators, or a text panel.  You can customise the layout by setting
grid_shape and cell_size and by overriding _render_cell().
"""

import cv2
import numpy as np
import logging
from typing import Dict, Tuple, Any
from visual_protocols.base_visual import VisualProtocol

class GridVisualProtocol(VisualProtocol):
    """Display multiple diagnostics in a grid layout."""

    def __init__(
        self,
        window_name: str = "Tello Debug Grid",
        grid_shape: Tuple[int, int] = (2, 2),
        cell_size: Tuple[int, int] = (320, 240),
    ) -> None:
        self.window_name = window_name
        self.grid_shape = grid_shape
        self.cell_w, self.cell_h = cell_size
        self.window_created = False
        self._frame_buffer = None
        self._debug_buffer = None

    def initialize_window(self) -> None:
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.cell_w * self.grid_shape[1], self.cell_h * self.grid_shape[0])
            self.window_created = True
            logging.info(f"Grid window '{self.window_name}' created successfully")
        except Exception as e:
            logging.error(f"Failed to create grid window: {e}")

    def close(self) -> None:
        """Destroy this protocol's window (required by VisualProtocol)."""
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            cv2.destroyAllWindows()

    def show_previews(self, previews: list[np.ndarray]) -> None:
        """
        Display a list of preview images in a grid montage.
        If no previews exist, do nothing.
        """
        if not previews:
            return
        n = len(previews)
        cols = int(np.ceil(np.sqrt(n)))
        rows = int(np.ceil(n / cols))
        h, w = previews[0].shape[:2]
        montage = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
        for idx, img in enumerate(previews):
            r = idx // cols
            c = idx % cols
            y0, x0 = r * h, c * w
            img_resized = cv2.resize(img, (w, h)) if img.shape[:2] != (h, w) else img
            montage[y0:y0 + h, x0:x0 + w] = img_resized
        cv2.imshow(f"{self.window_name} Previews", montage)

    def show(self, frame: np.ndarray, debug: Dict[str, Any]) -> None:
        """Store frame and debug info for the main thread to display."""
        if frame is None:
            return

        # Store frame and debug info for the main thread to display
        self._frame_buffer = frame.copy()
        self._debug_buffer = debug

    def _display_frame(self):
        """Actually display the frame (called from main thread)."""
        if self._frame_buffer is None:
            return

        if not self.window_created:
            logging.warning("Grid window not created yet")
            return

        try:
            rows, cols = self.grid_shape
            canvas = np.zeros((rows * self.cell_h, cols * self.cell_w, 3), dtype=np.uint8)
            for r in range(rows):
                for c in range(cols):
                    idx = r * cols + c
                    cell = self._render_cell(idx, self._frame_buffer, self._debug_buffer)
                    if cell is None:
                        continue
                    cell_resized = cv2.resize(cell, (self.cell_w, self.cell_h))
                    y0 = r * self.cell_h
                    x0 = c * self.cell_w
                    canvas[y0:y0 + self.cell_h, x0:x0 + self.cell_w] = cell_resized
            cv2.imshow(self.window_name, canvas)
            cv2.waitKey(1)  # Update window
        except Exception as e:
            logging.exception(f"GridVisualProtocol display error: {e}")

    def _render_cell(self, index: int, frame: np.ndarray, debug: Dict[str, Any]) -> np.ndarray | None:
        """
        Return an image for the given cell index.  The default 2×2 layout is:

        0: raw frame
        1: tracker view with top candidates
        2: alignment view with crosshairs
        3: text panel with debug info

        Override this method to customise other cells or different grid sizes.
        """
        if index == 0:
            # Raw frame
            return frame.copy()

        elif index == 1:
            # Tracker view: draw candidate circles and bounding box
            view = frame.copy()
            for i, cand in enumerate(debug.get('candidates', [])[:3]):
                cx, cy, radius, score = cand
                colour = [(255,0,0),(0,255,255),(0,0,255)][i % 3]
                cv2.circle(view, (int(cx), int(cy)), int(radius), colour, 2)
                cv2.putText(view, f"r={int(radius)}", (int(cx), int(cy)-5),
                            cv2.FONT_HERSHEY_PLAIN, 0.8, colour, 1)
            # Draw bounding box only if present and not None
            bbox = debug.get('bbox')
            if bbox:
                x, y, w, h = map(int, bbox)
                cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
            return view

        elif index == 2:
            # Alignment view: blue cross at image centre; green cross at target centre; connecting line
            view = frame.copy()
            h, w = view.shape[:2]
            centre_x, centre_y = w // 2, h // 2
            cv2.drawMarker(view, (centre_x, centre_y), (255, 0, 0),
                           markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
            if 'center' in debug:
                tx, ty = map(int, debug['center'])
                cv2.drawMarker(view, (tx, ty), (0, 255, 0),
                               markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
                cv2.line(view, (centre_x, centre_y), (tx, ty), (0, 255, 0), 1)
            return view

        elif index == 3:
            # Text panel: list all debug key/value pairs except large lists
            panel = np.zeros((self.cell_h, self.cell_w, 3), dtype=np.uint8)
            y = 20
            for k, v in debug.items():
                if k in ('previews', 'candidates'):
                    continue
                text = f"{k}: {v}"
                cv2.putText(panel, text, (5, y), cv2.FONT_HERSHEY_SIMPLEX,
                            0.45, (0, 255, 255), 1)
                y += 18
                if y > self.cell_h - 10:
                    break
            return panel

        # For larger grids, extra cells can be implemented here
        return None


