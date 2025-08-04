# landing_protocols/base_landing.py
from abc import ABC, abstractmethod

class LandingProtocolBase(ABC):
    """Common interface for landing strategies."""

    @abstractmethod
    def land(self, tello, **kwargs):
        """Execute landing.  May use *frame_read*, *visual_protocol*, etc."""
        raise NotImplementedError