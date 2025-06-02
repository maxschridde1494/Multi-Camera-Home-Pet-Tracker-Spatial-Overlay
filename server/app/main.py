import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.routes.detections import router as detection_router
from app.rtsp.stream import RTSPStreamManager
from app.roboflow.detector import RoboflowDetectorManager
from app.utils.handlers import setup_handlers
import os
import json
from dotenv import load_dotenv
from datetime import datetime

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
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.9")),
        )

app = FastAPI(root_path="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost", 
        # "ws://localhost"
    ],  # dev + traefik + ws
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    # setup_handlers()  # Initialize signal handlers before starting streams
    # start_streams()

app.include_router(detection_router)

@app.get("/")
def root():
    return {"status": "Pet Tracker API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"New client connected: {websocket}")
    await websocket.send_json({
        "timestamp": datetime.now().isoformat(),
        "type": "ping",
        "status": "connected",
        "message": "WebSocket connection established"
    })
    try:
        while True:
            # data = await websocket.receive_text()
            await asyncio.sleep(5) # (or send a ping every N seconds)
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "type": "ping",
                "status": "active",
                "message": "WebSocket connection alive"
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected")

