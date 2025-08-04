"""
Configuration manager for drone project settings.
Handles loading, saving, and validating configuration files.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration files for the drone project."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.default_config_path = self.config_dir / "default_config.json"
        self.user_config_path = self.config_dir / "user_config.json"
        
    def load_config(self, config_name: str = "user") -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_name: Name of config file (without .json extension)
            
        Returns:
            Dictionary containing configuration
        """
        config_path = self.config_dir / f"{config_name}.json"
        
        if not config_path.exists():
            if config_name == "user":
                # Create user config from default if it doesn't exist
                self._create_user_config()
                config_path = self.user_config_path
            else:
                raise FileNotFoundError(f"Configuration file {config_path} not found")
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logging.info(f"Loaded configuration from {config_path}")
            return config
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file {config_path}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error loading config file {config_path}: {e}")
            raise
    
    def save_config(self, config: Dict[str, Any], config_name: str = "user") -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            config_name: Name of config file (without .json extension)
        """
        config_path = self.config_dir / f"{config_name}.json"
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Saved configuration to {config_path}")
        except Exception as e:
            logging.error(f"Error saving config file {config_path}: {e}")
            raise
    
    def _create_user_config(self) -> None:
        """Create user config file from default config."""
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, 'r') as f:
                    default_config = json.load(f)
                self.save_config(default_config, "user")
                logging.info("Created user config from default config")
            except Exception as e:
                logging.error(f"Error creating user config: {e}")
                raise
        else:
            logging.warning("Default config not found, creating empty user config")
            empty_config = self._get_empty_config()
            self.save_config(empty_config, "user")
    
    def _get_empty_config(self) -> Dict[str, Any]:
        """Get an empty configuration template."""
        return {
            "tracker": {"type": "circle", "parameters": {}},
            "control_protocol": {"type": "pid", "parameters": {}},
            "landing_protocol": {"type": "multilayer", "parameters": {}},
            "visual_protocol": {"type": "opencv", "parameters": {}},
            "drone_settings": {},
            "precision_landing": {},
            "continuous_glide": {},
            "grid_visual": {}
        }
    
    def list_configs(self) -> list:
        """List all available configuration files."""
        configs = []
        for config_file in self.config_dir.glob("*.json"):
            configs.append(config_file.stem)
        return sorted(configs)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_sections = [
            "tracker", "control_protocol", "landing_protocol", 
            "visual_protocol", "drone_settings"
        ]
        
        for section in required_sections:
            if section not in config:
                logging.error(f"Missing required section: {section}")
                return False
        
        return True
    
    def get_tracker_config(self, config: Dict[str, Any]) -> tuple:
        """Extract tracker configuration from config dict."""
        tracker_config = config.get("tracker", {})
        tracker_type = tracker_config.get("type", "circle")
        parameters = tracker_config.get("parameters", {})
        return tracker_type, parameters
    
    def get_control_config(self, config: Dict[str, Any]) -> tuple:
        """Extract control protocol configuration from config dict."""
        control_config = config.get("control_protocol", {})
        control_type = control_config.get("type", "pid")
        parameters = control_config.get("parameters", {})
        return control_type, parameters
    
    def get_landing_config(self, config: Dict[str, Any]) -> tuple:
        """Extract landing protocol configuration from config dict."""
        landing_config = config.get("landing_protocol", {})
        landing_type = landing_config.get("type", "multilayer")
        parameters = landing_config.get("parameters", {})
        return landing_type, parameters
    
    def get_visual_config(self, config: Dict[str, Any]) -> tuple:
        """Extract visual protocol configuration from config dict."""
        visual_config = config.get("visual_protocol", {})
        visual_type = visual_config.get("type", "opencv")
        parameters = visual_config.get("parameters", {})
        return visual_type, parameters
    
    def get_drone_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract drone settings from config dict."""
        return config.get("drone_settings", {})

def create_config_from_user_input() -> Dict[str, Any]:
    """
    Interactive function to create a configuration from user input.
    This allows users to create a custom config file.
    """
    from utils.setup_utils import (
        select_tracker, select_control_protocol, 
        select_visual_protocol, configure_landing
    )
    
    print("Creating new configuration file...")
    print("Please select your preferred settings:")
    
    # Create a mock tello connector for the setup functions
    class MockTelloConnector:
        def __init__(self):
            self.tello = None
    
    mock_connector = MockTelloConnector()
    
    # Get user selections
    tracker = select_tracker(mock_connector)
    control_protocol = select_control_protocol()
    visual_protocol = select_visual_protocol()
    landing_protocol = configure_landing(tracker, control_protocol, visual_protocol)
    
    # Build config dictionary
    config = {
        "tracker": {
            "type": tracker.__class__.__name__.lower().replace("tracker", ""),
            "parameters": _extract_tracker_parameters(tracker)
        },
        "control_protocol": {
            "type": control_protocol.__class__.__name__.lower().replace("control", ""),
            "parameters": _extract_control_parameters(control_protocol)
        },
        "landing_protocol": {
            "type": landing_protocol.__class__.__name__.lower().replace("landing", ""),
            "parameters": _extract_landing_parameters(landing_protocol)
        },
        "visual_protocol": {
            "type": visual_protocol.__class__.__name__.lower().replace("visualprotocol", ""),
            "parameters": _extract_visual_parameters(visual_protocol)
        },
        "drone_settings": _extract_drone_settings()
    }
    
    return config 

