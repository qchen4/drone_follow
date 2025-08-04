"""
Factory functions to create objects from configuration.
"""

import logging
from typing import Dict, Any

def create_tracker_from_config(tracker_type: str, parameters: Dict[str, Any], tello_connector=None):
    """Create a tracker instance from configuration."""
    try:
        if tracker_type == "circle":
            from trackers.circle_tracker import CircleTracker
            # Map configuration parameters to CircleTracker constructor parameters
            mapped_params = {}
            if "min_area" in parameters and "max_area" in parameters:
                # Use area-based parameters directly
                min_area = parameters.get("min_area", 100)
                max_area = parameters.get("max_area", 8000)
                mapped_params["area_range"] = (min_area, max_area)
            elif "min_area" in parameters and "max_radius" in parameters:
                # Convert radius-based parameters to area-based (backward compatibility)
                min_area = parameters.get("min_area", 100)
                max_area = int(3.14159 * parameters.get("max_radius", 500) ** 2)  # π * r²
                mapped_params["area_range"] = (min_area, max_area)
            elif "area_range" in parameters:
                mapped_params["area_range"] = parameters["area_range"]
            else:
                mapped_params["area_range"] = (100, 8000)  # Default
            
            if "min_circularity" in parameters:
                mapped_params["circularity_min"] = parameters["min_circularity"]
            else:
                mapped_params["circularity_min"] = 0.6  # Default
            
            return CircleTracker(**mapped_params)
        elif tracker_type == "aruco":
            from trackers.aruco_tracker import ArucoTracker
            return ArucoTracker(**parameters)
        elif tracker_type == "precisionaruco":
            from trackers.precision_aruco_tracker import PrecisionArucoTracker
            return PrecisionArucoTracker(**parameters)
        elif tracker_type == "missionpad":
            from trackers.mission_pad_tracker import MissionPadTracker
            return MissionPadTracker(tello_connector, **parameters)
        elif tracker_type == "colorpatch":
            from trackers.color_patch_tracker import ColorPatchTracker
            return ColorPatchTracker(**parameters)
        elif tracker_type == "darkrect":
            from trackers.dark_rect_tracker import DarkRectTracker
            return DarkRectTracker(**parameters)
        elif tracker_type == "lightrect":
            from trackers.light_rect_tracker import LightRectTracker
            return LightRectTracker(**parameters)
        elif tracker_type == "phone":
            from trackers.phone_tracker import PhoneTracker
            return PhoneTracker(**parameters)
        elif tracker_type == "simplephone":
            from trackers.simple_phone_tracker import SimplePhoneTracker
            return SimplePhoneTracker(**parameters)
        else:
            raise ValueError(f"Unknown tracker type: {tracker_type}")
    except Exception as e:
        logging.error(f"Error creating tracker {tracker_type}: {e}")
        raise

def create_control_protocol_from_config(control_type: str, parameters: Dict[str, Any]):
    """Create a control protocol instance from configuration."""
    try:
        if control_type == "proportional":
            from control_protocols.proportional_control import ProportionalControl
            return ProportionalControl(**parameters)
        elif control_type == "pi":
            from control_protocols.pi_control import PIControl
            return PIControl(**parameters)
        elif control_type == "pid":
            from control_protocols.pid_control import PIDControl
            return PIDControl(**parameters)
        else:
            raise ValueError(f"Unknown control protocol type: {control_type}")
    except Exception as e:
        logging.error(f"Error creating control protocol {control_type}: {e}")
        raise

