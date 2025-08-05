"""Pantry-related Pydantic models."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class PantryItem(BaseModel):
    pantry_item_id: Optional[int]  # Optional for cases where the ID is auto-generated
    pantry_id: Optional[int]  # Reference to the Pantry table
    product_id: Optional[int]  # Reference to the FoodProducts table
    quantity: float
    unit_of_measure: str
    expiration_date: date
    unit_price: Optional[float]
    total_price: Optional[float]
    added_at: Optional[date]


class PantryDB(BaseModel):
    items: List[PantryItem]  # A list of PantryItem objects