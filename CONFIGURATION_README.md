# Configuration System

The drone project now supports configuration files to save your preferred settings and avoid typing them in every time you run the application.

## Quick Start

### Option 1: Use Configuration File (Recommended)
```bash
python main.py
# Select option 1: "Use configuration file"
```

### Option 2: Create Your First Configuration
```bash
python manage_config.py
# Select option 2: "Create new configuration"
```

## Configuration Files

Configuration files are stored in the `config/` directory as JSON files. The system includes:

- **`default_config.json`**: Default configuration with recommended settings
- **`user_config.json`**: Your personal configuration (created automatically)

## Configuration Structure

Each configuration file contains the following sections:

```json
{
  "tracker": {
    "type": "circle",
    "parameters": {
      "min_radius": 20,
      "max_radius": 100,
      "min_circularity": 0.7,
      "min_area": 500
    }
  },
  "control_protocol": {
    "type": "pid",
    "parameters": {
      "Kp": 0.5,
      "Ki": 0.01,
      "Kd": 0.05,
      "vmax": 25,
      "integral_limit": 100
    }
  },
  "landing_protocol": {
    "type": "multilayer",
    "parameters": {
      "layers": 3,
      "layer_height": 20,
      "align_timeout": 2.5,
      "align_threshold": 12,
      "aligned_frames": 10,
      "velocity_threshold": 12
    }
  },
  "visual_protocol": {
    "type": "opencv",
    "parameters": {
      "window_name": "Tello Debug",
      "debug_level": "detailed"
    }
  },
  "drone_settings": {
    "takeoff_height": 30,
    "target_height": 30,
    "timeout": 40,
    "camera_mode": "downward"
  }
}
```

## Available Options

### Camera Mode
- **downward**: Ground-facing camera (recommended for landing and precision operations)
- **front**: Forward-facing camera (good for general navigation)

**Note**: The downward camera is only available on Tello EDU models. If you're using a regular Tello, the system will automatically fall back to the front camera.

### Tracker Types
- `circle`: Circle detection tracker
- `aruco`: ArUco marker tracker
- `precisionaruco`: Precision ArUco tracker with pose estimation
- `missionpad`: Mission pad tracker
- `colorpatch`: Color patch tracker
- `darkrect`: Dark rectangle tracker
- `lightrect`: Light rectangle tracker
- `phone`: Phone tracker
- `simplephone`: Simple phone tracker

### Control Protocol Types
- `proportional`: Proportional control
- `pi`: PI control
- `pid`: PID control (recommended)

### Landing Protocol Types
- `simple`: Simple landing
- `multilayer`: Multi-layer landing (recommended)
- `precision`: Precision landing with target detection
- `continuousglide`: Continuous glide landing

### Visual Protocol Types
- `opencv`: OpenCV window display
- `logger`: Console logging
- `grid`: Grid-based multi-pane debugging

## Managing Configurations

### Using the Configuration Manager

Run the configuration manager to create, edit, and manage your configurations:

```bash
python manage_config.py
```

**Available Options:**
1. **List all configurations** - See all available config files
2. **Create new configuration** - Interactive setup to create a new config
3. **Edit existing configuration** - Modify settings in an existing config
4. **Delete configuration** - Remove a configuration file
5. **View configuration details** - See the full JSON content
6. **Copy configuration** - Duplicate a config with a new name

### Creating a Configuration

1. **Interactive Creation:**
   ```bash
   python manage_config.py
   # Select option 2: "Create new configuration"
   # Follow the prompts to select your preferred settings
   ```

2. **From Main Application:**
   ```bash
   python main.py
   # Select option 3: "Create new configuration file"
   # This will guide you through the setup process
   ```

3. **Manual JSON Creation:**
   - Copy `config/default_config.json`
   - Modify the values as needed
   - Save with a new name in the `config/` directory

### Editing Configurations

```bash
python manage_config.py
# Select option 3: "Edit existing configuration"
# Choose the configuration to edit
# Select which section to modify:
#   - Tracker settings
#   - Control protocol settings
#   - Landing protocol settings
#   - Visual protocol settings
#   - Drone settings
```

## Using Configurations

### In Main Application

When you run `python main.py`, you'll see:

