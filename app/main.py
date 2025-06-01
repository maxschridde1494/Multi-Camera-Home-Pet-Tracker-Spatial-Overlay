from fastapi import FastAPI
from app.db import init_db
from app.routes.detections import router as detection_router
from app.streams.streamer import RTSPManager
import os
import json
from dotenv import load_dotenv
load_dotenv()

from app.utils.logger import get_logger

logger = get_logger(__name__)

def start_streams():
    CAMERA_STREAMS = os.getenv('CAM_PROXY_CONFIG', '[]')
    camera_feeds = {}

    try:
        camera_config = json.loads(CAMERA_STREAMS)
        camera_feeds = {cam['name']: cam['stream_url'] for cam in camera_config}
    except json.JSONDecodeError:
        logger.error("Error: CAMERA_STREAMS environment variable is not valid JSON")
    except KeyError:
        logger.error("Error: Each camera config must have 'name' and 'stream_url' fields")

    rtsp_manager = RTSPManager()

    for camera_id, url in camera_feeds.items():
        rtsp_manager.add_stream(
            camera_id,
            url,
            # snapshot_dir="/app/snapshots"
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
