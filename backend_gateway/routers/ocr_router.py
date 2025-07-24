"""Router for OCR receipt and image scanning functionality"""

import logging
import base64
import re
import imghdr
import os
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from PIL import Image
from datetime import datetime, timedelta
import openai
from openai import OpenAI

from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.config.database import get_database_service
from backend_gateway.services.pantry_item_manager_enhanced import PantryItemManagerEnhanced
from backend_gateway.services.practical_food_categorization import PracticalFoodCategorizationService

logger = logging.getLogger(__name__)

# Maximum image size (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"],
    responses={404: {"description": "Not found"}},
)

def get_mime_type(image_data: bytes) -> str:
    """Detect MIME type from image data"""
    file_type = imghdr.what(None, h=image_data)
    mime_types = {
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'heic': 'image/heic',
    }
    return mime_types.get(file_type or 'jpeg', 'image/jpeg')

def optimize_image(image_data: bytes, max_size: Tuple[int, int] = (1024, 1024), quality: int = 85) -> Tuple[bytes, str]:
    """Optimize image size and quality"""
    try:
        with Image.open(BytesIO(image_data)) as img:
            # Convert to RGB if necessary (handles PNG with alpha channel)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if needed
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to bytes buffer
            buffer = BytesIO()
            img_format = img.format or 'JPEG'
            img.save(buffer, format=img_format, quality=quality, optimize=True)
            return buffer.getvalue(), get_mime_type(buffer.getvalue())
    except Exception as e:
        logger.warning(f"Image optimization failed: {str(e)}")
        return image_data, get_mime_type(image_data)

class OCRRequest(BaseModel):
    """Request model for OCR processing"""
    image_base64: str
    user_id: int = 111  # Default demo user
    mime_type: Optional[str] = None  # Optional MIME type hint

class ScanItemRequest(BaseModel):
    """Request model for scanning individual items"""
    image_base64: str
    user_id: int = 111  # Default demo user
    scan_type: str = "pantry_item"  # Can be "pantry_item", "barcode", etc.
    mime_type: Optional[str] = None  # Optional MIME type hint

