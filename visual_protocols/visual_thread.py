# visual_protocols/visual_thread.py

from threading import Thread
import logging
import time

class VisualThread(Thread):
    def __init__(self, visual_protocol):
        super().__init__()
        self.visual_protocol = visual_protocol
        self.frame = None
        self.debug = None
        self.running = True

    def run(self):
        logging.info("Visualization thread started.")
        while self.running:
            if self.frame is not None:
                try:
                    # For OpenCV protocols, only buffer the frame
                    if hasattr(self.visual_protocol, '_frame_buffer'):
                        # Just store the frame, let main thread handle display
                        self.visual_protocol.show(self.frame, self.debug)
                    else:
                        # For non-OpenCV protocols (like console logger), display directly
                        self.visual_protocol.show(self.frame, self.debug)
                        if self.debug and self.debug.get("previews"):
                            self.visual_protocol.show_previews(self.debug["previews"])
                except Exception as e:
                    logging.exception(f"Visualization error: {e}")
                finally:
                    self.frame = None
            time.sleep(0.01)

    def stop(self):
        self.running = False
        logging.info("Visualization thread stopping.")
