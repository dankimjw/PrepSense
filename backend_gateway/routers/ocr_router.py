"""Router for OCR receipt scanning functionality"""

import logging
import base64
import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
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


@router.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to provide better error messages"""
    errors = exc.errors()
    logger.error(f"Validation error for OCR request: {errors}")
    
    # Check for specific field errors
    for error in errors:
        if error.get('loc') and 'image_base64' in error.get('loc', []):
            if 'ensure this value has at most' in str(error.get('msg', '')):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": "Image too large. Please use a smaller image (max ~7MB after base64 encoding).",
                        "error": "image_size_exceeded"
                    }
                )
            elif 'field required' in str(error.get('msg', '')):
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": "Missing image_base64 field in request.",
                        "error": "missing_image"
                    }
                )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "errors": errors
        }
    )


class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    image_base64: str
    user_id: int = 111  # Default demo user


class ScanItemRequest(BaseModel):
    """Request model for scanning individual items"""
    image_base64: str = Field(..., max_length=10_000_000)  # ~7.5MB limit for base64
    user_id: int = 111  # Default demo user
    scan_type: str = "pantry_item"  # Can be "pantry_item", "barcode", etc.
    
    @validator('image_base64')
    def validate_base64(cls, v):
        if not v:
            raise ValueError("image_base64 cannot be empty")
        # Remove data URI prefix if present
        if v.startswith('data:'):
            v = v.split(',', 1)[-1]
        # Basic base64 validation
        try:
            # Test if it's valid base64 by attempting to decode a small portion
            base64.b64decode(v[:100] + '==', validate=True)
        except Exception:
            raise ValueError("Invalid base64 string")
        return v


class ParsedItem(BaseModel):
    """Parsed item from receipt"""
    name: str
    quantity: float = 1.0
    unit: str = "each"
    price: Optional[float] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    nutrition_info: Optional[Dict[str, Any]] = None
    expiration_date: Optional[str] = None


class OCRResponse(BaseModel):
    """Response model for OCR processing"""
    success: bool
    items: List[ParsedItem]
    raw_text: Optional[str] = None
    message: str


def get_pantry_manager(db_service = Depends(get_database_service)) -> PantryItemManagerEnhanced:
    """Dependency to get PantryItemManager instance"""
    return PantryItemManagerEnhanced(db_service)


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
        
        # If not in env, try to load from file
        if not openai_api_key:
            key_file = os.getenv("OPENAI_API_KEY_FILE", "config/openai_key.txt")
            try:
                with open(key_file, 'r') as f:
                    openai_api_key = f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read OpenAI API key from {key_file}: {str(e)}")
        
        # Also check config/openai.json
        if not openai_api_key or openai_api_key == "Please add your OpenAI API key to this file":
            try:
                import json
                with open('config/openai.json', 'r') as f:
                    config = json.load(f)
                    openai_api_key = config.get('openai_key', '')
            except Exception as e:
                logger.error(f"Failed to read OpenAI API key from config/openai.json: {str(e)}")
        
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please add your API key to config/openai_key.txt or config/openai.json"
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
                    5. Category from this list:
                       - Dairy: Milk, cheese, yogurt, butter, cream
                       - Meat: Fresh meat, poultry, processed meats
                       - Produce: Fresh fruits, vegetables, herbs
                       - Bakery: Bread, pastries, baked goods
                       - Pantry: Rice, pasta, flour, spices, oil, condiments
                       - Beverages: Juices, sodas, water, coffee, tea
                       - Frozen: Frozen foods, ice cream
                       - Snacks: Chips, crackers, candy, nuts
                       - Canned Goods: Canned vegetables, fruits, soups
                       - Deli: Prepared foods, sandwich meats
                       - Seafood: Fish, shellfish, seafood products
                       - Other: Items that don't fit other categories
                    
                    Return the data in this exact JSON format:
                    {
                        "items": [
                            {"name": "Milk", "quantity": 1, "unit": "gallon", "category": "Dairy", "price": 3.99},
                            {"name": "Bread", "quantity": 2, "unit": "loaf", "category": "Bakery", "price": 2.50}
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
            
            # Use category from OpenAI first, fallback to categorization service
            category = item.get("category")  # Get category from OpenAI response
            if not category:
                # Only use categorization service if OpenAI didn't provide category
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
                
                # Add item to pantry using smart_add_item method
                item_description = f"{item.quantity} {item.unit} {item.name}"
                result = await pantry_manager.smart_add_item(
                    user_id=user_id,
                    item_description=item_description
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


@router.post("/scan-items", response_model=OCRResponse, summary="Scan individual pantry items")
async def scan_items(
    request: ScanItemRequest,
    pantry_manager: PantryItemManagerEnhanced = Depends(get_pantry_manager),
):
    """
    Scan individual pantry items using barcode or product image recognition
    """
    try:
        # Log request details
        logger.info(f"Received scan-items request: user_id={request.user_id}, scan_type={request.scan_type}, image_size={len(request.image_base64)}")
        # Check if OpenAI API key is configured
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # If not in env, try to load from file
        if not openai_api_key:
            key_file = os.getenv("OPENAI_API_KEY_FILE", "config/openai_key.txt")
            try:
                with open(key_file, 'r') as f:
                    openai_api_key = f.read().strip()
            except Exception as e:
                logger.error(f"Failed to read OpenAI API key from {key_file}: {str(e)}")
        
        # Also check config/openai.json
        if not openai_api_key or openai_api_key == "Please add your OpenAI API key to this file":
            try:
                import json
                with open('config/openai.json', 'r') as f:
                    config = json.load(f)
                    openai_api_key = config.get('openai_key', '')
            except Exception as e:
                logger.error(f"Failed to read OpenAI API key from config/openai.json: {str(e)}")
        
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please add your API key to config/openai_key.txt or config/openai.json"
            )
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Different prompts based on scan type
        if request.scan_type == "barcode":
            system_prompt = """You are a barcode and product scanner. Analyze the image to identify the product.
            Look for:
            1. Barcode (if visible, extract the numbers)
            2. Product name (exact name from package)
            3. Brand name
            4. Quantity/Size (e.g., 16 oz, 1 lb, 500ml)
            5. Category (Dairy, Meat, Produce, Bakery, Pantry, Beverages, Frozen, Snacks, Canned Goods, etc.)
            6. Nutrition information (if visible)
            
            Return the data in this exact JSON format:
            {
                "items": [{
                    "name": "Product Name",
                    "brand": "Brand Name",
                    "product_name": "Full Product Name with Brand",
                    "quantity": 1,
                    "unit": "package/box/can/bottle",
                    "category": "Category",
                    "barcode": "123456789012",
                    "nutrition_info": {
                        "calories": 100,
                        "protein": "5g",
                        "carbs": "20g",
                        "fat": "3g"
                    }
                }]
            }
            
            Important:
            - Use the exact product name from the package
            - Include brand information
            - Extract size/quantity from the package
            - If it's a multi-pack, note that in quantity
            """
        else:
            system_prompt = """You are a product identifier. Analyze the image to identify pantry items.
            Look for:
            1. Product labels and text
            2. Brand names
            3. Product type and category
            4. Size/quantity information
            5. Any visible expiration dates
            
            Return the data in this exact JSON format:
            {
                "items": [{
                    "name": "Product Name",
                    "brand": "Brand Name",
                    "product_name": "Full Product Name",
                    "quantity": 1,
                    "unit": "appropriate unit",
                    "category": "Category",
                    "expiration_date": "YYYY-MM-DD if visible"
                }]
            }
            
            Categories: Dairy, Meat, Produce, Bakery, Pantry, Beverages, Frozen, Snacks, Canned Goods, Deli, Seafood, Other
            
            Important:
            - Identify each distinct product in the image
            - Use appropriate units (can, box, bag, bottle, jar, package, etc.)
            - Be specific with product names
            """
        
        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please identify and extract information about the product(s) in this image."
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
            max_tokens=500,
            temperature=0.1
        )
        
        # Parse the response
        content = response.choices[0].message.content
        logger.info(f"OpenAI Vision response for item scan: {content}")
        
        # Extract JSON from the response
        import json
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed_data = json.loads(json_match.group())
            else:
                parsed_data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from OpenAI response: {content}")
            parsed_data = {"items": []}
        
        # Process items
        processed_items = []
        for item in parsed_data.get("items", []):
            # Use product name or fallback to name
            product_name = item.get("product_name") or item.get("name", "Unknown Item")
            name = item.get("name", product_name)
            
            # Get brand
            brand = item.get("brand")
            if brand and brand not in name:
                display_name = f"{brand} {name}"
            else:
                display_name = name
            
            # Get quantity and unit
            quantity = float(item.get("quantity", 1.0))
            unit = item.get("unit", "each").lower()
            
            # Get category or use categorization service
            category = item.get("category")
            if not category:
                try:
                    categorization_result = await pantry_manager.categorization_service.categorize_item(display_name)
                    if categorization_result["success"]:
                        category = categorization_result["category"]
                except Exception as e:
                    logger.warning(f"Failed to categorize item {display_name}: {str(e)}")
                    category = "Other"
            
            # Calculate default expiration based on category
            expiration_date = item.get("expiration_date")
            if not expiration_date:
                expiration_days = {
                    "Dairy": 7,
                    "Meat": 3,
                    "Seafood": 2,
                    "Produce": 5,
                    "Bakery": 5,
                    "Frozen": 180,
                    "Canned Goods": 730,
                    "Pantry": 365,
                    "Beverages": 180,
                    "Snacks": 90,
                }.get(category, 30)
                
                from datetime import timedelta
                exp_date = datetime.now().date() + timedelta(days=expiration_days)
                expiration_date = exp_date.isoformat()
            
            processed_items.append(ParsedItem(
                name=display_name,
                quantity=quantity,
                unit=unit,
                category=category,
                barcode=item.get("barcode"),
                brand=brand,
                product_name=product_name,
                nutrition_info=item.get("nutrition_info"),
                expiration_date=expiration_date
            ))
        
        return OCRResponse(
            success=True,
            items=processed_items,
            raw_text=None,
            message=f"Successfully identified {len(processed_items)} item(s)"
        )
        
    except Exception as e:
        logger.error(f"Error scanning items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan items: {str(e)}"
        )