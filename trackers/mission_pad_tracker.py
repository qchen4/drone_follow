from __future__ import annotations

import logging
from trackers.base_tracker import TrackerBase

# We depend on the `TelloConnector` wrapper to supply a `.tello` attr
# with djitellopy's original methods.

class MissionPadTracker(TrackerBase):
    """Tracker using DJI Tello SDK mission-pad distance values (cm)."""

    def __init__(self, tello_connector, target_height: int = 100):
        self.tello = tello_connector.tello
        self.target_height = target_height

    # ------------------------------------------------------------------
    def process_frame(self, frame, **kwargs):  # noqa: D401
        pad_id = self.tello.get_mission_pad_id()
        debug = {"pad_id": pad_id}

        if pad_id == -1:
            debug["status"] = "NO PAD"
            return False, (0, 0, 0), debug

        x = self.tello.get_mission_pad_distance_x()  # cm, + right
        y = self.tello.get_mission_pad_distance_y()  # cm, + forward
        z = self.tello.get_mission_pad_distance_z()  # cm, + down
        err_x, err_y = x, y
        err_z = z - self.target_height

        debug.update(status="PAD DETECTED", pad_xyz=(x, y, z))
        return True, (err_x, err_y, err_z), debug