from .base_visual import VisualProtocol

class LoggerVisualProtocol(VisualProtocol):

    def show(self, frame, debug=None):
        if debug:
            print(f"[Visual] {debug.get('status', '')}  {debug.get('bbox', '')}")  # noqa: T201


    def show_previews(self, previews):  # noqa: D401
        pass

    def close(self):  # noqa: D401
        pass
