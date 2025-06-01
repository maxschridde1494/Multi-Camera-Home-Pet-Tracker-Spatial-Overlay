# app/streams/streamer.py
"""High-reliability RTSP reader using FFmpeg.

This module provides:
- RTSPStream: pulls frames via FFmpeg subprocess (no cv2.VideoCapture)
- RTSPStreamManager: manages multiple streams (singleton)
"""

from __future__ import annotations

import subprocess, threading, time, numpy as np, os
from typing import Dict, Optional
import cv2

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RTSPStream:
    """Continuously decodes an RTSP stream to BGR frames using FFmpeg."""

    WIDTH: int = int(os.getenv("FRAME_WIDTH", 640))
    HEIGHT: int = int(os.getenv("FRAME_HEIGHT", 480))
    PIXELS: int = WIDTH * HEIGHT * 3  # 3 channels (bgr24)

    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.pipe: Optional[subprocess.Popen] = None
        self.latest: Optional[np.ndarray] = None
        self.lock = threading.Lock()
        self.running = False

    def start(self) -> None:
        """Launch FFmpeg and start the reader thread."""
        self.running = True
        threading.Thread(target=self._reader_loop, daemon=True).start()
        logger.info(f"[{self.camera_id}] reader started → {self.rtsp_url}")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return a copy of the most recent frame (or None)."""
        with self.lock:
            return None if self.latest is None else self.latest.copy()

    def stop(self) -> None:
        """Stop the stream and terminate FFmpeg."""
        self.running = False
        if self.pipe and self.pipe.poll() is None:
            self.pipe.terminate()

    def _ffmpeg_cmd(self):
        """
        Output raw BGR frames to stdout.
        -rtsp_transport tcp      → more stable than UDP behind Docker NAT
        -vf scale                → resize
        -pix_fmt bgr24           → OpenCV-friendly pixel format
        """
        return [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-vf", f"scale={self.WIDTH}:{self.HEIGHT}",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo",
            "-loglevel", "error",
            "-"                       # stdout
        ]

    def _reader_loop(self) -> None:
        """Reader thread that pulls frames from FFmpeg."""
        try:
            self.pipe = subprocess.Popen(
                self._ffmpeg_cmd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
        except FileNotFoundError:
            logger.error("ffmpeg not installed inside the image!")
            return

        frame_bytes = self.PIXELS
        frame_count = 0

        while self.running:
            raw = self.pipe.stdout.read(frame_bytes)
            if len(raw) != frame_bytes:
                logger.warning(f"[{self.camera_id}] incomplete frame; terminating reader")
                break

            frame = np.frombuffer(raw, np.uint8).reshape((self.HEIGHT, self.WIDTH, 3))

            with self.lock:
                self.latest = frame

            frame_count += 1
            if frame_count % 60 == 0:
                logger.info(f"[{self.camera_id}] {frame_count} frames decoded")

        logger.info(f"[{self.camera_id}] reader stopped")


class RTSPStreamManager:
    """Singleton manager for multiple RTSP streams."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.streams: Dict[str, RTSPStream] = {}
        self._initialized = True

    def add_stream(self, camera_id: str, url: str) -> RTSPStream:
        """Add and start a new RTSP stream.
        
        Args:
            camera_id: Unique identifier for the camera
            url: RTSP URL to stream from
            
        Returns:
            The created RTSPStream instance
        """
        if camera_id in self.streams:
            logger.warning(f"Stream {camera_id} already exists, stopping old one")
            self.stop_stream(camera_id)

        stream = RTSPStream(camera_id, url)
        self.streams[camera_id] = stream
        stream.start()
        return stream

    def get_stream(self, camera_id: str) -> Optional[RTSPStream]:
        """Get a stream by camera ID."""
        return self.streams.get(camera_id)

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get the latest frame from a stream."""
        if stream := self.streams.get(camera_id):
            return stream.get_latest_frame()
        return None

    def stop_stream(self, camera_id: str) -> None:
        """Stop a specific stream."""
        if stream := self.streams.get(camera_id):
            stream.stop()
            del self.streams[camera_id]

    def stop_all(self) -> None:
        """Stop all streams."""
        for camera_id in list(self.streams.keys()):
            self.stop_stream(camera_id)