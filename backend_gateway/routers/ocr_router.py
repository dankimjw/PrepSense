"""Router for OCR receipt and image scanning functionality"""

import logging
import base64
import re
import imghdr
import os
import json
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from PIL import Image
from datetime import datetime, timedelta
from openai import OpenAI, AuthenticationError
import openai
from fastapi import FastAPI

from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.config.database import get_database_service
from backend_gateway.services.pantry_item_manager_enhanced import PantryItemManagerEnhanced
from backend_gateway.services.practical_food_categorization import PracticalFoodCategorizationService
from backend_gateway.RemoteControl_7 import is_ocr_mock_enabled, set_mock

logger = logging.getLogger(__name__)

# Global variable to control mock data - DEPRECATED, use RemoteControl instead
use_mock_data = False

# Maximum image size (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# Mock data for scanned items
MOCK_SCANNED_ITEMS = [
    {
        "name": "Trader Joe's Organic Joe's O's Pasta",
        "quantity": 15,
        "unit": "oz",
        "category": "Canned Goods",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Organic Joe's O's Pasta",
        "expiration_date": "2026-07-24"
    },
    {
        "name": "Trader Joe's Organic Mini Cheese Sandwich Crackers",
        "quantity": 7.5,
        "unit": "oz",
        "category": "Snacks",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Organic Mini Cheese Sandwich Crackers",
        "expiration_date": "2026-01-20"
    },
    {
        "name": "Trader Joe's Organic Mini Peanut Butter Sandwich Crackers",
        "quantity": 7.5,
        "unit": "oz",
        "category": "Snacks",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Organic Mini Peanut Butter Sandwich Crackers",
        "expiration_date": "2026-01-20"
    },
    {
        "name": "Trader Joe's Italian Linguine Pasta",
        "quantity": 16,
        "unit": "oz",
        "category": "Pantry",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Italian Linguine Pasta",
        "expiration_date": "2026-07-24"
    },
    {
        "name": "Trader Joe's Italian Macaroni Pasta",
        "quantity": 16,
        "unit": "oz",
        "category": "Pantry",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Italian Macaroni Pasta",
        "expiration_date": "2026-07-24"
    },
    {
        "name": "Trader Joe's Italian Fusilli Pasta",
        "quantity": 16,
        "unit": "oz",
        "category": "Pantry",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Italian Fusilli Pasta",
        "expiration_date": "2026-07-24"
    },
    {
        "name": "Trader Joe's Italian Farfalle Pasta",
        "quantity": 16,
        "unit": "oz",
        "category": "Pantry",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's Italian Farfalle Pasta",
        "expiration_date": "2026-07-24"
    },
    {
        "name": "Trader Joe's \"this blueberry walks into a bar\" Cereal Bars",
        "quantity": 7.8,
        "unit": "oz",
        "category": "Snacks",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's \"this blueberry walks into a bar\" Cereal Bars",
        "expiration_date": "2026-01-20"
    },
    {
        "name": "Trader Joe's \"this strawberry walks into a bar\" Cereal Bars",
        "quantity": 7.8,
        "unit": "oz",
        "category": "Snacks",
        "brand": "Trader Joe's",
        "product_name": "Trader Joe's \"this strawberry walks into a bar\" Cereal Bars",
        "expiration_date": "2026-01-20"
    }
]

