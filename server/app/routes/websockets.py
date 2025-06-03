from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from typing import Set
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

from app.utils.signals import high_confidence_detection_made, detection_made, snapshot_made    # your blinker signal
_clients: Set[WebSocket] = set()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    logger.info(f"New client connected: {websocket}")
    
    await websocket.send_json({
        "timestamp": datetime.now().isoformat(),
        "status": "connected",
        "message": "WebSocket connection established"
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
async def publish_now(sender, frame, **kw):
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
async def publish_now(sender, frame, **kw):
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

# broadcast on every snapshot
@snapshot_made.connect
async def publish_now(sender, frame, **kw):
    for websocket in list(_clients):
        try:
          await websocket.send_json({
                  "timestamp": datetime.now().isoformat(),
                  "status": "active",
                  "message": "snapshot_made",
                  "data": kw
              })
        except Exception as e:
            logger.error(f"{type(e)} error sending snapshot to client: {e}")