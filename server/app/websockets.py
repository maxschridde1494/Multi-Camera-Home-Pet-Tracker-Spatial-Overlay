from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
# from typing import Set
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["RTP"])

@router.websocket("/ws")
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

# # @app.websocket("/ws")
# # async def websocket_endpoint(websocket: WebSocket):
# #     await websocket.accept()
# #     logger.info(f"New client connected: {websocket}")
# #     while True:
# #         data = await websocket.receive_text()
# #         await websocket.send_text(f"Message text was: {data}")

# # from app.utils.signals import detection_made   # your blinker signal
# # _clients: Set[WebSocket] = set()

# # @app.websocket("/ws/now")          # path is /api/ws/now via root_path
# # async def ws_now(websocket: WebSocket):
# #     await websocket.accept()
# #     _clients.add(websocket)
# #     logger.info(f"New client connected: {websocket}")
# #     # asyncio.create_task(websocket.send_json({"message": "Hello, world!"}))
# #     try:
# #         while True:                # keep connection alive
# #             await asyncio.sleep(3600)
# #     except WebSocketDisconnect:
# #         _clients.remove(websocket)

# # # broadcast on every detection
# # @detection_made.connect
# # def publish_now(sender, frame, **kw):
# #     logger.info(f"Publishing detection to {len(_clients)} clients with kw: {kw}")
# #     room = kw["camera_id"]
# #     payload = {"room": room, "ts": kw["timestamp"].isoformat()}
# #     for ws in list(_clients):
# #         asyncio.create_task(ws.send_json(payload))