# Mock data for receipt items - these will be transformed into ParsedItem objects
MOCK_RECEIPT_ITEMS = [
    {"name": "PL Tortilla's", "quantity": 1, "unit": "package", "category": "Bakery", "price": 6.99},
    {"name": "Cage Free All Whit", "quantity": 1, "unit": "dozen", "category": "Dairy", "price": 3.69},
    {"name": "Black Beans", "quantity": 1, "unit": "can", "category": "Canned Goods", "price": 1.29},
    {"name": "Frozen Mangoes 16 oz", "quantity": 1, "unit": "package", "category": "Frozen", "price": 2.99},
    {"name": "Whole Strawberries", "quantity": 1, "unit": "container", "category": "Produce", "price": 2.99},
    {"name": "OG LF Cottage Cheese", "quantity": 1, "unit": "container", "category": "Dairy", "price": 3.49},
    {"name": "Mahi‑Mahi Fillets", "quantity": 1, "unit": "package", "category": "Seafood", "price": 8.99},
    {"name": "California Harvest", "quantity": 1, "unit": "bag", "category": "Produce", "price": 2.69},
    {"name": "Plums Black CV", "quantity": 1.08, "unit": "lb", "category": "Produce", "price": 2.15},
    {"name": "NHP Sliced Oven Roast", "quantity": 1, "unit": "package", "category": "Deli", "price": 3.99},
    {"name": "NHP Sliced Hickory", "quantity": 1, "unit": "package", "category": "Deli", "price": 3.99},
    {"name": "Gala Apples OG", "quantity": 1.64, "unit": "lb", "category": "Produce", "price": 3.26}
]

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



class ScanRequest(BaseModel):
    image_base64: str = Field(..., alias="image_data")   # accept both keys
    mime_type: str | None = None

    model_config = ConfigDict(populate_by_name=True)     # Pydantic v2

# (no other code changes needed unless you want to rename everything to image_data)

class ParsedItem(BaseModel):
    name: str
    quantity: float
    unit: str
    category: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    nutrition_info: Optional[Dict[str, Any]] = None
    expiration_date: Optional[str] = None

class OCRResponse(BaseModel):
    success: bool
    items: List[ParsedItem]
    raw_text: Optional[str] = None
    message: Optional[str] = None

def get_pantry_manager() -> PantryItemManagerEnhanced:
    db_service = get_database_service()
    return PantryItemManagerEnhanced(db_service)

@router.post("/scan-receipt", response_model=OCRResponse, summary="Scan a receipt image")
async def scan_receipt(
    request: ScanRequest,
    client: OpenAI = Depends(get_openai_client)
):
    # If mock data flag is set, return mock receipt items
    if is_ocr_mock_enabled():
        logger.info("Using mock data for receipt scan")
        processed_items = []
        for item in MOCK_RECEIPT_ITEMS:
            # Calculate expiration date based on category
            expiration_days = {
                "Dairy": 7, "Meat": 3, "Seafood": 2, "Produce": 5, "Bakery": 5,
                "Frozen": 180, "Canned Goods": 730, "Pantry": 365, 
                "Beverages": 180, "Snacks": 90, "Deli": 7, "Other": 30
            }.get(item.get('category', 'Other'), 30)
            
            exp_date = datetime.now().date() + timedelta(days=expiration_days)
            
            processed_items.append(ParsedItem(
                name=item['name'],
                quantity=item['quantity'],
                unit=item.get('unit', 'unit'),
                category=item.get('category', 'Other'),
                barcode=None,
                brand=None,
                product_name=item['name'],
                nutrition_info=None,
                expiration_date=exp_date.isoformat()
            ))
        
        return OCRResponse(
            success=True,
            items=processed_items,
            message=f"Successfully extracted {len(processed_items)} items from the receipt (mock data)."
        )
    
    try:
        image_data = base64.b64decode(request.image_base64)
    except (base64.binascii.Error, IndexError) as e:
        logger.error(f"Invalid base64 string provided for receipt scan: {e}")
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image file size exceeds the limit of {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

    mime_type = request.mime_type or get_mime_type(image_data)
    base64_image = base64.b64encode(image_data).decode('utf-8')

    system_prompt = """You are a receipt scanning expert. Analyze the receipt image and extract all line items. 
    Return a JSON object with an 'items' array. Each item should have 'name', 'quantity', 'unit', 'category', and 'price'.
    Use appropriate units based on item category:
    - PRODUCE: 'lb', 'oz', 'each', 'bunch', 'bag' (NOT ml, L)
    - DAIRY: Liquid='gallon', 'quart', 'pint'; Solid='oz', 'lb'; Eggs='dozen'
    - MEAT/SEAFOOD: 'lb', 'oz', 'piece' (NOT ml, each)
    - BEVERAGES: 'bottle', 'can', 'liter', 'fl oz' (NOT lb)
    - BAKERY: 'loaf', 'each', 'package'
    - CANNED GOODS: 'can', 'oz', 'jar'
    Ignore taxes, totals, and non-product lines. Focus only on the purchased items.
    """

    try:
        logger.info(f"Calling OpenAI API for receipt scan with model: gpt-4o")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )
        logger.info(f"OpenAI API response received - Model: {response.model}, Usage: {response.usage}")
        content = response.choices[0].message.content
        logger.debug(f"OpenAI response content length: {len(content)} characters")
    except AuthenticationError as e:
        logger.error(f"OpenAI Authentication Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid OpenAI API key. Please check your configuration.")
    except Exception as e:
        logger.error(f"OpenAI API call failed during receipt scan: {e}")
        raise HTTPException(status_code=502, detail="Error communicating with OpenAI Vision API")

    try:
        # Find the JSON part of the response
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content
        parsed_json = json.loads(json_str)
        items = parsed_json.get("items", [])
    except (json.JSONDecodeError, AttributeError):
        items = []
        # Fallback to simple regex if JSON parsing fails
        for match in re.finditer(r'(\\b[\\w\\s]+)[\\s\\S]*?([\\d\\.]+)', content):
            items.append({"name": match.group(1).strip(), "quantity": 1, "price": float(match.group(2))})

    processed_items = [
        ParsedItem(name=item.get('name'), quantity=item.get('quantity', 1), unit='unit') 
        for item in items
    ]

    return OCRResponse(
        success=True,
        items=processed_items,
        message=f"Successfully extracted {len(processed_items)} items from the receipt."
    )