def _extract_tracker_parameters(tracker):
    """Extract parameters from tracker object for configuration."""
    if hasattr(tracker, 'area_range') and hasattr(tracker, 'circularity_min'):
        # CircleTracker
        min_area = tracker.area_range[0] if tracker.area_range else 200
        max_area = tracker.area_range[1] if tracker.area_range else 5000
        max_radius = int((max_area / 3.14159) ** 0.5)  # Convert area back to radius
        return {
            "min_area": min_area,
            "max_radius": max_radius,
            "min_circularity": tracker.circularity_min
        }
    elif hasattr(tracker, 'marker_size'):
        # ArUco trackers
        params = {"marker_size": tracker.marker_size}
        if hasattr(tracker, 'dictionary'):
            # Could add marker_dict parameter here if needed
            pass
        return params
    else:
        return getattr(tracker, 'parameters', {})

def _extract_control_parameters(control_protocol):
    """Extract parameters from control protocol object for configuration."""
    params = {}
    if hasattr(control_protocol, 'Kp'):
        params['Kp'] = control_protocol.Kp
    if hasattr(control_protocol, 'Ki'):
        params['Ki'] = control_protocol.Ki
    if hasattr(control_protocol, 'Kd'):
        params['Kd'] = control_protocol.Kd
    if hasattr(control_protocol, 'vmax'):
        params['vmax'] = control_protocol.vmax
    if hasattr(control_protocol, 'integral_limit'):
        params['integral_limit'] = control_protocol.integral_limit
    return params

def _extract_landing_parameters(landing_protocol):
    """Extract parameters from landing protocol object for configuration."""
    params = {}
    if hasattr(landing_protocol, 'layers'):
        params['layers'] = landing_protocol.layers
    if hasattr(landing_protocol, 'layer_height'):
        params['layer_height'] = landing_protocol.layer_height
    if hasattr(landing_protocol, 'align_timeout'):
        params['align_timeout'] = landing_protocol.align_timeout
    if hasattr(landing_protocol, 'align_threshold'):
        params['align_threshold'] = landing_protocol.align_threshold
    if hasattr(landing_protocol, 'aligned_frames_needed'):
        params['aligned_frames'] = landing_protocol.aligned_frames_needed
    if hasattr(landing_protocol, 'velocity_threshold'):
        params['velocity_threshold'] = landing_protocol.velocity_threshold
    if hasattr(landing_protocol, 'target_area_percentage'):
        params['target_area_percentage'] = landing_protocol.target_area_percentage
    if hasattr(landing_protocol, 'min_distance'):
        params['min_distance'] = landing_protocol.min_distance
    if hasattr(landing_protocol, 'spiral_radius'):
        params['spiral_radius'] = landing_protocol.spiral_radius
    if hasattr(landing_protocol, 'alignment_threshold'):
        params['alignment_threshold'] = landing_protocol.alignment_threshold
    if hasattr(landing_protocol, 'position_threshold'):
        params['position_threshold'] = landing_protocol.position_threshold
    if hasattr(landing_protocol, 'descent_gain'):
        params['descent_gain'] = landing_protocol.descent_gain
    if hasattr(landing_protocol, 'min_vz'):
        params['min_vz'] = landing_protocol.min_vz
    if hasattr(landing_protocol, 'max_vz'):
        params['max_vz'] = landing_protocol.max_vz
    if hasattr(landing_protocol, 'height_threshold'):
        params['height_threshold'] = landing_protocol.height_threshold
    return params

def _extract_visual_parameters(visual_protocol):
    """Extract parameters from visual protocol object for configuration."""
    params = {}
    if hasattr(visual_protocol, 'window_name'):
        params['window_name'] = visual_protocol.window_name
    if hasattr(visual_protocol, 'debug_level'):
        params['debug_level'] = visual_protocol.debug_level
    if hasattr(visual_protocol, 'grid_shape'):
        params['grid_rows'] = visual_protocol.grid_shape[0]
        params['grid_cols'] = visual_protocol.grid_shape[1]
    if hasattr(visual_protocol, 'cell_w') and hasattr(visual_protocol, 'cell_h'):
        params['cell_width'] = visual_protocol.cell_w
        params['cell_height'] = visual_protocol.cell_h
    return params

def _extract_drone_settings():
    """Extract default drone settings for configuration."""
    return {
        "takeoff_height": 30,
        "target_height": 30,
        "timeout": 40,
        "camera_mode": "downward"
    } 