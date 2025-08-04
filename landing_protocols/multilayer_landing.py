import numpy as np
import logging
import time
from .base_landing import LandingProtocolBase




class MultiLayerLanding(LandingProtocolBase):
    def __init__(self, layers=3, layer_height=20, align_timeout=2.5,
                 align_threshold=12, aligned_frames_needed=10,
                 velocity_threshold=12, tracker=None,
                 control_protocol=None, visual_protocol=None):

        self.layers = layers
        self.layer_height = layer_height
        self.align_timeout = align_timeout
        self.align_threshold = align_threshold
        self.aligned_frames_needed = aligned_frames_needed
        self.velocity_threshold = velocity_threshold
        self.tracker = tracker
        self.control_protocol = control_protocol
        self.visual_protocol = visual_protocol

    def land(self, tello, frame_read=None, visual_protocol=None, **kwargs):
        visual_protocol = visual_protocol or self.visual_protocol
        logging.info(f"Landing in {self.layers} steps of {self.layer_height}cm each.")
        for layer in range(self.layers):
            aligned = self._align_on_pad(tello, frame_read, layer, visual_protocol)
            self._descend_layer(tello, aligned)
        logging.info("Final landing executed.")
        tello.land()

    def _descend_layer(self, tello, aligned):
        tello.send_rc_control(0, 0, 0, 0)
        time.sleep(0.1)
        if self.is_stable_imu(tello):
            logging.info(f"Stable IMU. Descending {self.layer_height}cm.")
            tello.move('down', self.layer_height)
        else:
            logging.warning("IMU instability detected, delaying descent.")
            time.sleep(1)
        time.sleep(0.3)

    def is_stable_imu(self, tello, accel_threshold=0.1):
        """Check if the drone's IMU indicates stable flight."""
        try:
            imu = tello.get_imu()
            acceleration = np.linalg.norm([imu.ax, imu.ay, imu.az])
            logging.debug(f"IMU Acceleration: {acceleration:.3f}")
            return acceleration < accel_threshold
        except Exception as e:
            logging.warning(f"Could not read IMU data: {e}")
            return True  # Assume stable if we can't read IMU

    def _align_on_pad(self, tello, frame_read, layer, visual_protocol):
        """Align the drone on the landing pad for the current layer."""
        logging.info(f"Aligning on pad for layer {layer + 1}")
        # Simple alignment - in a real implementation, this would use the tracker
        # to align the drone with the target
        time.sleep(0.5)  # Give time for alignment
        return True  # Assume aligned for now