@router.post("/add-scanned-items", summary="Add scanned items to pantry")
async def add_scanned_items(
    items: List[ParsedItem],
    user_id: int = 111,
    pantry_manager: PantryItemManagerEnhanced = Depends(get_pantry_manager),
):
    # If mock data is enabled, return successful response without actually adding to database
    if is_ocr_mock_enabled():
        logger.info("Using mock data for add-scanned-items")
        success_count = len(items)
        results = [{"item": item.name, "success": True, "message": "Added successfully (mock)"} for item in items]
        return {
            "success": True,
            "added_count": success_count,
            "total_count": len(items),
            "results": results,
            "message": f"Added {success_count} of {len(items)} items (mock data)."
        }
    
    results = []
    success_count = 0
    
    for item in items:
        try:
            expiration_days = {
                "Dairy": 7, "Meat": 3, "Seafood": 2, "Produce": 5, "Bakery": 5,
                "Frozen": 180, "Canned Goods": 730, "Pantry": 365, 
                "Beverages": 180, "Snacks": 90, "Other": 30
            }.get(item.category or "Other", 30)
            
            expiration_date = datetime.now().date() + timedelta(days=expiration_days)
            
            item_description = f"{item.quantity} {item.unit} {item.name}"
            result = await pantry_manager.smart_add_item(
                user_id=user_id,
                item_description=item_description,
                expiration_date=expiration_date.isoformat()
            )
            
            if result["success"]:
                success_count += 1
                results.append({"item": item.name, "success": True, "message": "Added successfully"})
            else:
                results.append({"item": item.name, "success": False, "message": result.get("message", "Failed to add")})
                
        except Exception as e:
            logger.error(f"Error adding item {item.name}: {str(e)}")
            results.append({"item": item.name, "success": False, "message": str(e)})
    
    result = {
        "success": success_count > 0,
        "added_count": success_count,
        "total_count": len(items),
        "results": results,
        "message": f"Added {success_count} of {len(items)} items."
    }
    
    if success_count > 0:
        logger.info(f"✅ PANTRY UPDATE SUCCESS: Added {success_count}/{len(items)} items to pantry")
    else:
        logger.warning(f"⚠️  PANTRY UPDATE FAILED: Unable to add any items (0/{len(items)})")
    
    return result


