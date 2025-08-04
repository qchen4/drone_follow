# Dynamic Precision Landing with Target Detection

This document describes the implementation of dynamic precision landing with target detection for the Tello drone project.

## Overview

The precision landing system offers multiple approaches to achieve accurate landing on a target marked with an ArUco marker:

### Precision Landing Protocol
1. **SEARCH**: Locate the target marker
2. **ALIGN**: Center on target and align orientation
3. **APPROACH**: Follow a converging spiral path toward the target
4. **TOUCHDOWN**: Execute landing when conditions are met

### Continuous Glide Landing Protocol
- **Continuous Descent**: Smoothly descends while maintaining target alignment
- **Adaptive Speed**: Adjusts descent rate based on alignment quality
- **Automatic Landing**: Uses time-of-flight sensor to detect ground contact

## Components

### 1. PrecisionArucoTracker (`trackers/precision_aruco_tracker.py`)

Enhanced ArUco tracker with pose estimation capabilities:

- **Pose Estimation**: Uses OpenCV's ArUco pose estimation to calculate 3D position and orientation
- **Distance Calculation**: Computes distance to marker in centimeters
- **Area Percentage**: Calculates what percentage of the frame the marker occupies
- **Yaw Alignment**: Determines relative orientation between drone and marker

**Key Features:**
- Camera calibration support (with default Tello camera parameters)
- Robust marker detection with optimized parameters
- Real-time pose estimation
- Debug visualization

### 2. PrecisionLandingProtocol (`landing_protocols/precision_landing.py`)

Advanced landing protocol implementing the three-phase approach:

**Phase 1: SEARCH**
- Executes gentle circular search pattern when no target is detected
- Returns to search mode if target is lost for more than 2 seconds

**Phase 2: ALIGN**
- Centers the drone on the target marker
- Aligns yaw orientation to match the marker
- Uses PID controllers for smooth movement
- Transitions to APPROACH when alignment criteria are met

**Phase 3: APPROACH**
- Implements converging spiral descent toward the target
- Blends spiral movement with target centering
- Gradually reduces spiral radius as it approaches
- Monitors area percentage and distance for touchdown decision

**Phase 4: TOUCHDOWN**
- Executes landing when marker fills target percentage of frame
- Ensures minimum distance requirements are met

### 3. ContinuousGlideLanding (`landing_protocols/continuous_glide_landing.py`)

Smooth continuous descent landing protocol:

**Key Features:**
- **Adaptive Descent**: Adjusts descent speed based on target alignment
- **Continuous Tracking**: Maintains horizontal position while descending
- **Automatic Detection**: Uses time-of-flight sensor for ground detection
- **Smooth Operation**: No discrete phases, continuous operation

**Descent Control:**
- When well-aligned: Maximum descent rate
- When misaligned: Reduced descent rate
- Uses error magnitude to compute optimal descent speed

### 4. GridVisualProtocol (`visual_protocols/grid_visual.py`)

Multi-pane debugging visualization:

**Key Features:**
- **Grid Layout**: Arranges multiple diagnostic views in a configurable grid
- **Multiple Views**: Raw frame, tracker candidates, alignment indicators, debug text
- **Customizable**: Configurable grid size and cell dimensions
- **Real-time Debugging**: Shows multiple perspectives simultaneously

**Default 2×2 Layout:**
- **Cell 0**: Raw camera frame
- **Cell 1**: Tracker view with candidate circles and bounding boxes
- **Cell 2**: Alignment view with crosshairs and target center
- **Cell 3**: Text panel with debug information

## Usage

### Quick Start

1. **Print an ArUco marker**:
   ```bash
   python test_precision_landing.py
   # Choose option 1 to generate a test marker
   ```

2. **Run the main application**:
   ```bash
   python main.py
   ```

3. **Select options**:
   - Tracker: Choose option 6 (Precision ArUco)
   - Landing: Choose option 3 (Precision) or 4 (Continuous Glide)
   - Visual: Choose option 3 (Grid Debug) for multi-pane debugging
   - Configure parameters as prompted

### Configuration Parameters

#### Tracker Parameters
- **Marker Size**: Physical size of ArUco marker in centimeters (default: 15.0)
- **Camera Matrix**: Camera calibration parameters (uses default Tello values)

#### Landing Parameters

**Precision Landing:**
- **Target Area Percentage**: Percentage of frame the marker should fill for landing (default: 15.0%)
- **Minimum Distance**: Minimum distance in cm before landing (default: 20.0cm)
- **Spiral Radius**: Initial spiral radius in cm (default: 50.0cm)
- **Alignment Threshold**: Yaw alignment threshold in degrees (default: 5.0°)
- **Position Threshold**: Position alignment threshold in pixels (default: 10px)

