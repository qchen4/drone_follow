# main.py

import logging
import time
import cv2

from connectors.tello_connector import TelloConnector
from trackers.base_tracker import TrackerBase
from control_protocols.base_control import DroneControlLaw
from landing_protocols.base_landing import LandingProtocolBase
from visual_protocols.base_visual import VisualProtocol
from visual_protocols.visual_thread import VisualThread
from utils.logging_utils import setup_logger
from utils.setup_utils import (
    select_tracker,
    select_control_protocol,
    configure_landing,
    select_visual_protocol
)
from control_protocols.pid_control import PIDControl

def main():
    setup_logger()
    logging.info("Drone application initialized.")

    tello_connector = TelloConnector()
    tello_connector.connect()

    tracker: TrackerBase = select_tracker(tello_connector)
    control_protocol: DroneControlLaw = select_control_protocol()
    visual_protocol: VisualProtocol = select_visual_protocol()
    landing_protocol: LandingProtocolBase = configure_landing(tracker, control_protocol, visual_protocol)

    follower = TelloTargetFollower(
        tello_connector,
        tracker,
        landing_protocol,
        control_protocol,
        visual_protocol
    )

    input("\nReady to fly! Press Enter to start the mission...")
    follower.run()
    post_flight_cleanup(tello_connector)