class ParsedItem(BaseModel):
    """Parsed item from receipt or image"""
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
        # Initialize OpenAI client
        try:
            client = get_openai_client()
        except ValueError as e:
            logger.error(f"OpenAI client initialization failed: {e}")
            raise HTTPException(status_code=500, detail="OpenAI service is not available")
        
        # Call OpenAI Vision API to analyze the receipt
        try:
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
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key. Please check your configuration."
            )
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API Timeout: {str(e)}")
            raise HTTPException(
                status_code=504,
                detail="OpenAI API request timed out. Please try again."
            )
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Error from OpenAI API: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process receipt: {str(e)}"
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
    Scan individual pantry items using barcode or product image recognition.
    
    Supports various image formats including JPEG, PNG, WEBP, and HEIC.
    Images are automatically optimized for size and quality.
    """
    try:
        # Initialize OpenAI client
        try:
            client = get_openai_client()
        except ValueError as e:
            logger.error(f"OpenAI client initialization failed: {e}")
            raise HTTPException(status_code=500, detail="OpenAI service is not available")
        
        # Process image data
        try:
            # Check if the base64 string has the data URL prefix
            if request.image_base64.startswith('data:'):
                # Extract the base64 part after the comma
                base64_data = request.image_base64.split(',', 1)[1]
            else:
                base64_data = request.image_base64
                
            # Decode base64 image
            try:
                image_data = base64.b64decode(base64_data)
                if len(image_data) > MAX_IMAGE_SIZE:
                    # Optimize large images
                    image_data, mime_type = optimize_image(image_data)
                else:
                    mime_type = request.mime_type or get_mime_type(image_data)
                    
                # Re-encode the optimized image for the API
                processed_image_base64 = base64.b64encode(image_data).decode('utf-8')
            except Exception as e:
                logger.error(f"Image processing error: {str(e)}")
                raise ValueError(f"Failed to process image: {str(e)}")
                
        except Exception as e:
            logger.error(f"Invalid image data: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

        # Different prompts based on scan type
        system_prompt = """You are a product identifier. Analyze the image to identify pantry items.
        Look for:
        1. Product labels and text
        2. Brand names
        3. Product type and category
        4. Size/quantity information
        
        Return the data in this exact JSON format:
        {
            "items": [{
                "name": "Product Name",
                "brand": "Brand Name",
                "product_name": "Full Product Name",
                "quantity": 1,
                "unit": "appropriate unit",
            "categ`o\`ry": "Category",
                "expiration_date": "YYYY-MM-DD if visible"
            }]
        }
        
        Categories: Dairy, Meat, Produce, Bakery, Pantry, Beverages, Frozen, Snacks, Canned Goods, Deli, Seafood, Other
        
        Important:
        - Identify each distinct product in the image
        - Use appropriate units (can, box, bag, bottle, jar, package, etc.)
        - Be specific with product names
        - If you can't identify the product, return an empty items array
        """
        logger.debug(f"Sending request to OpenAI Vision API with image of size: {len(processed_image_base64)} characters")
        
        try:
            # Call OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4-turbo",
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
                                    "url": f"data:{mime_type};base64,{processed_image_base64}",
                                    "detail": "high"  # 'low' for faster but less detailed analysis
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            logger.debug("Successfully received response from OpenAI Vision API")
        except openai.AuthenticationError as auth_error:
            logger.error(f"OpenAI Authentication Error: {str(auth_error)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key. Please check your configuration."
            )
        except openai.APITimeoutError as timeout_error:
            logger.error(f"OpenAI API Timeout: {str(timeout_error)}")
            raise HTTPException(
                status_code=504,
                detail="OpenAI API request timed out. Please try again."
            )
            
        # Parse the response
        content = response.choices[0].message.content
        logger.debug(f"OpenAI Vision response for item scan: {content}")
        
        # Extract JSON from the response
        import json
        try:
            # Clean up the response to extract valid JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed_data = json.loads(json_match.group())
            else:
                # If no JSON found, try to parse the entire content
                parsed_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {content}")
            # If parsing fails, try to extract items using regex
            items = []
            # Simple pattern to extract items (adjust based on actual response format)
            item_matches = re.finditer(r'"?name"?\s*[:=]\s*"?(.*?)"?(?:,|\n|$)', content, re.IGNORECASE)
            for match in item_matches:
                item_name = match.group(1).strip('"\'')
                if item_name and len(item_name) > 2:  # Filter out very short names
                    items.append({"name": item_name})
            parsed_data = {"items": items}
            
        # Process items
        processed_items = []
        for item in parsed_data.get("items", []):
            try:
                # Use product name or fallback to name
                product_name = item.get("product_name") or item.get("name", "Unknown Item")
                name = item.get("name", product_name)
                
                # Get brand
                brand = item.get("brand")
                if brand and brand not in name:
                    display_name = f"{brand} {name}"
                else:
                    display_name = name
                
                # Get quantity and unit with better defaults
                quantity = float(item.get("quantity", 1.0))
                unit = (item.get("unit") or "each").lower().strip('.')
                
                # Get category or use categorization service
                category = item.get("category")
                if not category and pantry_manager and hasattr(pantry_manager, 'categorization_service'):
                    try:
                        categorization_result = await pantry_manager.categorization_service.categorize_item(display_name)
                        if categorization_result and categorization_result.get("success"):
                            category = categorization_result.get("category")
                    except Exception as e:
                        logger.warning(f"Failed to categorize item {display_name}: {str(e)}")
                
                if not category:
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
            except Exception as item_error:
                logger.error(f"Error processing item {item}: {str(item_error)}")
                continue
        
        return OCRResponse(
            success=bool(processed_items),
            items=processed_items,
            raw_text=content if not processed_items else None,
            message=f"Successfully identified {len(processed_items)} item(s)" if processed_items 
                   else "No items could be identified in the image"
        )
        
    except openai.APIStatusError as api_error:
        logger.error(f"OpenAI API error: {str(api_error)}")
        raise HTTPException(
            status_code=502,
            detail=f"Error from OpenAI API: {str(api_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning items: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )