"""Example router for pantry CRUD endpoints."""

# filepath: /Users/danielkim/_Capstone/prepsense-app/PrepSense/backend-gateway/routers/pantry.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from backend_gateway.services.pantry_service import get_pantry_items, add_pantry_item

router = APIRouter()

@router.get("/items")
async def list_pantry_items(db: Session = Depends(get_db)):
    return get_pantry_items(db)

@router.post("/items")
async def add_item(item: PantryItem, db: Session = Depends(get_db)):
    return add_pantry_item(db, item)