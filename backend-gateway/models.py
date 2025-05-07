from pydantic import BaseModel
from typing import List

class FoodItem(BaseModel):
    name: str
    quantity: str
    expiration_date: str

class PantryItem(BaseModel):
    name: str
    quantity: float
    unit: str
    expiration_date: str