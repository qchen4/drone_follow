"""
Interactive helper-prompts that keep main.py clean.
"""

import logging
import math
# ── Generic prompt helpers ────────────────────────────────────────────────────
def _prompt_int(msg: str, default: int) -> int:
    val = input(f"{msg} [{default}]: ").strip()
    return int(val) if val else default

def _prompt_float(msg: str, default: float) -> float:
    val = input(f"{msg} [{default}]: ").strip()
    return float(val) if val else default

# ── Tracker selection ────────────────────────────────────────────────────────
from trackers.mission_pad_tracker import MissionPadTracker
from trackers.color_patch_tracker  import ColorPatchTracker
from trackers.rect_trackers        import LightRectTracker, DarkRectTracker
from trackers.aruco_tracker        import ArucoTracker
from trackers.circle_tracker       import CircleTracker
from trackers.phone_tracker        import PhoneTracker
from trackers.simple_phone_tracker import SimplePhoneTracker

def select_tracker(tello_connector):
    print("\n✔  Choose tracking mode:")
    print("1: Mission Pad  2: Color Patch  3: Light Rect  4: Dark Rect  5: ArUco  6: Circle  7: Phone  8: Simple Phone")
    choice = input("Enter 1-8: ").strip()

    tello_connector.set_downward_camera()

    if choice == "1":
        tello_connector.enable_mission_pads()
        return MissionPadTracker(tello_connector)
    if choice == "2":
        return ColorPatchTracker()
    if choice == "3":
        return LightRectTracker()
    if choice == "4":
        return DarkRectTracker()
    if choice == "5":
        return ArucoTracker()
    if choice == "6":
        # Ask for radii but derive areas
        min_radius = _prompt_int("Min circle radius (pixels)", 20)
        max_radius = _prompt_int("Max circle radius (pixels)", 100)
        circularity_min = _prompt_float("Minimum circularity (0.0–1.0)", 0.8)

        # derive area range: area ≈ πr², with some slack
        min_area = int(math.pi * min_radius**2 * 0.3)  # conservative lower bound
        max_area = int(math.pi * max_radius**2 * 3.0)  # liberal upper bound

        return CircleTracker(area_range=(min_area, max_area),
                            circularity_min=circularity_min)

    if choice == "7": # PHONE TRACKER
        confidence = _prompt_float("Detection confidence threshold", 0.5)
        iou_threshold = _prompt_float("IoU threshold for NMS", 0.5)
        return PhoneTracker(confidence=confidence, iou_threshold=iou_threshold)
    if choice == "8": # SIMPLE PHONE TRACKER
        min_area = _prompt_int("Minimum area for phone detection", 1000)
        max_area = _prompt_int("Maximum area for phone detection", 50000)
        min_ar = _prompt_float("Minimum aspect ratio (width/height)", 1.5)
        max_ar = _prompt_float("Maximum aspect ratio (width/height)", 3.0)
        return SimplePhoneTracker(min_area=min_area, max_area=max_area,
                                aspect_ratio_range=(min_ar, max_ar))
    # default
    return ArucoTracker()

# ── Control-law selection ────────────────────────────────────────────────────
from control_protocols.proportional_control import ProportionalControl
from control_protocols.pi_control           import PIControl
from control_protocols.pid_control          import PIDControl

def select_control_protocol():
    print("\n✔  Control law: 1) P   2) PI   3) PID")
    ch = input("Select 1-3: ").strip()

    if ch == "2":
        return PIControl(
            Kp=_prompt_float("PI Kp", 0.5),
            Ki=_prompt_float("PI Ki", 0.01),
            vmax=_prompt_int("vmax", 25),
        )
    if ch == "3":
        return PIDControl(
            Kp=_prompt_float("PID Kp", 0.5),
            Ki=_prompt_float("PID Ki", 0.01),
            Kd=_prompt_float("PID Kd", 0.05),
            vmax=_prompt_int("vmax", 25),
            integral_limit=_prompt_int("Int-limit", 100),
        )
    # P-control default
    return ProportionalControl(
        Kp=_prompt_float("P  Kp", 0.5),
        vmax=_prompt_int("vmax", 25),
    )

# ── Landing selection ────────────────────────────────────────────────────────
from landing_protocols.simple_landing     import SimpleLanding
from landing_protocols.multilayer_landing import MultiLayerLanding

def configure_landing(tracker, control_protocol, visual_protocol=None):
    print("\n✔  Landing: 1) Multi-layer  2) Simple")
    ch = input("Select 1/2: ").strip()

    if ch == "2":
        return SimpleLanding()

    # multilayer
    layers              = _prompt_int   ("Layers",                        3)
    layer_height        = _prompt_int   ("Height per layer (cm)",        20)
    align_timeout       = _prompt_float ("Align timeout (s)",            2.5)
    align_threshold     = _prompt_int   ("Align threshold (px|cm)",      12)
    aligned_frames      = _prompt_int   ("Consecutive aligned frames",   10)
    velocity_threshold  = _prompt_float ("Velocity threshold (cm/s)",    12)

    return MultiLayerLanding(
        layers=layers,
        layer_height=layer_height,
        align_timeout=align_timeout,
        align_threshold=align_threshold,
        aligned_frames_needed=aligned_frames,
        velocity_threshold=velocity_threshold,
        tracker=tracker,
        control_protocol=control_protocol,
        visual_protocol=visual_protocol,
    )

# ── Visual protocol selection ────────────────────────────────────────────────
from visual_protocols.opencv_visual  import OpenCVVisualProtocol
from visual_protocols.logger_visual import LoggerVisualProtocol

def select_visual_protocol():
    print("\n✔  Visual output: 1) OpenCV  2) Console logger")
    return (OpenCVVisualProtocol(window_name="Tello Debug", debug_level="detailed")
            if input("Select 1/2 [1]: ").strip() != "2"
            else LoggerVisualProtocol())
