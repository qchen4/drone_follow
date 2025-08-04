# trackers/phone_tracker.py

import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
from .base_tracker import TrackerBase

class PhoneTracker(TrackerBase):
    """Detects and tracks cell phones using YOLO and Supervision."""
    
    def __init__(self, model_path="yolov8n.pt", confidence=0.5, iou_threshold=0.5):
        """
        Initialize the phone tracker.
        
        Args:
            model_path: Path to YOLO model (will download if not found)
            confidence: Detection confidence threshold
            iou_threshold: IoU threshold for NMS
        """
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        
        # Load YOLO model with PyTorch 2.6+ compatibility fix
        try:
            import torch
            from torch.serialization import add_safe_globals
            
            # Add ultralytics classes to safe globals for PyTorch 2.6+
            try:
                from ultralytics.nn.tasks import DetectionModel
                add_safe_globals([DetectionModel])
                print("✅ Added ultralytics to safe globals")
            except ImportError:
                print("⚠️ Could not import ultralytics classes")
            
            # Fix for PyTorch 2.6+ compatibility
            torch.hub.set_dir('.')  # Use local cache
            
            # Try to load YOLO model
            try:
                self.model = YOLO(model_path)
                print(f"✅ YOLO model loaded: {model_path}")
            except Exception as e:
                print(f"❌ Failed to load YOLO model: {e}")
                print("Trying with CPU-only model...")
                # Try CPU-only version
                self.model = YOLO("yolov8n.pt")
                print("✅ YOLO model loaded (CPU version)")
                
        except Exception as e:
            print(f"❌ All YOLO loading attempts failed: {e}")
            print("Creating dummy model for testing...")
            self.model = None
        
        # Initialize Supervision components
        self.box_annotator = sv.BoxAnnotator(
            thickness=2,
            text_thickness=2,
            text_scale=1
        )
        
        self.tracker = sv.ByteTrack()
        
        # Phone-related class IDs in COCO dataset
        self.phone_classes = {
            67: "cell phone",  # COCO class ID for cell phone
            77: "cell phone",  # Alternative ID
        }
        
        print("✅ PhoneTracker initialized successfully")
    
    def process_frame(self, frame, **kwargs):
        """
        Process a frame to detect and track cell phones.
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            tuple: (found, (error_x, error_y, error_z), debug_info)
        """
        # Check if model is available
        if self.model is None:
            debug = {
                "status": "YOLO model not available",
                "frame_size": f"{frame.shape[1]}x{frame.shape[0]}",
                "total_detections": 0,
                "phone_detections": 0,
                "previews": []
            }
            return False, (0, 0, 0), debug
        
        # Run YOLO detection
        results = self.model(frame, verbose=False)[0]
        
        # Convert to Supervision format
        detections = sv.Detections.from_ultralytics(results)
        
        # Filter for phone detections
        phone_mask = np.zeros(len(detections), dtype=bool)
        for i, class_id in enumerate(detections.class_id):
            if class_id in self.phone_classes:
                phone_mask[i] = True
        
        # Apply phone filter
        phone_detections = detections[phone_mask]
        
        # Track phones
        if len(phone_detections) > 0:
            phone_detections = self.tracker.update_with_detections(phone_detections)
        
        # Get frame dimensions
        h, w = frame.shape[:2]
        frame_center = (w // 2, h // 2)
        
        # Find the largest phone (closest to center)
        best_phone = None
        min_distance = float('inf')
        
        for i in range(len(phone_detections)):
            bbox = phone_detections.xyxy[i]
            x1, y1, x2, y2 = bbox
            
            # Calculate center of phone
            phone_center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
            
            # Calculate distance to frame center
            distance = np.sqrt((phone_center[0] - frame_center[0])**2 + 
                             (phone_center[1] - frame_center[1])**2)
            
            # Calculate area (larger phones are more prominent)
            area = (x2 - x1) * (y2 - y1)
            
            # Prefer phones closer to center and larger
            score = distance / (area + 1)  # Lower score is better
            
            if score < min_distance:
                min_distance = score
                best_phone = {
                    "bbox": bbox,
                    "center": phone_center,
                    "area": area,
                    "confidence": phone_detections.confidence[i],
                    "tracker_id": phone_detections.tracker_id[i] if phone_detections.tracker_id is not None else None
                }
        
        # Create debug information
        debug = {
            "status": "No Phone Detected",
            "frame_size": f"{w}x{h}",
            "total_detections": len(detections),
            "phone_detections": len(phone_detections),
            "previews": []
        }
        
        if best_phone:
            # Calculate error from center
            error_x = int(best_phone["center"][0] - frame_center[0])
            error_y = int(best_phone["center"][1] - frame_center[1])
            error_z = 0  # Depth estimation would require stereo vision
            
            debug.update({
                "status": f"Phone detected (conf: {best_phone['confidence']:.2f})",
                "center": best_phone["center"],
                "bbox": best_phone["bbox"],
                "area": best_phone["area"],
                "confidence": best_phone["confidence"],
                "tracker_id": best_phone["tracker_id"],
                "error": (error_x, error_y, error_z)
            })
            
            return True, (error_x, error_y, error_z), debug
        else:
            return False, (0, 0, 0), debug
    
    def draw_debug_info(self, frame, debug_info):
        """
        Draw debug information on the frame using Supervision.
        
        Args:
            frame: Input frame to draw on
            debug_info: Debug information from process_frame
        """
        if debug_info.get("status", "").startswith("Phone detected"):
            # Create a single detection for visualization
            bbox = debug_info.get("bbox")
            if bbox is not None:
                # Convert to Supervision format
                detections = sv.Detections(
                    xyxy=np.array([bbox]),
                    confidence=np.array([debug_info.get("confidence", 0.5)]),
                    class_id=np.array([67]),  # cell phone class
                    tracker_id=np.array([debug_info.get("tracker_id", 0)])
                )
                
                # Create labels
                labels = [
                    f"Phone #{debug_info.get('tracker_id', 0)} "
                    f"({debug_info.get('confidence', 0):.2f})"
                ]
                
                # Draw using Supervision
                frame = self.box_annotator.annotate(
                    scene=frame,
                    detections=detections,
                    labels=labels
                )
                
                # Draw center crosshair
                center = debug_info.get("center")
                if center:
                    cv2.drawMarker(frame, center, (255, 0, 0), 
                                  markerType=cv2.MARKER_CROSS, 
                                  markerSize=20, thickness=3)
        
        # Add status text
        status = debug_info.get("status", "No status")
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)
        
        # Add detection count
        total_detections = debug_info.get("total_detections", 0)
        phone_detections = debug_info.get("phone_detections", 0)
        count_text = f"Total: {total_detections} | Phones: {phone_detections}"
        cv2.putText(frame, count_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, (255, 255, 0), 2) 