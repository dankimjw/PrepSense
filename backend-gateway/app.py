from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import httpx, os

# PYTHONPATH=$(pwd) uvicorn PrepSense.backend-gateway.app:app --port 8000 --reload
VISION_URL = os.getenv("VISION_URL", "http://localhost:8001/detect")

app = FastAPI(title="Gateway API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"])

@app.post("/v1/images/upload")
async def upload(file: UploadFile = File(...)):
    img = await file.read()
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.post(VISION_URL, files={"file": (file.filename, img, file.content_type)})
        resp.raise_for_status()
    return resp.json()
