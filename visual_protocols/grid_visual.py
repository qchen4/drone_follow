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

    def initialize_window(self) -> None:
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def show(self, frame: np.ndarray, debug: Dict[str, Any]) -> None:
        """Render the composite grid image to the OpenCV window."""
        try:
            rows, cols = self.grid_shape
            canvas = np.zeros((rows * self.cell_h, cols * self.cell_w, 3), dtype=np.uint8)
            for r in range(rows):
                for c in range(cols):
                    idx = r * cols + c
                    cell = self._render_cell(idx, frame, debug)
                    if cell is None:
                        continue
                    cell_resized = cv2.resize(cell, (self.cell_w, self.cell_h))
                    y0 = r * self.cell_h
                    x0 = c * self.cell_w
                    canvas[y0:y0 + self.cell_h, x0:x0 + self.cell_w] = cell_resized
            cv2.imshow(self.window_name, canvas)
        except Exception as e:
            logging.exception(f"GridVisualProtocol show error: {e}")

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
            # Tracker view: draw up to 3 candidate circles and the final bbox
            view = frame.copy()
            candidates = debug.get('candidates', [])
            colours = [(255, 0, 0), (0, 255, 255), (0, 0, 255)]
            for i, cand in enumerate(candidates[:3]):
                cx, cy, radius, score = cand
                colour = colours[i % len(colours)]
                cv2.circle(view, (int(cx), int(cy)), int(radius), colour, 2)
                cv2.putText(view, f"r={int(radius)}", (int(cx), int(cy) - 5),
                            cv2.FONT_HERSHEY_PLAIN, 0.8, colour, 1)
            
            bbox = debug.get('bbox', None)
            if bbox:
                x, y, w, h = map(int, debug['bbox'])
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
