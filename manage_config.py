#!/usr/bin/env python3
"""
Configuration management script for the drone project.
Allows users to create, edit, and manage configuration files.
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.append('.')

from utils.config_manager import ConfigManager, create_config_from_user_input
from utils.logging_utils import setup_logger

def main():
    """Main configuration management interface."""
    setup_logger()
    
    config_manager = ConfigManager()
    
    while True:
        print("\n" + "="*50)
        print("CONFIGURATION MANAGEMENT")
        print("="*50)
        print("1. List all configurations")
        print("2. Create new configuration")
        print("3. Edit existing configuration")
        print("4. Delete configuration")
        print("5. View configuration details")
        print("6. Copy configuration")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            list_configurations(config_manager)
        elif choice == "2":
            create_configuration(config_manager)
        elif choice == "3":
            edit_configuration(config_manager)
        elif choice == "4":
            delete_configuration(config_manager)
        elif choice == "5":
            view_configuration(config_manager)
        elif choice == "6":
            copy_configuration(config_manager)
        elif choice == "7":
            print("Exiting configuration manager.")
            break
        else:
            print("Invalid choice. Please select 1-7.")

def list_configurations(config_manager):
    """List all available configurations."""
    configs = config_manager.list_configs()
    if configs:
        print(f"\nAvailable configurations ({len(configs)}):")
        for i, config_name in enumerate(configs, 1):
            print(f"  {i}. {config_name}")
    else:
        print("\nNo configuration files found.")
        print("Use option 2 to create your first configuration.")

def create_configuration(config_manager):
    """Create a new configuration file."""
    print("\nCreating new configuration...")
    
    try:
        config = create_config_from_user_input()
        
        config_name = input("Enter name for new configuration: ").strip()
        if not config_name:
            print("Configuration name cannot be empty.")
            return
        
        if config_name in config_manager.list_configs():
            overwrite = input(f"Configuration '{config_name}' already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("Configuration creation cancelled.")
                return
        
        config_manager.save_config(config, config_name)
        print(f"Configuration '{config_name}' created successfully!")
        
    except Exception as e:
        print(f"Error creating configuration: {e}")

def edit_configuration(config_manager):
    """Edit an existing configuration file."""
    configs = config_manager.list_configs()
    if not configs:
        print("No configurations to edit.")
        return
    
    print(f"\nAvailable configurations: {', '.join(configs)}")
    config_name = input("Enter configuration name to edit: ").strip()
    
    if config_name not in configs:
        print(f"Configuration '{config_name}' not found.")
        return
    
    try:
        config = config_manager.load_config(config_name)
        
        print(f"\nEditing configuration: {config_name}")
        print("1. Edit tracker settings")
        print("2. Edit control protocol settings")
        print("3. Edit landing protocol settings")
        print("4. Edit visual protocol settings")
        print("5. Edit drone settings")
        print("6. Cancel")
        
        edit_choice = input("Select section to edit (1-6): ").strip()
        
        if edit_choice == "1":
            edit_tracker_settings(config)
        elif edit_choice == "2":
            edit_control_settings(config)
        elif edit_choice == "3":
            edit_landing_settings(config)
        elif edit_choice == "4":
            edit_visual_settings(config)
        elif edit_choice == "5":
            edit_drone_settings(config)
        elif edit_choice == "6":
            print("Edit cancelled.")
            return
        else:
            print("Invalid choice.")
            return
        
        config_manager.save_config(config, config_name)
        print(f"Configuration '{config_name}' updated successfully!")
        
    except Exception as e:
        print(f"Error editing configuration: {e}")

def edit_tracker_settings(config):
    """Edit tracker settings in configuration."""
    print("\nCurrent tracker settings:")
    tracker_config = config.get("tracker", {})
    print(f"  Type: {tracker_config.get('type', 'circle')}")
    print(f"  Parameters: {tracker_config.get('parameters', {})}")
    
    print("\nAvailable tracker types:")
    print("  circle, aruco, precisionaruco, missionpad, colorpatch, darkrect, lightrect, phone, simplephone")
    
    new_type = input("Enter new tracker type (or press Enter to keep current): ").strip()
    if new_type:
        tracker_config["type"] = new_type
    
    print("Enter new parameters (press Enter to skip each):")
    params = tracker_config.get("parameters", {})
    
    # Common parameters
    for param in ["min_radius", "max_radius", "min_circularity", "min_area"]:
        current = params.get(param, "")
        new_value = input(f"  {param} [{current}]: ").strip()
        if new_value:
            try:
                if "." in new_value:
                    params[param] = float(new_value)
                else:
                    params[param] = int(new_value)
            except ValueError:
                print(f"Invalid value for {param}, keeping current value.")
    
    tracker_config["parameters"] = params
    config["tracker"] = tracker_config

def edit_control_settings(config):
    """Edit control protocol settings in configuration."""
    print("\nCurrent control protocol settings:")
    control_config = config.get("control_protocol", {})
    print(f"  Type: {control_config.get('type', 'pid')}")
    print(f"  Parameters: {control_config.get('parameters', {})}")
    
    print("\nAvailable control types:")
    print("  proportional, pi, pid")
    
    new_type = input("Enter new control type (or press Enter to keep current): ").strip()
    if new_type:
        control_config["type"] = new_type
    
    print("Enter new parameters (press Enter to skip each):")
    params = control_config.get("parameters", {})
    
    # PID parameters
    for param in ["Kp", "Ki", "Kd", "vmax", "integral_limit"]:
        current = params.get(param, "")
        new_value = input(f"  {param} [{current}]: ").strip()
        if new_value:
            try:
                if param in ["Kp", "Ki", "Kd"]:
                    params[param] = float(new_value)
                else:
                    params[param] = int(new_value)
            except ValueError:
                print(f"Invalid value for {param}, keeping current value.")
    
    control_config["parameters"] = params
    config["control_protocol"] = control_config

def edit_landing_settings(config):
    """Edit landing protocol settings in configuration."""
    print("\nCurrent landing protocol settings:")
    landing_config = config.get("landing_protocol", {})
    print(f"  Type: {landing_config.get('type', 'multilayer')}")
    print(f"  Parameters: {landing_config.get('parameters', {})}")
    
    print("\nAvailable landing types:")
    print("  simple, multilayer, precision, continuousglide")
    
    new_type = input("Enter new landing type (or press Enter to keep current): ").strip()
    if new_type:
        landing_config["type"] = new_type
    
    print("Enter new parameters (press Enter to skip each):")
    params = landing_config.get("parameters", {})
    
    # Common parameters
    for param in ["layers", "layer_height", "align_timeout", "align_threshold", "aligned_frames", "velocity_threshold"]:
        current = params.get(param, "")
        new_value = input(f"  {param} [{current}]: ").strip()
        if new_value:
            try:
                if param in ["align_timeout", "velocity_threshold"]:
                    params[param] = float(new_value)
                else:
                    params[param] = int(new_value)
            except ValueError:
                print(f"Invalid value for {param}, keeping current value.")
    
    landing_config["parameters"] = params
    config["landing_protocol"] = landing_config

def edit_visual_settings(config):
    """Edit visual protocol settings in configuration."""
    print("\nCurrent visual protocol settings:")
    visual_config = config.get("visual_protocol", {})
    print(f"  Type: {visual_config.get('type', 'opencv')}")
    print(f"  Parameters: {visual_config.get('parameters', {})}")
    
    print("\nAvailable visual types:")
    print("  opencv, logger, grid")
    
    new_type = input("Enter new visual type (or press Enter to keep current): ").strip()
    if new_type:
        visual_config["type"] = new_type
    
    print("Enter new parameters (press Enter to skip each):")
    params = visual_config.get("parameters", {})
    
    # Common parameters
    for param in ["window_name", "debug_level"]:
        current = params.get(param, "")
        new_value = input(f"  {param} [{current}]: ").strip()
        if new_value:
            params[param] = new_value
    
    # Grid-specific parameters
    if new_type == "grid" or visual_config.get("type") == "grid":
        for param in ["grid_rows", "grid_cols", "cell_width", "cell_height"]:
            current = params.get(param, "")
            new_value = input(f"  {param} [{current}]: ").strip()
            if new_value:
                try:
                    params[param] = int(new_value)
                except ValueError:
                    print(f"Invalid value for {param}, keeping current value.")
    
    visual_config["parameters"] = params
    config["visual_protocol"] = visual_config

def edit_drone_settings(config):
    """Edit drone settings in configuration."""
    print("\nCurrent drone settings:")
    drone_settings = config.get("drone_settings", {})
    print(f"  {drone_settings}")
    
    print("Enter new settings (press Enter to skip each):")
    
    for param in ["takeoff_height", "target_height", "timeout"]:
        current = drone_settings.get(param, "")
        new_value = input(f"  {param} [{current}]: ").strip()
        if new_value:
            try:
                drone_settings[param] = int(new_value)
            except ValueError:
                print(f"Invalid value for {param}, keeping current value.")
    
    # Camera mode selection
    current_camera = drone_settings.get("camera_mode", "downward")
    print(f"\nCamera mode options: downward, front")
    new_camera = input(f"  camera_mode [{current_camera}]: ").strip()
    if new_camera and new_camera in ["downward", "front"]:
        drone_settings["camera_mode"] = new_camera
    elif new_camera:
        print("Invalid camera mode, keeping current value.")
    
    config["drone_settings"] = drone_settings

def delete_configuration(config_manager):
    """Delete a configuration file."""
    configs = config_manager.list_configs()
    if not configs:
        print("No configurations to delete.")
        return
    
    print(f"\nAvailable configurations: {', '.join(configs)}")
    config_name = input("Enter configuration name to delete: ").strip()
    
    if config_name not in configs:
        print(f"Configuration '{config_name}' not found.")
        return
    
    confirm = input(f"Are you sure you want to delete '{config_name}'? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            config_path = config_manager.config_dir / f"{config_name}.json"
            config_path.unlink()
            print(f"Configuration '{config_name}' deleted successfully!")
        except Exception as e:
            print(f"Error deleting configuration: {e}")
    else:
        print("Deletion cancelled.")

def view_configuration(config_manager):
    """View detailed configuration information."""
    configs = config_manager.list_configs()
    if not configs:
        print("No configurations to view.")
        return
    
    print(f"\nAvailable configurations: {', '.join(configs)}")
    config_name = input("Enter configuration name to view: ").strip()
    
    if config_name not in configs:
        print(f"Configuration '{config_name}' not found.")
        return
    
    try:
        config = config_manager.load_config(config_name)
        print(f"\nConfiguration: {config_name}")
        print("=" * 50)
        print(json.dumps(config, indent=2))
    except Exception as e:
        print(f"Error viewing configuration: {e}")

def copy_configuration(config_manager):
    """Copy an existing configuration to a new name."""
    configs = config_manager.list_configs()
    if not configs:
        print("No configurations to copy.")
        return
    
    print(f"\nAvailable configurations: {', '.join(configs)}")
    source_name = input("Enter source configuration name: ").strip()
    
    if source_name not in configs:
        print(f"Configuration '{source_name}' not found.")
        return
    
    target_name = input("Enter new configuration name: ").strip()
    if not target_name:
        print("Target name cannot be empty.")
        return
    
    if target_name in configs:
        overwrite = input(f"Configuration '{target_name}' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Copy cancelled.")
            return
    
    try:
        config = config_manager.load_config(source_name)
        config_manager.save_config(config, target_name)
        print(f"Configuration '{source_name}' copied to '{target_name}' successfully!")
    except Exception as e:
        print(f"Error copying configuration: {e}")

if __name__ == "__main__":
    main() 