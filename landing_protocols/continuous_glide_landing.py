"""
Continuous glide landing protocol for the Tello drone.

This landing strategy continuously descends while the tracker keeps the
drone centred over a target (e.g. a food tray).  Instead of stepping
down in fixed increments, the vertical velocity is adjusted smoothly
based on how well the drone is aligned.  When the distance to the
target is small, the descent rate increases; when misaligned, the
descent rate decreases.  The landing finishes automatically when the
barometer or time‑of‑flight sensor indicates the drone is on the ground.

The class exposes a `finished` attribute to signal completion to
external callers (e.g. for updating the video feed during descent).
"""

import time
import logging
from typing import Optional, Tuple

import numpy as np

from landing_protocols.base_landing import LandingProtocolBase
from trackers.base_tracker import TrackerBase
from control_protocols.base_control import DroneControlLaw


class ContinuousGlideLanding(LandingProtocolBase):
    """Landing protocol that continuously glides down while tracking.

    Parameters
    ----------
    descent_gain : float
        Coefficient that scales the descent velocity based on how well
        the drone is centred.  Smaller values make the descent more
        conservative.  Typical range is 0.1–0.5.
    min_vz : int
        Minimum downward speed (in cm/s) when the drone is well centred.
        The Tello expects the up/down component of RC control to be in
        the range -100..100 (positive values move up).  Downward
        velocities are negative.
    max_vz : int
        Maximum downward speed (in cm/s) when the drone is far off
        centre.  This caps the descent rate to avoid dropping too fast.
    height_threshold : float
        Altitude (in cm) below which the drone is considered to have
        landed.  When the Tello's time‑of‑flight sensor reads below
        this threshold, the motors are stopped and the landing
        procedure ends.
    timeout : float
        Maximum time (in seconds) allowed for the landing.  If this
        duration is exceeded, the landing ends regardless of the drone's
        height.
    tracker : TrackerBase
        The tracker used to compute the horizontal error to the target.
    control_protocol : DroneControlLaw
        The control protocol that converts an error vector into RC
        commands for horizontal movement (roll, pitch, yaw).
    """

    def __init__(
        self,
        descent_gain: float = 0.3,
        min_vz: int = 10,
        max_vz: int = 25,
        height_threshold: float = 20.0,
        timeout: float = 30.0,
        tracker: Optional[TrackerBase] = None,
        control_protocol: Optional[DroneControlLaw] = None,
    ) -> None:
        super().__init__()
        self.descent_gain = descent_gain
        self.min_vz = min_vz
        self.max_vz = max_vz
        self.height_threshold = height_threshold
        self.timeout = timeout
        self.tracker = tracker
        self.control_protocol = control_protocol

    def _compute_descent_speed(self, error: Tuple[float, float]) -> int:
        """Compute the downward velocity component based on horizontal error.

        The error tuple is (dx, dy) measured in pixels (or cm) where
        zero indicates perfect alignment.  We compute an error magnitude
        and map it to a negative velocity: near zero error yields the
        maximum descent rate (more negative), while large error yields
        slower descent.  The speed is clamped between ``-max_vz`` and
        ``-min_vz``.
        """
        dx, dy = error
        # Euclidean distance from centre
        mag = float(np.hypot(dx, dy))
        # Normalise so that error of 0 yields 1.0 and large error yields 0.0
        normalised = max(0.0, 1.0 - mag / 100.0)
        # Interpolate between min_vz and max_vz and convert to negative for downwards
        desired_speed = self.min_vz + (self.max_vz - self.min_vz) * normalised
        return -int(desired_speed)

    def land(self, tello, frame_read=None, visual_protocol=None, **kwargs) -> None:
        """Execute the continuous glide landing.

        The method enters a loop where it continuously reads frames,
        calculates horizontal error, computes RC commands using the
        supplied control protocol, adds a downward component computed
        from the error, and sends the command.  The loop exits when the
        drone is sufficiently low (as indicated by the time‑of‑flight
        sensor) or when the timeout expires.  At exit, ``self.finished``
        is set to ``True``.
        """
        if self.tracker is None or self.control_protocol is None:
            logging.warning("Continuous glide landing requires a tracker and a control protocol.")
            self.finished = True
            return

        if frame_read is None:
            frame_read = getattr(tello, 'frame_read', None)

        self.finished = False
        start_time = time.time()
        logging.info("Starting continuous glide landing…")

        while True:
            frame = frame_read.frame if frame_read is not None else None
            if frame is not None:
                found, error, _ = self.tracker.process_frame(frame)
                if found:
                    rc = self.control_protocol.compute_control(error)
                else:
                    rc = (0, 0, 0, 0)  # hover if target lost
                vz = self._compute_descent_speed(error[:2] if found else (np.inf, np.inf))
                lr, fb, _, yaw = rc
                tello.send_rc_control(lr, fb, vz, yaw)
            else:
                tello.send_rc_control(0, 0, 0, 0)

            # Check altitude using time‑of‑flight sensor; land if below threshold
            try:
                height = tello.get_distance_tof()
                if height <= self.height_threshold:
                    logging.info(f"Height {height:.1f} cm below threshold; executing final landing.")
                    tello.send_rc_control(0, 0, 0, 0)
                    tello.land()
                    break
            except Exception as e:
                logging.debug(f"TOF read failed: {e}")

            if time.time() - start_time > self.timeout:
                logging.warning("Continuous glide landing timeout expired; initiating final landing.")
                tello.send_rc_control(0, 0, 0, 0)
                tello.land()
                break

            time.sleep(0.05)

        self.finished = True
        logging.info("Continuous glide landing complete.")
