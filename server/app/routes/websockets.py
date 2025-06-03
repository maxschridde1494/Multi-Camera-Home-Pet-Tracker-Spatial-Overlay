from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import Set
from datetime import datetime
import os
from sqlmodel import Session, select
from app.utils.logger import get_logger
from app.models import Detection
from app.db import get_session

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

from app.utils.signals import high_confidence_detection_made, detection_made, snapshot_made
_clients: Set[WebSocket] = set()

async def get_initial_data():
    """Get the initial data for a new websocket connection."""
    # Get last 10 detections
    with get_session() as session:
        result = session.execute(
            select(Detection)
            .order_by(Detection.timestamp.desc())
            .limit(10)
        )
        detections = result.scalars().all()
        
        # Convert timestamps to ISO format for JSON serialization
        detections_data = []
        for detection in detections:
            detection_dict = {
                "id": detection.id,
                "detection_id": str(detection.detection_id),
                "timestamp": detection.timestamp.isoformat(),
                "model_id": detection.model_id,
                "camera_id": detection.camera_id,
                "x": detection.x,
                "y": detection.y,
                "width": detection.width,
                "height": detection.height,
                "confidence": detection.confidence,
                "class_name": detection.class_name,
                "class_id": detection.class_id
            }
            detections_data.append(detection_dict)

    # Get last 5 snapshots from the snapshots directory
    snapshot_dir = os.getenv("SNAPSHOT_DIR", "app/snapshots")
    snapshots = []
    try:
        # List all files in snapshot directory
        files = os.listdir(snapshot_dir)
        # Filter for jpg files and sort by name (which includes timestamp)
        snapshots = sorted(
            [f for f in files if f.endswith('.jpg')],
            reverse=True
        )[:5]
    except Exception as e:
        logger.error(f"Error reading snapshots directory: {e}")

    return {
        "last_10_detections": detections_data,
        "last_5_snapshots": snapshots
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    logger.info(f"New client connected: {websocket}")
    
    # Send initial data
    initial_data = await get_initial_data()
    await websocket.send_json({
        "timestamp": datetime.now().isoformat(),
        "status": "connected",
        "message": "connection_made",
        "data": initial_data
    })

    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "status": "active",
                "message": "ping"
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        _clients.remove(websocket)

# broadcast on every detection
@high_confidence_detection_made.connect
async def publish_high_confidence(sender, frame, **kw):
    kw["timestamp"] = kw["timestamp"].isoformat()

    for websocket in list(_clients):
        try:
          await websocket.send_json({
                  "timestamp": datetime.now().isoformat(),
                  "status": "active",
                  "message": "high_confidence_detection_made",
                  "data": kw
              })
        except Exception as e:
            logger.error(f"{type(e)} error sending detection to client: {e}")

@detection_made.connect
async def publish_detection(sender, frame, **kw):
    kw["timestamp"] = kw["timestamp"].isoformat()

    for websocket in list(_clients):
        try:
          await websocket.send_json({
                  "timestamp": datetime.now().isoformat(),
                  "status": "active",
                  "message": "detection_made",
                  "data": kw
              })
        except Exception as e:
            logger.error(f"{type(e)} error sending detection to client: {e}")

@snapshot_made.connect
async def publish_snapshot(sender, frame, **kw):
    for websocket in list(_clients):
        try:
          await websocket.send_json({
                  "timestamp": datetime.now().isoformat(),
                  "status": "active",
                  "message": "snapshot_made",
                  "data": {"asset_path": kw["asset_path"]}
              })
        except Exception as e:
            logger.error(f"{type(e)} error sending snapshot to client: {e}")