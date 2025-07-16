"""Router for OCR receipt scanning functionality"""

import logging
import base64
import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import openai
import os
from datetime import datetime

from backend_gateway.config.database import get_database_service
from backend_gateway.services.pantry_item_manager_enhanced import PantryItemManagerEnhanced
from backend_gateway.services.practical_food_categorization import PracticalFoodCategorizationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"],
    responses={404: {"description": "Not found"}},
)


class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    image_base64: str
    user_id: int = 111  # Default demo user


class ParsedItem(BaseModel):
    """Parsed item from receipt"""
    name: str
    quantity: float = 1.0
    unit: str = "each"
    price: Optional[float] = None
    category: Optional[str] = None


class OCRResponse(BaseModel):
    """Response model for OCR processing"""
    success: bool
    items: List[ParsedItem]
    raw_text: Optional[str] = None
    message: str


def get_pantry_manager(db_service = Depends(get_database_service)) -> PantryItemManagerEnhanced:
    """Dependency to get PantryItemManager instance"""
    categorization_service = PracticalFoodCategorizationService(db_service)
    return PantryItemManagerEnhanced(db_service, categorization_service)


@router.post("/scan-receipt", response_model=OCRResponse, summary="Scan receipt and extract items")
async def scan_receipt(
    request: OCRRequest,
    pantry_manager: PantryItemManagerEnhanced = Depends(get_pantry_manager),
):
    """
    Scan a receipt image and extract grocery items using OpenAI Vision API
    """
    try:
        # Check if OpenAI API key is configured
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Call OpenAI Vision API to analyze the receipt
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a receipt parser. Extract grocery items from the receipt image.
                    For each item, identify:
                    1. Product name (clean it up, remove brand names if generic item)
                    2. Quantity (if visible, otherwise default to 1)
                    3. Unit (if visible, otherwise guess based on item type)
                    4. Price (if visible)
                    
                    Return the data in this exact JSON format:
                    {
                        "items": [
                            {"name": "Milk", "quantity": 1, "unit": "gallon", "price": 3.99},
                            {"name": "Bread", "quantity": 2, "unit": "loaf", "price": 2.50}
                        ],
                        "raw_text": "original receipt text if readable"
                    }
                    
                    Important:
                    - Clean up product names (e.g., "DOLE BANANAS" -> "Bananas")
                    - Use appropriate units (gallon, pound, each, bag, etc.)
                    - If quantity is embedded in name (e.g., "MILK 2%"), extract it
                    - Skip non-food items, tax, totals, etc.
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please extract all grocery items from this receipt."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{request.image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        # Parse the response
        content = response.choices[0].message.content
        logger.info(f"OpenAI Vision response: {content}")
        
        # Extract JSON from the response
        import json
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed_data = json.loads(json_match.group())
            else:
                # If no JSON found, try to parse the entire content
                parsed_data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from OpenAI response: {content}")
            # Fallback: try to extract items manually
            parsed_data = {"items": [], "raw_text": content}
        
        # Process and categorize items
        processed_items = []
        for item in parsed_data.get("items", []):
            # Clean up the item name
            name = item.get("name", "").strip()
            if not name:
                continue
                
            # Get quantity and unit
            quantity = float(item.get("quantity", 1.0))
            unit = item.get("unit", "each").lower()
            
            # Standardize units
            unit_mapping = {
                "ea": "each",
                "lb": "pound",
                "lbs": "pound",
                "oz": "ounce",
                "gal": "gallon",
                "qt": "quart",
                "pt": "pint",
                "pkg": "package",
                "pack": "package",
                "btl": "bottle",
                "can": "can",
                "jar": "jar",
                "box": "box",
                "bag": "bag",
                "bunch": "bunch",
                "head": "head",
                "loaf": "loaf",
                "dozen": "dozen"
            }
            unit = unit_mapping.get(unit, unit)
            
            # Try to categorize the item
            category = None
            try:
                categorization_result = await pantry_manager.categorization_service.categorize_item(name)
                if categorization_result["success"]:
                    category = categorization_result["category"]
            except Exception as e:
                logger.warning(f"Failed to categorize item {name}: {str(e)}")
            
            processed_items.append(ParsedItem(
                name=name,
                quantity=quantity,
                unit=unit,
                price=item.get("price"),
                category=category
            ))
        
        return OCRResponse(
            success=True,
            items=processed_items,
            raw_text=parsed_data.get("raw_text"),
            message=f"Successfully extracted {len(processed_items)} items from receipt"
        )
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process receipt: {str(e)}"
        )


@router.post("/add-scanned-items", summary="Add scanned items to pantry")
async def add_scanned_items(
    items: List[ParsedItem],
    user_id: int = 111,
    pantry_manager: PantryItemManagerEnhanced = Depends(get_pantry_manager),
):
    """
    Add scanned items to user's pantry
    """
    try:
        results = []
        success_count = 0
        
        for item in items:
            try:
                # Calculate expiration date based on category
                expiration_days = {
                    "Dairy": 7,
                    "Meat": 3,
                    "Seafood": 2,
                    "Produce": 5,
                    "Bakery": 5,
                    "Frozen": 180,
                    "Canned Goods": 730,  # 2 years
                    "Pantry": 365,  # 1 year
                    "Beverages": 180,
                    "Snacks": 90,
                }.get(item.category or "Other", 30)  # Default 30 days
                
                expiration_date = datetime.now().date()
                expiration_date = expiration_date.replace(day=expiration_date.day + expiration_days)
                
                # Add item to pantry
                result = await pantry_manager.add_pantry_item(
                    user_id=user_id,
                    product_name=item.name,
                    quantity=item.quantity,
                    unit_of_measurement=item.unit,
                    expiration_date=expiration_date.strftime("%Y-%m-%d"),
                    category=item.category
                )
                
                if result["success"]:
                    success_count += 1
                    results.append({
                        "item": item.name,
                        "success": True,
                        "message": "Added successfully"
                    })
                else:
                    results.append({
                        "item": item.name,
                        "success": False,
                        "message": result.get("message", "Failed to add")
                    })
                    
            except Exception as e:
                logger.error(f"Error adding item {item.name}: {str(e)}")
                results.append({
                    "item": item.name,
                    "success": False,
                    "message": str(e)
                })
        
        return {
            "success": success_count > 0,
            "added_count": success_count,
            "total_count": len(items),
            "results": results,
            "message": f"Added {success_count} out of {len(items)} items to pantry"
        }
        
    except Exception as e:
        logger.error(f"Error adding scanned items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add items: {str(e)}"
        )