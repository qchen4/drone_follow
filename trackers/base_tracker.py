# trackers/base_tracker.py
from abc import ABC, abstractmethod

class TrackerBase(ABC):
    """Abstract vision tracker – returns success flag, 3‑tuple error, and debug dict."""

    @abstractmethod
    def process_frame(self, frame, **kwargs):
        """Analyse *frame* and return ``(found, (err_x, err_y, err_z), debug_info)``."""
        raise NotImplementedError

# control_protocols/base_control.py
from abc import ABC, abstractmethod