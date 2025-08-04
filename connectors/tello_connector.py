"""connectors/tello_connector.py
---------------------------------------------------------------------
High‑level helper that wraps **djitellopy.Tello** and exposes only the
capabilities the rest of the project needs.  Keeps all SDK‑string magic
and resource clean‑up logic in one place.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import cv2
from djitellopy import Tello


class TelloConnector:  # pylint: disable=too-few-public-methods
    """Simple façade around *djitellopy.Tello*.

    Usage
    -----
    >>> tc = TelloConnector()
    >>> tc.connect()
    >>> frame = tc.get_frame()
    >>> tc.cleanup()
    """

    #: region‑of‑interest cropping (downward camera is 320×240 optical-flow; we crop top‑left
    CROPPED_H = 240
    CROPPED_W = 320

    def __init__(self, log_dir: str | Path | None = None) -> None:
        self.tello: Tello = None  # Will be initialized in connect()
        self.frame_read = None  # type: ignore[attr-defined]
        self._log_dir = Path(log_dir) if log_dir else None

    # ──────────────────────────────────────────────────────────────────
    # Setup / teardown
    # ──────────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Connect, start stream, and optionally record telemetry logs."""
        logging.info("Connecting to Tello …")

        # Initialize Tello with retry logic
        for attempt in range(3):
            try:
                self.tello = Tello()
                self.tello.connect()
                battery = self.tello.get_battery()
                logging.info("Tello battery: %s%%", battery)

                if battery < 20:
                    logging.warning("Low battery! Consider charging before flight.")

                break  # Success, exit retry loop

            except OSError as e:
                if "Address already in use" in str(e):
                    logging.error(f"Connection attempt {attempt + 1} failed: Port already in use")
                    if attempt < 2:
                        logging.info("This usually means another Tello application is running.")
                        logging.info("Try running: python3 utils/tello_cleanup.py")
                        logging.info("Waiting 2 seconds before retry...")
                        time.sleep(2)
                    else:
                        logging.error("All connection attempts failed. Please:")
                        logging.error("1. Run: python3 utils/tello_cleanup.py")
                        logging.error("2. Or restart your computer")
                        logging.error("3. Or restart the Tello drone")
                        raise
                else:
                    logging.error(f"Failed to connect to Tello: {e}")
                    raise
            except Exception as e:
                logging.error(f"Failed to connect to Tello: {e}")
                logging.info("Make sure the Tello drone is powered on and connected to WiFi")
                raise

        # Start stream with retry logic
        logging.info("Starting video stream...")
        for attempt in range(3):
            try:
                self.tello.streamon()
                time.sleep(1)  # Wait for stream to initialize

                self.frame_read = self.tello.get_frame_read()
                time.sleep(0.5)  # Wait for frame reader

                # Test if we can get a frame
                test_frame = self.frame_read.frame
                if test_frame is not None:
                    logging.info(f"✅ Stream started successfully! Frame shape: {test_frame.shape}")
                    break
                else:
                    logging.warning(f"Stream attempt {attempt + 1}: No frames received")

            except Exception as e:
                logging.warning(f"Stream attempt {attempt + 1} failed: {e}")

            if attempt < 2:
                logging.info("Retrying stream startup...")
                time.sleep(1)
        else:
            logging.error("Failed to start video stream after all attempts")

        # optional telemetry log to a CSV
        if self._log_dir:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            self.tello.set_telemetry_log(str(self._log_dir / "telemetry.csv"))

    # ──────────────────────────────────────────────────────────────────
    # Camera helpers
    # ──────────────────────────────────────────────────────────────────

    def set_downward_camera(self) -> None:
        """Switch to the downward-facing 320×240 optical-flow camera (Tello EDU only)."""
        self.tello.send_command_with_return("downvision 1")
        logging.debug("Downward-facing 320×240 optical-flow camera active.")

    def set_front_camera(self) -> None:
        self.tello.send_command_with_return("downvision 0")
        logging.debug("Front camera active.")

    # ──────────────────────────────────────────────────────────────────
    # Mission pads
    # ──────────────────────────────────────────────────────────────────

    def enable_mission_pads(self) -> None:
        self.tello.enable_mission_pads()
        self.tello.set_mission_pad_detection_direction(0)  # both directions
        logging.debug("Mission pad detection enabled.")

    def disable_mission_pads(self) -> None:
        try:
            self.tello.disable_mission_pads()
        except Exception:  # Tello EDU only – ignore on plain Tello
            pass

    # ──────────────────────────────────────────────────────────────────
    # Frame grab
    # ──────────────────────────────────────────────────────────────────

    def get_frame(self, crop_to_roi: bool = True) -> Optional[cv2.Mat]:
        """Return the latest video frame from the downward-facing 320×240 optical-flow camera, optionally cropped to 320×240."""
        frame = None if self.frame_read is None else self.frame_read.frame
        if frame is not None and crop_to_roi:
            frame = frame[0 : self.CROPPED_H, 0 : self.CROPPED_W]
        return frame

    # ──────────────────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """Turn off stream, land safely if still flying, and close OpenCV."""
        logging.info("Cleaning up Tello resources …")
        try:
            self.tello.streamoff()
        except Exception:  # stream may already be off
            pass
        self.disable_mission_pads()
        try:
            self.tello.end()
        except Exception:  # already ended
            pass
        cv2.destroyAllWindows()
        time.sleep(0.2)  # allow UDP socket to close
        logging.info("Tello cleanup done.")