```
==================================================
DRONE CONFIGURATION
==================================================
1. Use configuration file (recommended)
2. Interactive setup (manual input)
3. Create new configuration file
4. List available configurations
```

**Option 1** (Recommended): Load settings from a configuration file
**Option 2**: Use the original interactive setup
**Option 3**: Create a new configuration file
**Option 4**: List available configurations

### Multiple Configurations

You can create multiple configurations for different scenarios:

- `config/indoor.json` - Indoor flying settings
- `config/outdoor.json` - Outdoor flying settings
- `config/precision.json` - Precision landing settings
- `config/debug.json` - Debugging settings

## Configuration Examples

### Precision Landing Configuration
```json
{
  "tracker": {
    "type": "precisionaruco",
    "parameters": {
      "marker_size": 15.0
    }
  },
  "control_protocol": {
    "type": "pid",
    "parameters": {
      "Kp": 0.3,
      "Ki": 0.01,
      "Kd": 0.1,
      "vmax": 50
    }
  },
  "landing_protocol": {
    "type": "precision",
    "parameters": {
      "target_area_percentage": 15.0,
      "min_distance": 20.0,
      "spiral_radius": 50.0,
      "alignment_threshold": 5.0,
      "position_threshold": 10
    }
  },
  "visual_protocol": {
    "type": "grid",
    "parameters": {
      "grid_rows": 2,
      "grid_cols": 2,
      "cell_width": 320,
      "cell_height": 240
    }
  },
  "drone_settings": {
    "takeoff_height": 50,
    "target_height": 50,
    "timeout": 60
  }
}
```

### Simple Circle Tracking Configuration
```json
{
  "tracker": {
    "type": "circle",
    "parameters": {
      "min_radius": 30,
      "max_radius": 150,
      "min_circularity": 0.8,
      "min_area": 1000
    }
  },
  "control_protocol": {
    "type": "proportional",
    "parameters": {
      "Kp": 0.5,
      "vmax": 30
    }
  },
  "landing_protocol": {
    "type": "simple",
    "parameters": {}
  },
  "visual_protocol": {
    "type": "opencv",
    "parameters": {
      "window_name": "Circle Tracker",
      "debug_level": "basic"
    }
  },
  "drone_settings": {
    "takeoff_height": 30,
    "target_height": 30,
    "timeout": 30
  }
}
```

## Troubleshooting

### Configuration File Not Found
If you get an error about a missing configuration file:
1. Check that the file exists in the `config/` directory
2. Verify the JSON syntax is valid
3. Use `python manage_config.py` to create a new configuration

### Invalid Configuration
If the application fails to load a configuration:
1. Check the JSON syntax using `python manage_config.py` → "View configuration details"
2. Verify all required sections are present
3. Check that parameter values are within valid ranges

### Parameter Validation
The system validates configuration parameters:
- **Tracker parameters**: Must match the tracker type requirements
- **Control parameters**: PID values must be positive numbers
- **Landing parameters**: Heights and timeouts must be positive
- **Visual parameters**: Window dimensions must be positive integers

## Best Practices

1. **Start with Default**: Use the default configuration as a starting point
2. **Test Incrementally**: Make small changes and test before major modifications
3. **Backup Configurations**: Keep copies of working configurations
4. **Document Changes**: Add comments to your JSON files for complex setups
5. **Use Descriptive Names**: Name your configurations clearly (e.g., `indoor_precision.json`)

## Advanced Usage

### Command Line Configuration
You can specify a configuration file directly:
```bash
# This feature can be added to main.py if needed
python main.py --config indoor.json
```

### Environment Variables
You can override configuration values with environment variables:
```bash
export TELLO_TAKEOFF_HEIGHT=50
export TELLO_TIMEOUT=60
python main.py
```

### Configuration Validation
The system automatically validates configurations:
- Required sections are present
- Parameter types are correct
- Values are within reasonable ranges
- Dependencies between settings are satisfied

## Migration from Interactive Setup

If you've been using the interactive setup and want to create a configuration:

1. Run `python manage_config.py`
2. Select "Create new configuration"
3. Go through the setup process
4. Save the configuration with a descriptive name
5. Use the configuration file in future runs

This will save you time and ensure consistent settings across multiple runs. 