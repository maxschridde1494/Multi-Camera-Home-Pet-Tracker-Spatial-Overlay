from fastapi import FastAPI
from app.db import init_db
from app.routes.detections import router as detection_router

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(detection_router)

@app.get("/")
def root():
    return {"status": "Pet Tracker API is running"}
