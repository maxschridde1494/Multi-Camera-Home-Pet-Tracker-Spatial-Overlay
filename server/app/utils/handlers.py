"""
Signal handlers for the detection system.

This module contains all the handler functions that respond to various signals
in the detection system.
"""
import os
import cv2
from uuid import UUID
from app.utils.logger import get_logger
from app.models import Detection
from app.db import get_session

logger = get_logger(__name__)

def handle_snapshot_storage(sender, frame, **kwargs):
    """Handle storing snapshots for high confidence detections."""
    try:
        # Format timestamp for filename
        timestamp_str = kwargs['timestamp'].strftime("%Y%m%d_%H%M%S")
        
        # Ensure snapshot directory exists
        snapshot_dir = os.getenv("SNAPSHOT_DIR", "app/snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Save the frame with detection info in filename
        filename = f"{timestamp_str}_{kwargs['camera_id']}_{kwargs['confidence']:.2f}_{kwargs['class_name']}.jpg"
        filepath = os.path.join(snapshot_dir, filename)
        
        # Save with good quality for detection images
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        logger.info(f"Saved high confidence detection snapshot: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving detection snapshot: {e}")

def handle_detection_storage(sender, frame, **kwargs):
    """Handle storing detection metadata in the database."""
    try:
        # Convert UUID string to UUID object if needed
        if isinstance(kwargs['detection_id'], str):
            kwargs['detection_id'] = UUID(kwargs['detection_id'])
            
        # Create Detection model instance
        detection = Detection(**kwargs)
        
        with get_session() as session:
            session.add(detection)
            session.commit()
            
        # Log detection info
        logger.info(
            f"Detection {kwargs['detection_id']} at {kwargs['timestamp']}: "
            f"camera={kwargs['camera_id']}, model={kwargs['model_id']}, "
            f"class={kwargs['class_name']}({kwargs['class_id']}), "
            f"conf={kwargs['confidence']:.2f}"
        )
        
    except Exception as e:
        logger.error(f"Error handling detection storage: {e}")

def handle_camera_status(sender, connected, **kwargs):
    """Log camera connection status changes."""
    status = "connected" if connected else "disconnected"
    camera_id = sender.camera_id if hasattr(sender, 'camera_id') else 'unknown'
    logger.info(f"Camera {camera_id} {status}")

def setup_handlers():
    """Initialize all signal handlers."""
    from app.utils.signals import (
        detection_made,
        high_confidence_detection_made,
        # camera_connected,
        # camera_disconnected
    )
    
    # Connect handlers to signals
    detection_made.connect(handle_detection_storage)
    high_confidence_detection_made.connect(handle_snapshot_storage)
    # camera_connected.connect(handle_camera_status, connected=True)
    # camera_disconnected.connect(handle_camera_status, connected=False) 