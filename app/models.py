from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class DetectionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    camera_id: str
    room: str
    x: float
    y: float
    confidence: float
