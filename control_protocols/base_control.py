# control_protocols/base_control.py
from abc import ABC, abstractmethod

class DroneControlLaw(ABC):
    """Abstract base for P / PI / PID etc."""

    @abstractmethod
    def compute_control(self, error, **kwargs):
        """Return RC tuple ``(lr, fb, ud, yaw)`` from error vector."""
        raise NotImplementedError
