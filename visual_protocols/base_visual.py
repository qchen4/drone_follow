from abc import ABC, abstractmethod

class VisualProtocol(ABC):
    """Strategy interface for GUI / logging visualisation."""

    @abstractmethod
    def show(self, frame, debug=None):
        pass

    @abstractmethod
    def show_previews(self, previews):
        pass

    @abstractmethod
    def close(self):
        pass