**Continuous Glide Landing:**
- **Descent Gain**: Coefficient for scaling descent velocity (default: 0.3)
- **Min Descent Speed**: Minimum downward speed in cm/s (default: 10)
- **Max Descent Speed**: Maximum downward speed in cm/s (default: 25)
- **Height Threshold**: Altitude in cm for landing detection (default: 20.0)
- **Timeout**: Maximum landing time in seconds (default: 30.0)

## Technical Details

### Pose Estimation

The system uses OpenCV's `estimatePoseSingleMarkers` function to calculate:
- Translation vector (x, y, z) in camera coordinates
- Rotation vector (roll, pitch, yaw)
- Distance to marker
- Relative orientation

### Spiral Approach Algorithm

The spiral approach combines two movement components:

1. **Spiral Movement**: Circular motion with decreasing radius
   ```python
   spiral_radius = initial_radius * (tightening_rate ** (angle / (2*π)))
   x_spiral = spiral_radius * cos(angle)
   y_spiral = spiral_radius * sin(angle)
   ```

2. **Target Centering**: Proportional control toward target center
   ```python
   x_center = error_x * proportional_gain
   y_center = error_y * proportional_gain
   ```

3. **Blending**: Combines spiral and centering based on proximity
   ```python
   blend_factor = min(area_percentage / target_area, 1.0)
   x_cmd = (1 - blend_factor) * x_spiral + blend_factor * x_center
   ```

### PID Control

The system uses PID controllers for smooth movement:
- **Position PID**: Controls x, y movement with gains (0.3, 0.01, 0.1)
- **Yaw PID**: Controls rotation with gains (0.5, 0.01, 0.1)

### Touchdown Decision

Landing is triggered when both conditions are met:
1. Marker area percentage ≥ target percentage
2. Distance to marker ≤ minimum distance

## Testing

### Test Script

Use the provided test script to validate functionality:

```bash
python test_precision_landing.py
```

**Available Tests:**
1. Generate test ArUco marker
2. Test tracker with webcam
3. Simulate precision landing protocol
4. Simulate continuous glide landing protocol
5. Test grid visual protocol
6. Run full precision landing (requires Tello)

### Manual Testing

1. **Marker Detection Test**:
   - Print the generated ArUco marker
   - Place it on a flat surface
   - Run tracker test to verify detection

2. **Pose Estimation Test**:
   - Move camera around the marker
   - Verify distance and angle calculations
   - Check area percentage measurements

3. **Landing Simulation**:
   - Run simulation to verify phase transitions
   - Check parameter configurations
   - Validate control algorithms

## Troubleshooting

### Common Issues

1. **Marker Not Detected**:
   - Ensure good lighting conditions
   - Check marker size configuration
   - Verify marker is not damaged or wrinkled
   - Try adjusting detection parameters

2. **Poor Pose Estimation**:
   - Calibrate camera if possible
   - Ensure marker is flat and undistorted
   - Check marker size accuracy
   - Verify camera matrix parameters

3. **Unstable Landing**:
   - Adjust PID gains
   - Increase position/alignment thresholds
   - Reduce spiral radius
   - Check for wind or environmental factors

### Parameter Tuning

**For Better Detection:**
- Increase `minMarkerPerimeterRate` for smaller markers
- Adjust `adaptiveThreshConstant` for lighting conditions
- Modify `errorCorrectionRate` for marker quality

**For Smoother Movement:**
- Reduce PID gains for less aggressive control
- Increase position threshold for more tolerance
- Adjust spiral parameters for gentler approach

**For More Accurate Landing:**
- Decrease target area percentage for closer landing
- Reduce minimum distance threshold
- Tighten alignment thresholds

## Safety Considerations

1. **Always test in open areas** with sufficient clearance
2. **Start with conservative parameters** and adjust gradually
3. **Monitor battery level** during extended operations
4. **Have emergency stop procedures** ready
5. **Test marker detection** before flight
6. **Verify landing area** is clear of obstacles

## Future Enhancements

Potential improvements for the precision landing system:

1. **Multi-Marker Support**: Use multiple markers for redundancy
2. **Adaptive Parameters**: Automatically adjust based on conditions
3. **Obstacle Avoidance**: Integrate with obstacle detection
4. **Wind Compensation**: Account for environmental factors
5. **Landing Zone Validation**: Verify landing area safety
6. **Recovery Procedures**: Handle failed landing attempts

## Dependencies

- OpenCV 4.x with ArUco support
- NumPy for numerical computations
- djitellopy for Tello control
- Existing project dependencies

## License

This precision landing implementation is part of the drone project and follows the same licensing terms. 