class TelloTargetFollower:
    def __init__(self, tello_connector, tracker, landing_protocol,
                 control_protocol, visual_protocol,
                 takeoff_height=30, target_height=30, timeout=40):

        self.tello_connector = tello_connector
        self.tello = tello_connector.tello
        self.tracker = tracker
        self.landing_protocol = landing_protocol
        self.control_protocol = control_protocol
        self.visual_protocol = visual_protocol

        self.takeoff_height = takeoff_height
        self.target_height = target_height
        self.timeout = timeout

        self.running = True
        self.frame_read = None

        # Initialize visual thread
        self.visual_thread = VisualThread(visual_protocol)

    def run(self):
        # Initialize OpenCV window in main thread if needed
        if hasattr(self.visual_protocol, 'initialize_window'):
            self.visual_protocol.initialize_window()

        self.visual_thread.start()  # Start visualization in separate thread
        try:
            self._takeoff_and_stabilize()
            start_time = time.time()
            self.frame_read = self.tello_connector.frame_read
            for _ in range(10):
                _ = self.frame_read.frame
                time.sleep(0.05)
            while self.running:
                frame = self._get_frame()
                if frame is None:
                    logging.warning("Frame unavailable, skipping iteration.")
                    continue

                found, error, debug = self.tracker.process_frame(frame)
                debug["stage"] = "control"
                self._draw_cross(frame)

                # Draw tracker-specific debug info (boundary annotations)
                if hasattr(self.tracker, 'draw_debug_info'):
                    self.tracker.draw_debug_info(frame, debug)

                # Send frame and debug to visualization thread
                if self.visual_thread.is_alive():
                    self.visual_thread.frame = frame
                    self.visual_thread.debug = debug

                # Update OpenCV window in main thread to avoid threading issues
                if hasattr(self.visual_protocol, '_display_frame'):
                    self.visual_protocol._display_frame()

                self._handle_control(found, error)
                self._check_quit()
                self._check_timeout(start_time)

                time.sleep(0.05)

        except Exception as critical_error:
            logging.exception(f"Critical error encountered: {critical_error}")

        finally:
            self._land_and_cleanup()

    # --- Private methods ---

    def _get_frame(self):
        """Get frame with improved error handling."""
        try:
            if self.frame_read is None:
                logging.warning("Frame reader is None")
                return None

            frame = self.frame_read.frame
            if frame is None:
                return None

            # Get frame dimensions
            h, w = frame.shape[:2]

            # Check for significant frame size changes (camera mode switch)
            if not hasattr(self, '_last_frame_shape'):
                self._last_frame_shape = frame.shape
            elif frame.shape != self._last_frame_shape:
                logging.warning(f"Frame size changed from {self._last_frame_shape} to {frame.shape} - camera mode may have switched")
                self._last_frame_shape = frame.shape

            logging.debug(f"Raw frame shape: {frame.shape}")

            # Crop to ROI (ensure we don't exceed frame dimensions)
            crop_h = min(240, h)
            crop_w = min(320, w)
            cropped = frame[0:crop_h, 0:crop_w]
            logging.debug(f"Cropped frame shape: {cropped.shape}")

            # Transpose if needed (depends on camera orientation)
            transposed = cv2.transpose(cropped)
            logging.debug(f"Transposed frame shape: {transposed.shape}")

            return transposed

        except Exception as e:
            logging.error(f"Frame processing error: {e}")
            return None

    def _handle_control(self, found, error):
        if found:
            rc = self.control_protocol.compute_control(error)
            self.tello.send_rc_control(*rc)
            logging.debug(f"Sent control: {rc}")
        else:
            logging.warning("Target lost. Hovering.")
            self.tello.send_rc_control(0, 0, 0, 0)

    def _check_quit(self):
        # Check for quit key in main thread
        try:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Quit signal received.")
                self.running = False
        except Exception as e:
            logging.debug(f"Error checking quit key: {e}")

    def _check_timeout(self, start_time):
        if time.time() - start_time > self.timeout:
            logging.info("Timeout reached, initiating landing.")
            self.running = False

    def _land_and_cleanup(self):
        logging.info("Initiating landing protocol.")
        try:
            # kick off the landing sequence
            if self.frame_read:
                self.landing_protocol.land(self.tello, frame_read=self.frame_read)
            else:
                self.landing_protocol.land(self.tello)

            # while landing is still in progress, keep updating the visual feed
            while not getattr(self.landing_protocol, "finished", True):
                frame = self.tello_connector.frame_read.frame
                if frame is not None:
                    h, w = frame.shape[:2]
                    crop_h = min(240, h)
                    crop_w = min(320, w)
                    cropped = frame[0:crop_h, 0:crop_w]
                    transposed = cv2.transpose(cropped)
                    self._draw_cross(transposed)
                    debug = {"status": "LANDING", "previews": []}
                    if self.visual_thread.is_alive():
                        self.visual_thread.frame = transposed
                        self.visual_thread.debug = debug
                time.sleep(0.05)

            # once landing is done, clean up
            self.tello_connector.cleanup()


        except Exception as cleanup_error:
            logging.exception(f"Error during cleanup: {cleanup_error}")

        finally:
            if self.visual_thread.is_alive():
                self.visual_thread.stop()
                self.visual_thread.join()
            logging.info("Cleanup completed.")
  
        
  



    def _takeoff_and_stabilize(self):
        logging.info("Drone taking off...")
        self.tello.takeoff()
        start = time.time()
        ascend_sent = False
        # loop for ~3 s: send the 'up' command once, then keep updating the view
        while time.time() - start < 3.0:
            if not ascend_sent and time.time() - start > 0.1:
                self.tello.move('up', self.takeoff_height)
                ascend_sent = True

            # get a frame from the stream
            frame = self.tello_connector.frame_read.frame
            if frame is not None:
                # reuse the same cropping/transposition you do in _get_frame()
                h, w = frame.shape[:2]
                crop_h = min(240, h)
                crop_w = min(320, w)
                cropped = frame[0:crop_h, 0:crop_w]
                transposed = cv2.transpose(cropped)
                # draw the centre cross
                self._draw_cross(transposed)
                # minimal debug info for take‑off phase
                debug = {"status": "TAKEOFF", "previews": []}
                if self.visual_thread.is_alive():
                    self.visual_thread.frame = transposed
                    self.visual_thread.debug = debug
            time.sleep(0.05)

        logging.info(f"Drone stabilized at {self.takeoff_height} cm.")



    def _draw_cross(self, frame):
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        size = int(min(w, h) * 0.06)
        cv2.drawMarker(frame, center, (255, 0, 0), markerType=cv2.MARKER_CROSS, markerSize=size, thickness=2)


def post_flight_cleanup(tello_connector):
    logging.info("Resetting drone and cleaning up resources.")
    tello_connector.cleanup()
    input("Cleanup complete. Press Enter to exit.")


if __name__ == "__main__":
    main()
