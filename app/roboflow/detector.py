"""
Roboflow-based pet detector for processing RTSP streams.

This module provides:
- RoboflowDetector: Monitors a single RTSP stream and runs inference
- RoboflowDetectorManager: Manages multiple detectors (singleton)
"""

import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional
import cv2

from app.utils.logger import get_logger
from app.roboflow.client import create_client
from app.rtsp.stream import RTSPStream

logger = get_logger(__name__)


class RoboflowDetector:
    """Monitors an RTSP stream and runs Roboflow inference."""

    def __init__(
        self,
        stream: RTSPStream,
        model_id: str,
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        snapshot_dir: Optional[str] = None,
        snapshot_quality: int = 85
    ):
        """Initialize the detector.
        
        Args:
            stream: RTSPStream to monitor
            model_id: Roboflow model ID (e.g., "home-pet-detection/3")
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
            snapshot_dir: Optional directory to save detection frames
            snapshot_quality: JPEG quality for snapshots (0-100)
        """
        self.stream = stream
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self.interval = interval
        
        # Snapshot configuration
        self.snapshot_dir = snapshot_dir
        if snapshot_dir:
            os.makedirs(snapshot_dir, exist_ok=True)
        self.snapshot_quality = snapshot_quality
        
        # State
        self.running = False
        self.frame_counter = 0
        self.client = create_client()
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the detector thread."""
        if self.running:
            logger.warning(f"Detector for {self.stream.camera_id} already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info(f"[{self.stream.camera_id}] detector started")

    def stop(self) -> None:
        """Stop the detector thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

    def _loop(self) -> None:
        """Main detection loop."""
        while self.running:
            frame = self.stream.get_latest_frame()
            if frame is not None:
                try:
                    # Run inference
                    prediction = self.client.infer(
                        inference_input=frame,
                        model_id=self.model_id
                    )

                    # Check for high-confidence detections
                    if (predictions := prediction.get("predictions", [])):
                      logger.info(f"[{self.stream.camera_id}] prediction: {prediction}")

                      if predictions[0]["confidence"] > self.confidence_threshold:
                        # Save snapshot if configured
                        if self.snapshot_dir:
                            # Generate timestamp in format: YYYYMMDD_HHMMSS
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{timestamp}_{self.stream.camera_id}_{self.frame_counter:04d}.jpg"
                            filepath = os.path.join(self.snapshot_dir, filename)
                            
                            cv2.imwrite(
                                filepath,
                                frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), self.snapshot_quality]
                            )
                            
                            self.frame_counter += 1
                            if self.frame_counter % 10 == 0:
                                logger.info(
                                    f"[{self.stream.camera_id}] "
                                    f"Saved frame {self.frame_counter}"
                                )
                                
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    
            time.sleep(self.interval)


class RoboflowDetectorManager:
    """Singleton manager for multiple RoboflowDetector instances."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.detectors: Dict[str, RoboflowDetector] = {}
        self._initialized = True
        
    def add_detector(
        self,
        stream: RTSPStream,
        model_id: str,
        confidence_threshold: float = 0.9,
        interval: float = 1.0,
        snapshot_dir: Optional[str] = None,
        snapshot_quality: int = 85
    ) -> None:
        """Add a detector for a stream.
        
        Args:
            stream: RTSPStream to monitor
            model_id: Roboflow model ID
            confidence_threshold: Minimum confidence for detections
            interval: Seconds between inference runs
            snapshot_dir: Optional directory to save detection frames
            snapshot_quality: JPEG quality for snapshots
        """
        camera_id = stream.camera_id
        
        if camera_id in self.detectors:
            logger.warning(f"Detector for {camera_id} already exists, stopping old one")
            self.stop_detector(camera_id)

        # reset snapshot dir if it exists
        if snapshot_dir and os.path.exists(snapshot_dir):
            for file in os.listdir(snapshot_dir):
                os.remove(os.path.join(snapshot_dir, file))
            
        detector = RoboflowDetector(
            stream=stream,
            model_id=model_id,
            confidence_threshold=confidence_threshold,
            interval=interval,
            snapshot_dir=snapshot_dir,
            snapshot_quality=snapshot_quality
        )
        
        detector.start()
        self.detectors[camera_id] = detector
        
    def stop_detector(self, camera_id: str) -> None:
        """Stop a specific detector."""
        if detector := self.detectors.get(camera_id):
            detector.stop()
            del self.detectors[camera_id]
            
    def stop_all(self) -> None:
        """Stop all detectors."""
        for camera_id in list(self.detectors.keys()):
            self.stop_detector(camera_id) 