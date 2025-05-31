from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import DetectionLog
from app.db import SessionLocal

router = APIRouter(prefix="/detections", tags=["Detections"])

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

@router.post("/")
async def log_detection(detection: DetectionLog, session: AsyncSession = Depends(get_session)):
    session.add(detection)
    await session.commit()
    await session.refresh(detection)
    return detection

@router.get("/")
async def list_detections(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(DetectionLog))
    return result.all()
