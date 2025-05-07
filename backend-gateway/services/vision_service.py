import httpx
import os

VISION_URL = os.getenv("VISION_URL", "http://localhost:8001/detect")

async def process_image(file):
    img = await file.read()
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            VISION_URL,
            files={"file": (file.filename, img, file.content_type)}
        )
        response.raise_for_status()
        return response.json()