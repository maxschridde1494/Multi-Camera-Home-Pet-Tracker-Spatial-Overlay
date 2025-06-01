# app/streams/streamer.py
"""High-reliability RTSP reader + optional on-disk snapshot writing.

* RTSPStream: pulls frames via an FFmpeg subprocess (no cv2.VideoCapture).
* Snapshotter: saves the latest frame to <snapshot_dir>/<camera>.jpg every N seconds.

This lives entirely in memory except for the optional JPEG snapshot, which is
useful for validating what the container sees from the host.
"""

from __future__ import annotations

import subprocess, threading, time, numpy as np, os
from typing import Dict, Optional
import cv2

from app.utils.logger import get_logger
from app.roboflow.client import create_client

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# RTSP reader (FFmpeg -> raw BGR -> NumPy)
# ---------------------------------------------------------------------------
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

    # --------------------- public ---------------------
    def start(self) -> None:
        """Launch FFmpeg and start the reader thread."""
        # logger.info(f"Starting stream for {self.camera_id}")

        self.running = True
        threading.Thread(target=self._reader_loop, daemon=True).start()
        logger.info(f"[{self.camera_id}] reader started → {self.rtsp_url}")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return a copy of the most recent frame (or None)."""
        with self.lock:
            return None if self.latest is None else self.latest.copy()

    def stop(self) -> None:
        self.running = False
        if self.pipe and self.pipe.poll() is None:
            self.pipe.terminate()

    # --------------------- internal -------------------
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


# ---------------------------------------------------------------------------
# Snapshot writer – optional diagnostics
# ---------------------------------------------------------------------------
class Snapshotter:
    """Periodically writes frames from an RTSPStream to JPEG files on disk with incrementing counters."""

    def __init__(self, stream: RTSPStream, out_path: str, interval: float = 1.0, quality: int = 85):
        self.stream = stream
        self.out_dir = os.path.dirname(out_path)  # We'll use this as the output directory
        self.camera_id = stream.camera_id
        self.interval = interval
        self.quality = quality
        self.running = False
        self.frame_counter = 0  # Counter for naming files
        self.client = create_client()

    def start(self) -> None:
        os.makedirs(self.out_dir, exist_ok=True)
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info(f"[snapshot] saving to {self.out_dir} every {self.interval}s")

    def stop(self) -> None:
        self.running = False

    def _loop(self) -> None:
        while self.running:
            frame = self.stream.get_latest_frame()
            if frame is not None:
                prediction = self.client.infer(
                    inference_input=frame,
                    model_id="home-pet-detection/3"
                )

                if len(prediction["predictions"]) > 0 and prediction["predictions"][0]["confidence"] > 0.9:
                    logger.info(f"[{self.camera_id}] prediction: {prediction}")

                    # Create filename with incrementing counter
                    filename = f"{self.camera_id}_{self.frame_counter}.jpg"
                    filepath = os.path.join(self.out_dir, filename)
                    
                    # Save the frame
                    cv2.imwrite(filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.quality])
                    
                    # Increment counter
                    self.frame_counter += 1
                    
                    if self.frame_counter % 10 == 0:  # Log every 10 frames
                        logger.info(f"[snapshot] Saved frame {self.frame_counter} for {self.camera_id}")
                    
            time.sleep(self.interval)


# ---------------------------------------------------------------------------
# Manager that owns multiple streams (unchanged API)
# ---------------------------------------------------------------------------
class RTSPManager:
    def __init__(self):
        self.streams: Dict[str, RTSPStream] = {}
        self.snapshotters: list[Snapshotter] = []

    def add_stream(
        self,
        camera_id: str,
        url: str,
        snapshot_dir: Optional[str] = None,
        snapshot_interval: float = 1.0,
    ) -> None:
        stream = RTSPStream(camera_id, url)
        self.streams[camera_id] = stream
        stream.start()

        # optional snapshotter
        if snapshot_dir:
            out_file = os.path.join(snapshot_dir, f"{camera_id}.jpg")
            logger.info(f"Snapshotting to {out_file}")
            snap = Snapshotter(stream, out_file, interval=snapshot_interval)
            snap.start()
            self.snapshotters.append(snap)

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        s = self.streams.get(camera_id)
        return None if s is None else s.get_latest_frame()

    def stop_all(self) -> None:
        for s in self.snapshotters:
            s.stop()
        for s in self.streams.values():
            s.stop()