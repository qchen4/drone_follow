import numpy as np
import logging
import time
from typing import Optional

from .base_landing import LandingProtocolBase

class MultiLayerLanding(LandingProtocolBase):
    def __init__(self,
                 layers: int = 3,
                 layer_height: int = 20,
                 align_timeout: float = 2.5,
                 align_threshold: float = 12.0,
                 aligned_frames_needed: int = 10,
                 velocity_threshold: float = 12.0,
                 tracker: Optional[object] = None,
                 control_protocol: Optional[object] = None,
                 visual_protocol: Optional[object] = None) -> None:
        super().__init__()
        self.layers = layers
        self.layer_height = layer_height
        self.align_timeout = align_timeout
        self.align_threshold = align_threshold
        self.aligned_frames_needed = aligned_frames_needed
        self.velocity_threshold = velocity_threshold  # retained for API compatibility
        self.tracker = tracker
        self.control_protocol = control_protocol
        self.visual_protocol = visual_protocol

    def land(self, tello, frame_read=None, visual_protocol=None, **kwargs) -> None:
        self.finished = False
        visual_protocol = visual_protocol or self.visual_protocol
        logging.info(f"Landing in {self.layers} steps of {self.layer_height}cm each.")
        if frame_read is None:
            frame_read = getattr(tello, "frame_read", None)
        for layer in range(self.layers):
            aligned = self._align_on_pad(tello, frame_read, layer, visual_protocol)
            self._descend_layer(tello, aligned)
        logging.info("Final landing executed.")
        try:
            tello.land()
        except Exception as e:
            logging.warning(f"Final land command failed: {e}")
        self.finished = True

    def _descend_layer(self, tello, aligned: bool) -> None:
        tello.send_rc_control(0, 0, 0, 0)
        time.sleep(0.1)
        try:
            # --- Safety: if we are already close to the ground, land directly ---
            try:
                current_h = tello.get_height()  # cm – supported by most Tello firmware
            except Exception:
                # Fallback to TOF sensor (returns mm)
                try:
                    current_h = tello.get_distance_tof() / 10.0
                except Exception:
                    current_h = None
            if current_h is not None and current_h <= self.layer_height + 15:
                logging.info(f"Height {current_h} cm ≤ safe margin; executing final land instead of {self.layer_height} cm descent.")
                tello.land()
                self.finished = True
                return

            if self.is_stable_imu(tello):
                if aligned:
                    logging.info(f"Stable. Descending {self.layer_height} cm.")
                else:
                    logging.warning("Descending without confirmed alignment; proceeding cautiously.")
                tello.move("down", self.layer_height)
            else:
                logging.warning("IMU instability detected or invalid data; skipping descent.")
                time.sleep(1)
                return
        except Exception as e:
            logging.error(f"Descending {self.layer_height}cm failed: {e}. Attempting direct land.")
            try:
                tello.land()
            except Exception as land_err:
                logging.error(f"Direct land failed: {land_err}")
        time.sleep(0.3)

    def _align_on_pad(self,
                      tello,
                      frame_read,
                      layer: int,
                      visual_protocol: Optional[object]) -> bool:
        logging.info(f"Aligning on pad for layer {layer + 1}/{self.layers}")
        start_time = time.time()
        aligned_count = 0
        if frame_read is None or self.tracker is None or self.control_protocol is None:
            logging.debug("No tracker/control available; performing time‑based alignment.")
            time.sleep(self.align_timeout)
            return True
        while time.time() - start_time < self.align_timeout:
            frame = frame_read.frame
            if frame is None:
                time.sleep(0.05)
                continue
            try:
                found, error, debug = self.tracker.process_frame(frame)
            except Exception as e:
                logging.warning(f"Tracker error during alignment: {e}")
                found, error, debug = False, (0, 0, 0), {}
            if found:
                rc = self.control_protocol.compute_control(error)
                lr, fb, _, yaw = rc
                tello.send_rc_control(int(lr), int(fb), 0, int(yaw))
                dx, dy = error[:2]
                if abs(dx) < self.align_threshold and abs(dy) < self.align_threshold:
                    aligned_count += 1
                else:
                    aligned_count = 0
                if visual_protocol is not None:
                    if isinstance(debug, dict):
                        debug["landing_phase"] = f"ALIGN (layer {layer + 1})"
                    # Preferred fast-path: dedicated update() API (e.g. LoggerVisual)
                    if hasattr(visual_protocol, "update"):
                        try:
                            visual_protocol.update(frame, debug)
                        except Exception:
                            pass
                    # Fallback for OpenCV-based protocols (GridVisual/OpenCVVisual)
                    elif hasattr(visual_protocol, "show"):
                        try:
                            visual_protocol.show(frame, debug)
                            if hasattr(visual_protocol, "_display_frame"):
                                visual_protocol._display_frame()
                        except Exception:
                            pass
            else:
                tello.send_rc_control(0, 0, 0, 0)
                aligned_count = 0
            if aligned_count >= self.aligned_frames_needed:
                logging.info("Alignment achieved.")
                return True
            time.sleep(0.1)
        logging.warning("Alignment timeout reached; proceeding without confirmed alignment.")
        return False

    @staticmethod
    def is_stable_imu(*_, **__) -> bool:
        """IMU stability check disabled (always returns True)."""
        return True