def create_landing_protocol_from_config(landing_type: str, parameters: Dict[str, Any], 
                                       tracker=None, control_protocol=None, visual_protocol=None):
    """Create a landing protocol instance from configuration."""
    try:
        if landing_type == "simple":
            from landing_protocols.simple_landing import SimpleLanding
            return SimpleLanding()
        elif landing_type == "multilayer":
            from landing_protocols.multilayer_landing import MultiLayerLanding
            # Map configuration parameters to MultiLayerLanding constructor parameters
            mapped_params = {}
            if "layers" in parameters:
                mapped_params["layers"] = parameters["layers"]
            if "layer_height" in parameters:
                mapped_params["layer_height"] = parameters["layer_height"]
            if "align_timeout" in parameters:
                mapped_params["align_timeout"] = parameters["align_timeout"]
            if "align_threshold" in parameters:
                mapped_params["align_threshold"] = parameters["align_threshold"]
            if "aligned_frames" in parameters:
                mapped_params["aligned_frames_needed"] = parameters["aligned_frames"]
            if "velocity_threshold" in parameters:
                mapped_params["velocity_threshold"] = parameters["velocity_threshold"]
            
            return MultiLayerLanding(tracker=tracker, control_protocol=control_protocol, 
                                   visual_protocol=visual_protocol, **mapped_params)
        elif landing_type == "precision":
            from landing_protocols.precision_landing import PrecisionLandingProtocol
            return PrecisionLandingProtocol(tracker=tracker, control_protocol=control_protocol,
                                          visual_protocol=visual_protocol, **parameters)
        elif landing_type == "continuousglide":
            from landing_protocols.continuous_glide_landing import ContinuousGlideLanding
            return ContinuousGlideLanding(tracker=tracker, control_protocol=control_protocol, **parameters)
        else:
            raise ValueError(f"Unknown landing protocol type: {landing_type}")
    except Exception as e:
        logging.error(f"Error creating landing protocol {landing_type}: {e}")
        raise

def create_visual_protocol_from_config(visual_type: str, parameters: Dict[str, Any]):
    """Create a visual protocol instance from configuration."""
    try:
        if visual_type == "opencv":
            from visual_protocols.opencv_visual import OpenCVVisualProtocol
            return OpenCVVisualProtocol(**parameters)
        elif visual_type == "logger":
            from visual_protocols.logger_visual import LoggerVisualProtocol
            return LoggerVisualProtocol()
        elif visual_type in ("grid", "grid_visual", "gridvisual"):
            from visual_protocols.grid_visual import GridVisualProtocol
            # Map configuration parameters to GridVisualProtocol constructor parameters
            mapped_params = {}
            if "window_name" in parameters:
                mapped_params["window_name"] = parameters["window_name"]
            if "grid_rows" in parameters and "grid_cols" in parameters:
                mapped_params["grid_shape"] = (parameters["grid_rows"], parameters["grid_cols"])
            if "cell_width" in parameters and "cell_height" in parameters:
                mapped_params["cell_size"] = (parameters["cell_width"], parameters["cell_height"])
            
            return GridVisualProtocol(**mapped_params)
        else:
            raise ValueError(f"Unknown visual protocol type: {visual_type}")
    except Exception as e:
        logging.error(f"Error creating visual protocol {visual_type}: {e}")
        raise

def create_components_from_config(config: Dict[str, Any], tello_connector=None):
    """
    Create all components from configuration.
    
    Returns:
        tuple: (tracker, control_protocol, visual_protocol, landing_protocol, drone_settings)
    """
    # Extract configurations
    tracker_type, tracker_params = config.get("tracker", {}).get("type", "circle"), config.get("tracker", {}).get("parameters", {})
    control_type, control_params = config.get("control_protocol", {}).get("type", "pid"), config.get("control_protocol", {}).get("parameters", {})
    visual_type, visual_params = config.get("visual_protocol", {}).get("type", "opencv"), config.get("visual_protocol", {}).get("parameters", {})
    landing_type, landing_params = config.get("landing_protocol", {}).get("type", "multilayer"), config.get("landing_protocol", {}).get("parameters", {})
    drone_settings = config.get("drone_settings", {})
    
    # Create components
    tracker = create_tracker_from_config(tracker_type, tracker_params, tello_connector)
    control_protocol = create_control_protocol_from_config(control_type, control_params)
    visual_protocol = create_visual_protocol_from_config(visual_type, visual_params)
    landing_protocol = create_landing_protocol_from_config(landing_type, landing_params, 
                                                         tracker, control_protocol, visual_protocol)
    
    return tracker, control_protocol, visual_protocol, landing_protocol, drone_settings 