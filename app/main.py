from fastapi import FastAPI
from app.db import init_db
from app.routes.detections import router as detection_router
from app.rtsp.stream import RTSPStreamManager
from app.roboflow.detector import RoboflowDetectorManager
import os
import json
from dotenv import load_dotenv

load_dotenv()

from app.utils.logger import get_logger

logger = get_logger(__name__)

def start_streams():
    """Initialize and start RTSP streams and detectors."""
    CAMERA_STREAMS = os.getenv('CAM_PROXY_CONFIG', '[]')
    camera_feeds = {}

    try:
        camera_config = json.loads(CAMERA_STREAMS)
        camera_feeds = {cam['name']: cam['stream_url'] for cam in camera_config}
    except json.JSONDecodeError:
        logger.error("Error: CAMERA_STREAMS environment variable is not valid JSON")
    except KeyError:
        logger.error("Error: Each camera config must have 'name' and 'stream_url' fields")

    # Get singleton managers
    stream_manager = RTSPStreamManager()
    detector_manager = RoboflowDetectorManager()

    # Start streams and detectors
    for camera_id, url in camera_feeds.items():
        # Start stream
        stream = stream_manager.add_stream(camera_id, url)
        
        # Start detector for this stream
        detector_manager.add_detector(
            stream=stream,
            model_id=os.getenv("ROBOFLOW_MODEL_ID"),
            confidence_threshold=0.8,
            snapshot_dir="/app/snapshots"
        )

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()
    start_streams()

app.include_router(detection_router)

@app.get("/")
def root():
    return {"status": "Pet Tracker API is running"}