@router.post("/scan-items", response_model=OCRResponse, summary="Scan items from an image")
async def scan_items(
    request: ScanRequest,
    client: OpenAI = Depends(get_openai_client)
):
    """
    Scan items from an image using OpenAI Vision API.
    
    Accepts a base64 encoded image and returns a list of identified items.
    """
    try:
        if request.image_base64.startswith('data:'):
            base64_data = request.image_base64.split(',', 1)[1]
        else:
            base64_data = request.image_base64
        try:
            image_data = base64.b64decode(base64_data)
        except (base64.binascii.Error, IndexError) as e:
            logger.error(f"Invalid base64 string: {e}")
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        if len(image_data) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image file size exceeds the limit of {MAX_IMAGE_SIZE // (1024*1024)}MB"
            )
        try:
            result = await _scan_items_logic(image_data, client)
            return result
        except HTTPException:
            raise
        except AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}")
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key. Please check your configuration.")
        except openai.APIStatusError as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
            raise HTTPException(status_code=502, detail=f"Error from OpenAI API: {str(api_error)}")
        except Exception as e:
            logger.error(f"Error scanning items: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scan_items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# Core scan logic extracted for testing
async def _scan_items_logic(image_data: bytes, client: OpenAI) -> OCRResponse:
    """
    Core logic for scanning items from image data. Used by scan_items endpoint and for isolated testing.
    """
    # If mock data flag is set, return mock scanned items
    if is_ocr_mock_enabled():
        logger.info("Using mock data for item scan")
        processed_items = []
        for item in MOCK_SCANNED_ITEMS:
            processed_items.append(ParsedItem(
                name=item['name'],
                quantity=item['quantity'],
                unit=item['unit'],
                category=item['category'],
                barcode=item.get('barcode'),
                brand=item['brand'],
                product_name=item['product_name'],
                nutrition_info=item.get('nutrition_info'),
                expiration_date=item['expiration_date']
            ))
        return OCRResponse(
            success=True,
            items=processed_items,
            message=f"Successfully identified {len(processed_items)} item(s) (mock data)"
        )
    
    mime_type = get_mime_type(image_data)
    processed_image_base64 = base64.b64encode(image_data).decode('utf-8')

    system_prompt = """You are a product identifier. Analyze the image to identify pantry items.
    Look for:
    - Product names
    - Brand names
    - Quantity with appropriate units based on product type
    - Barcodes

    Return a JSON object with an 'items' array. Each object in the array should have:
    - 'name': The product name
    - 'brand': The brand name (if visible)
    - 'quantity': The quantity as a number
    - 'unit': Use appropriate units based on product type:
      * PRODUCE: 'lb', 'oz', 'each', 'bunch', 'bag' (NOT ml, L)
      * DAIRY: Liquid='gallon', 'quart', 'pint'; Solid='oz', 'lb'; Eggs='dozen'
      * MEAT/SEAFOOD: 'lb', 'oz', 'piece' (NOT ml, each)
      * BEVERAGES: 'bottle', 'can', 'liter', 'fl oz' (NOT lb)
      * CANNED GOODS: 'can', 'oz', 'jar'
      * PANTRY: 'lb', 'oz', 'bag', 'box' for dry goods
    - 'barcode': The barcode number (if visible)

    Rules:
    - Be specific with product names
    - If you can't identify the product, return an empty items array
    """
    try:
        logger.info(f"Calling OpenAI API for item scan with model: gpt-4o")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{processed_image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
        )
        logger.info(f"OpenAI API response received - Model: {response.model}, Usage: {response.usage}")
    except AuthenticationError:
        raise  # Re-raise to be caught by the calling function
    content = response.choices[0].message.content
    logger.debug(f"OpenAI response content length: {len(content)} characters")
    try:
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content
        parsed_json = json.loads(json_str)
        items = parsed_json.get("items", [])
        logger.info(f"Parsed JSON successfully. Found {len(items)} items: {items}")
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to parse JSON from OpenAI response: {e}")
        return OCRResponse(
            success=False,
            items=[],
            raw_text=content,
            message="Could not parse items from the image analysis."
        )

    processed_items = []
    categorization_service = PracticalFoodCategorizationService()
    logger.info(f"Processing {len(items)} items from OpenAI response")
    for item in items:
        try:
            logger.info(f"Processing item: {item}")
            display_name = item.get("name", "Unknown Item")
            brand = item.get("brand")
            product_name = f"{brand} {display_name}" if brand else display_name
            quantity = item.get("quantity", 1)
            unit = item.get("unit", "count")
            
            # Check if OpenAI already provided a category
            openai_category = item.get("category")
            if openai_category and openai_category != "Other":
                # Trust OpenAI's category assignment
                category = openai_category
                logger.info(f"Using OpenAI category for {product_name}: {category}")
            else:
                # Only use categorization service if OpenAI didn't provide a category
                try:
                    categorization_result = await categorization_service.categorize_food_item(product_name)
                    category = categorization_result.category
                    logger.info(f"Categorized {product_name} as: {category}")
                except Exception as cat_error:
                    logger.error(f"Error categorizing {product_name}: {str(cat_error)}")
                    category = "Other"
            
            expiration_date = None
            if category:
                expiration_days = {
                    "Dairy": 7, "Meat": 3, "Seafood": 2, "Produce": 5, "Bakery": 5,
                    "Frozen": 180, "Canned Goods": 730, "Pantry": 365,
                    "Beverages": 180, "Snacks": 90, "Other": 30
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
            logger.info(f"Successfully processed item: {display_name} with category: {category}")
        except Exception as item_error:
            logger.error(f"Error processing item {item}: {str(item_error)}")
            continue
    result = OCRResponse(
        success=bool(processed_items),
        items=processed_items,
        raw_text=content if not processed_items else None,
        message=f"Successfully identified {len(processed_items)} item(s)" if processed_items else "No items could be identified in the image"
    )
    
    if processed_items:
        logger.info(f"✅ FINAL RESULT: Returning {len(processed_items)} processed items to client")
        for i, item in enumerate(processed_items[:3]):  # Log first 3 items
            logger.info(f"  ➤ {item.name}: {item.quantity} {item.unit} (Category: {item.category})")
        if len(processed_items) > 3:
            logger.info(f"  ➤ ... and {len(processed_items) - 3} more items")
    else:
        logger.warning("⚠️  No items identified in the image")
    
    return result


class MockDataConfig(BaseModel):
    use_mock_data: bool


@router.post("/configure-mock-data", summary="Toggle mock data usage")
async def configure_mock_data(config: MockDataConfig):
    """Toggle the use of mock data for OCR endpoints"""
    # Update RemoteControl instead of local variable
    set_mock("ocr_scan", config.use_mock_data, "ocr_router")
    logger.info(f"Mock data {'enabled' if config.use_mock_data else 'disabled'}")
    return {
        "success": True,
        "use_mock_data": config.use_mock_data,
        "message": f"Mock data {'enabled' if config.use_mock_data else 'disabled'}"
    }


@router.get("/mock-data-status", summary="Get current mock data status")
async def get_mock_data_status():
    """Get the current status of mock data usage"""
    return {
        "use_mock_data": is_ocr_mock_enabled(),
        "message": f"Mock data is {'enabled' if is_ocr_mock_enabled() else 'disabled'}"
    }