"""
OCR router for processing receipt/pantry item images and barcode scanning.
This module handles image processing, OpenAI vision API calls, and barcode recognition.
"""

import base64
import json
import re
import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, File, UploadFile, HTTPException
from openai import OpenAI, AuthenticationError
from pydantic import BaseModel, ConfigDict
from backend_gateway.RemoteControl_7 import is_mock_enabled, set_mock
from backend_gateway.services.practical_food_categorization import PracticalFoodCategorizationService
from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.utils.smart_cache import get_cache, invalidate_pattern_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])

def get_mime_type(image_data: bytes) -> str:
    """Determine MIME type from image data"""
    if image_data.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif image_data.startswith(b'GIF8'):
        return "image/gif"
    elif image_data.startswith(b'\x00\x00\x00\x00ftyp'):
        return "image/heic"
    else:
        return "image/jpeg"  # Default fallback

def is_ocr_mock_enabled() -> bool:
    """Check if OCR mock data is enabled"""
    return is_mock_enabled("ocr_scan")

def generate_image_hash(image_data: bytes) -> str:
    """Generate hash for image data to create cache keys"""
    return hashlib.md5(image_data).hexdigest()

# Enhanced mock data with diverse categories for better testing
MOCK_SCANNED_ITEMS = [
    {
        "name": "Bananas",
        "quantity": 6,
        "unit": "each",
        "category": "Produce",
        "brand": "Dole",
        "product_name": "Dole Bananas",
        "expiration_date": "2025-08-12"
    },
    {
        "name": "Whole Milk",
        "quantity": 1,
        "unit": "gallon",
        "category": "Dairy",
        "brand": "Organic Valley",
        "product_name": "Organic Valley Whole Milk",
        "expiration_date": "2025-08-15"
    },
    {
        "name": "Ground Beef",
        "quantity": 1,
        "unit": "lb",
        "category": "Meat",
        "brand": "Grass Run Farms",
        "product_name": "Grass Run Farms Ground Beef",
        "expiration_date": "2025-08-08"
    },
    {
        "name": "Orange Juice",
        "quantity": 64,
        "unit": "fl oz",
        "category": "Beverages",
        "brand": "Simply",
        "product_name": "Simply Orange Juice",
        "expiration_date": "2025-08-20"
    },
    {
        "name": "Canned Tomatoes",
        "quantity": 14.5,
        "unit": "oz",
        "category": "Canned Goods",
        "brand": "Hunt's",
        "product_name": "Hunt's Canned Tomatoes",
        "expiration_date": "2026-08-05"
    },
    {
        "name": "Salmon Fillet",
        "quantity": 8,
        "unit": "oz",
        "category": "Seafood",
        "brand": "Wild Planet",
        "product_name": "Wild Planet Salmon Fillet",
        "expiration_date": "2025-08-07"
    },
    {
        "name": "Greek Yogurt",
        "quantity": 32,
        "unit": "oz",
        "category": "Dairy",
        "brand": "Fage",
        "product_name": "Fage Greek Yogurt",
        "expiration_date": "2025-08-18"
    },
    {
        "name": "Sourdough Bread",
        "quantity": 1,
        "unit": "loaf",
        "category": "Bakery",
        "brand": "Dave's Killer Bread",
        "product_name": "Dave's Killer Bread Sourdough",
        "expiration_date": "2025-08-10"
    }
]

class ParsedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
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
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    items: List[ParsedItem]
    raw_text: Optional[str] = None
    message: str = ""
    debug_info: Optional[Dict[str, Any]] = None

class BarcodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    barcode: Optional[str] = None
    message: str = ""

class DebugStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    mock_data_enabled: bool
    cache_stats: Dict[str, Any]
    openai_client_status: str
    recent_detections: int
    image_hash_examples: List[str]

class MockDataConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    use_mock_data: bool

# Store recent detections for debugging
_recent_detections = []

@router.post("/scan-items", response_model=OCRResponse)
async def scan_items(file: UploadFile = File(...)):
    """
    Scan items from an uploaded image using OpenAI Vision API or mock data.
    Returns structured data about identified pantry items including proper categorization.
    """
    logger.info(f"🔍 Starting item scan for file: {file.filename}")
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    try:
        image_data = await file.read()
        logger.info(f"📸 Read image data: {len(image_data)} bytes")
        
        # Generate image hash for debugging
        image_hash = generate_image_hash(image_data)
        logger.info(f"🔑 Image hash: {image_hash}")
        
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client not available")
            raise HTTPException(status_code=500, detail="OpenAI client not configured")
        
        # Use the extracted logic for consistency
        result = await _scan_items_logic(image_data, client, image_hash)
        
        # Store detection result for debugging
        _recent_detections.append({
            'timestamp': datetime.now().isoformat(),
            'image_hash': image_hash,
            'filename': file.filename,
            'success': result.success,
            'items_count': len(result.items),
            'mock_used': is_ocr_mock_enabled()
        })
        
        # Keep only last 10 detections
        if len(_recent_detections) > 10:
            _recent_detections.pop(0)
        
        return result
        
    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=401, detail="OpenAI authentication failed. Please check API key.")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/scan-barcode", response_model=BarcodeResponse)
async def scan_barcode(file: UploadFile = File(...)):
    """
    Scan barcode from an uploaded image using OpenAI Vision API.
    """
    logger.info(f"Starting barcode scan for file: {file.filename}")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    try:
        image_data = await file.read()
        logger.info(f"Read image data: {len(image_data)} bytes")
        
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client not available")
            raise HTTPException(status_code=500, detail="OpenAI client not configured")
        
        mime_type = get_mime_type(image_data)
        processed_image_base64 = base64.b64encode(image_data).decode('utf-8')

        system_prompt = """You are a barcode reader. Look for any barcode (UPC, EAN, QR code, or other) in this image.
        If you find a barcode, return the numbers you can read.
        
        Return a JSON object with:
        - 'barcode': The barcode number as a string (or null if no barcode found)
        - 'type': The type of barcode (UPC, EAN, QR, etc.) if identifiable
        
        If no barcode is visible, return: {"barcode": null, "type": null}
        """

        logger.info("Calling OpenAI API for barcode scan")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
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
            max_tokens=300,
        )

        content = response.choices[0].message.content
        logger.debug(f"OpenAI response: {content}")

        try:
            # Extract JSON from response
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            parsed_json = json.loads(json_str)
            barcode = parsed_json.get("barcode")
            
            if barcode:
                logger.info(f"Barcode found: {barcode}")
                return BarcodeResponse(
                    success=True,
                    barcode=str(barcode),
                    message="Barcode successfully detected"
                )
            else:
                logger.info("No barcode found in image")
                return BarcodeResponse(
                    success=False,
                    barcode=None,
                    message="No barcode found in the image"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return BarcodeResponse(
                success=False,
                barcode=None,
                message="Could not parse barcode from image analysis"
            )

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(status_code=401, detail="OpenAI authentication failed")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Core scan logic extracted for testing
async def _scan_items_logic(image_data: bytes, client: OpenAI, image_hash: Optional[str] = None) -> OCRResponse:
    """
    Core logic for scanning items from image data. Used by scan_items endpoint and for isolated testing.
    """
    if not image_hash:
        image_hash = generate_image_hash(image_data)
    
    # Create cache key for this specific image
    cache_key = f"ocr_scan_{image_hash}"
    cache = get_cache()
    
    debug_info = {
        'image_hash': image_hash,
        'cache_key': cache_key,
        'mock_enabled': is_ocr_mock_enabled(),
        'cache_hit': False,
        'openai_called': False
    }
    
    # If mock data flag is set, return mock scanned items
    if is_ocr_mock_enabled():
        logger.info("🎭 Using mock data for item scan")
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
        
        debug_info['source'] = 'mock_data'
        
        return OCRResponse(
            success=True,
            items=processed_items,
            message=f"Successfully identified {len(processed_items)} item(s) (mock data)",
            debug_info=debug_info
        )
    
    # Check cache for this specific image hash (only if not bypassed)
    cached_result = cache.get(cache_key, ttl=3600)  # 1 hour cache
    if cached_result:
        logger.info(f"📋 Cache hit for image hash: {image_hash}")
        debug_info['cache_hit'] = True
        debug_info['source'] = 'cache'
        
        # Return cached result with updated debug info
        if hasattr(cached_result, 'debug_info'):
            # Create a new response with updated debug info to avoid modifying cached object
            return OCRResponse(
                success=cached_result.success,
                items=cached_result.items,
                raw_text=cached_result.raw_text,
                message=cached_result.message,
                debug_info=debug_info
            )
        
        return cached_result
    
    logger.info(f"🚀 Making fresh OpenAI detection call for image hash: {image_hash}")
    debug_info['openai_called'] = True
    
    mime_type = get_mime_type(image_data)
    processed_image_base64 = base64.b64encode(image_data).decode('utf-8')

    system_prompt = """You are a product identifier. Analyze the image to identify pantry items.
    Look for:
    - Product names
    - Brand names
    - Quantity with appropriate units based on product type
    - Barcodes
    - Food category classification

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
    - 'category': Classify the item into one of these categories:
      * 'Produce' - Fresh fruits and vegetables
      * 'Dairy' - Milk, cheese, yogurt, butter
      * 'Meat' - Fresh meat and poultry
      * 'Seafood' - Fish and shellfish
      * 'Beverages' - Drinks, juices, sodas
      * 'Bakery' - Bread, pastries, baked goods
      * 'Frozen' - Frozen foods
      * 'Canned Goods' - Canned items
      * 'Pantry' - Dry goods, spices, condiments
      * 'Snacks' - Chips, crackers, bars
      * 'Other' - Items that don't fit other categories
    - 'barcode': The barcode number (if visible)

    Rules:
    - Be specific with product names
    - Always assign a category - guess the most appropriate one if uncertain
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
        debug_info['openai_model'] = response.model
        # Convert usage to serializable dict avoiding Pydantic serialization issues
        if response.usage:
            debug_info['openai_usage'] = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        else:
            debug_info['openai_usage'] = None
        
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
        debug_info['parse_error'] = str(e)
        debug_info['raw_response'] = content[:500] + "..." if len(content) > 500 else content
        
        return OCRResponse(
            success=False,
            items=[],
            raw_text=content,
            message="Could not parse items from the image analysis.",
            debug_info=debug_info
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
            
            # Check if OpenAI provided a category
            openai_category = item.get("category")
            if openai_category and openai_category != "Other":
                # Trust OpenAI's category assignment
                category = openai_category
                logger.info(f"Using OpenAI category for {product_name}: {category}")
            else:
                # Use categorization service as fallback with correct parameter
                try:
                    categorization_result = await categorization_service.categorize_food_item(display_name)
                    # Map our internal categories to display categories
                    category_mapping = {
                        'produce_countable': 'Produce',
                        'produce_measurable': 'Produce', 
                        'liquids': 'Beverages',
                        'dry_goods': 'Pantry',
                        'meat_seafood': 'Meat',
                        'dairy': 'Dairy',
                        'snacks_bars': 'Snacks',
                        'packaged_snacks': 'Snacks',
                        'frozen_foods': 'Frozen'
                    }
                    category = category_mapping.get(categorization_result.category, 'Other')
                    logger.info(f"Categorized {product_name} as: {category} (from {categorization_result.category})")
                except Exception as cat_error:
                    logger.error(f"Error categorizing {product_name}: {str(cat_error)}")
                    # Intelligent fallback based on item name patterns
                    category = _determine_fallback_category(display_name)
                    logger.info(f"Using fallback category for {product_name}: {category}")
            
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
    
    debug_info['processed_items_count'] = len(processed_items)
    debug_info['source'] = 'openai_fresh'
    
    result = OCRResponse(
        success=bool(processed_items),
        items=processed_items,
        raw_text=content if not processed_items else None,
        message=f"Successfully identified {len(processed_items)} item(s)" if processed_items else "No items could be identified in the image",
        debug_info=debug_info
    )
    
    # Cache the result for this specific image
    if processed_items:
        cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        logger.info(f"💾 Cached result for image hash: {image_hash}")
    
    if processed_items:
        logger.info(f"✅ FINAL RESULT: Returning {len(processed_items)} processed items to client")
        for i, item in enumerate(processed_items[:3]):  # Log first 3 items
            logger.info(f"  ➤ {item.name}: {item.quantity} {item.unit} (Category: {item.category})")
        if len(processed_items) > 3:
            logger.info(f"  ➤ ... and {len(processed_items) - 3} more items")
    else:
        logger.warning("⚠️  No items identified in the image")
    
    return result

def _determine_fallback_category(item_name: str) -> str:
    """
    Intelligent fallback category determination based on item name patterns.
    This replaces the generic 'dry_goods' fallback with more specific categorization.
    Pattern matching order is optimized to handle edge cases correctly.
    """
    item_lower = item_name.lower()
    
    # Check specific patterns first (most specific to least specific)
    
    # Beverages patterns (check first for juice items)
    if any(word in item_lower for word in ['juice', 'soda', 'water', 'coffee', 'tea', 'beer', 'wine', 'drink']):
        return 'Beverages'
    
    # Canned goods patterns (check before produce for canned items)
    if any(word in item_lower for word in ['canned', 'can', 'jar', 'sauce', 'soup']):
        return 'Canned Goods'
    
    # Frozen patterns (check before dairy for ice cream)
    if any(word in item_lower for word in ['frozen', 'ice cream']):
        return 'Frozen'
    
    # Produce patterns
    if any(word in item_lower for word in ['apple', 'banana', 'orange', 'tomato', 'potato', 'onion', 'carrot', 'lettuce', 'spinach', 'broccoli', 'fruit', 'vegetable']):
        return 'Produce'
    
    # Dairy patterns
    if any(word in item_lower for word in ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg']):
        return 'Dairy'
    
    # Meat/Seafood patterns
    if any(word in item_lower for word in ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'ham', 'bacon']):
        return 'Meat'
    
    # Bakery patterns
    if any(word in item_lower for word in ['bread', 'roll', 'bagel', 'muffin', 'cake', 'cookie', 'pastry']):
        return 'Bakery'
    
    # Snacks patterns
    if any(word in item_lower for word in ['chips', 'crackers', 'bar', 'nuts', 'popcorn', 'candy']):
        return 'Snacks'
    
    # Default to Pantry for dry goods and unknown items
    return 'Pantry'

# === DIAGNOSTIC ENDPOINTS ===

@router.get("/debug/status", response_model=DebugStatusResponse)
async def get_debug_status():
    """
    Get comprehensive OCR pipeline status for debugging wrong item detection.
    """
    cache = get_cache()
    cache_stats = cache.get_stats()
    
    # Check OpenAI client status
    try:
        client = get_openai_client()
        openai_status = "✅ Available"
    except Exception as e:
        openai_status = f"❌ Error: {str(e)}"
    
    # Generate sample image hashes for reference
    sample_images = [
        b"sample_image_1",
        b"sample_image_2", 
        b"different_content"
    ]
    sample_hashes = [generate_image_hash(data) for data in sample_images]
    
    return DebugStatusResponse(
        mock_data_enabled=is_ocr_mock_enabled(),
        cache_stats={
            **cache_stats,
            'ocr_cache_entries': len([k for k in cache.cache.keys() if 'ocr_scan_' in k])
        },
        openai_client_status=openai_status,
        recent_detections=len(_recent_detections),
        image_hash_examples=sample_hashes
    )

@router.get("/debug/recent-detections")
async def get_recent_detections():
    """
    Get recent detection results for debugging.
    """
    return {
        "recent_detections": _recent_detections,
        "total_count": len(_recent_detections)
    }

@router.post("/debug/clear-cache")
async def clear_ocr_cache():
    """
    Clear OCR-related cache entries to force fresh detection.
    """
    try:
        cache = get_cache()
        
        # Find and clear OCR-related cache entries
        ocr_keys = [key for key in cache.cache.keys() if 'ocr_scan_' in key]
        
        for key in ocr_keys:
            cache.delete(key)
        
        # Also use the pattern invalidation function
        invalidate_pattern_cache('ocr_scan_')
        
        logger.info(f"🧹 Cleared {len(ocr_keys)} OCR cache entries")
        
        return {
            "success": True,
            "cleared_entries": len(ocr_keys),
            "message": f"Cleared {len(ocr_keys)} OCR cache entries"
        }
        
    except Exception as e:
        logger.error(f"Error clearing OCR cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.post("/debug/test-detection")
async def test_detection_pipeline():
    """
    Test the detection pipeline with various scenarios.
    """
    test_results = []
    
    # Test 1: Mock data status
    mock_enabled = is_ocr_mock_enabled()
    test_results.append({
        "test": "Mock Data Check",
        "status": "✅ PASS" if not mock_enabled else "⚠️  WARNING",
        "result": f"Mock data is {'enabled' if mock_enabled else 'disabled'}",
        "recommendation": "Disable mock data for real detection" if mock_enabled else "Mock data properly disabled"
    })
    
    # Test 2: OpenAI client
    try:
        client = get_openai_client()
        openai_test = {
            "test": "OpenAI Client",
            "status": "✅ PASS",
            "result": "Client available",
            "recommendation": "OpenAI integration ready"
        }
    except Exception as e:
        openai_test = {
            "test": "OpenAI Client", 
            "status": "❌ FAIL",
            "result": f"Error: {str(e)}",
            "recommendation": "Fix OpenAI API key configuration"
        }
    test_results.append(openai_test)
    
    # Test 3: Cache system
    cache = get_cache()
    cache_stats = cache.get_stats()
    test_results.append({
        "test": "Cache System",
        "status": "✅ PASS",
        "result": f"Cache operational with {cache_stats['size']} entries",
        "recommendation": "Cache system working normally"
    })
    
    # Test 4: Image hash consistency
    test_data = b"test_image_content"
    hash1 = generate_image_hash(test_data)
    hash2 = generate_image_hash(test_data)
    test_results.append({
        "test": "Image Hash Consistency",
        "status": "✅ PASS" if hash1 == hash2 else "❌ FAIL",
        "result": f"Hashes match: {hash1 == hash2}",
        "recommendation": "Image hashing working correctly" if hash1 == hash2 else "Fix image hash generation"
    })
    
    return {
        "test_summary": {
            "total_tests": len(test_results),
            "passed": len([t for t in test_results if "✅ PASS" in t["status"]]),
            "warnings": len([t for t in test_results if "⚠️ " in t["status"]]),
            "failed": len([t for t in test_results if "❌ FAIL" in t["status"]])
        },
        "test_results": test_results,
        "recommendations": [
            "🔄 Clear cache if getting stale results",
            "🎭 Disable mock data for real detection testing", 
            "🤖 Ensure OpenAI API key is properly configured",
            "📸 Use different images to test detection accuracy",
            "🔍 Check recent detections endpoint to monitor results"
        ]
    }

@router.post("/debug/force-fresh-detection")
async def force_fresh_detection(file: UploadFile = File(...)):
    """
    Force fresh detection by bypassing cache and mock data.
    """
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    try:
        image_data = await file.read()
        image_hash = generate_image_hash(image_data)
        
        # Clear any existing cache for this image
        cache_key = f"ocr_scan_{image_hash}"
        cache = get_cache()
        cache.delete(cache_key)
        
        # Temporarily disable mock data
        original_mock_state = is_ocr_mock_enabled()
        if original_mock_state:
            set_mock("ocr_scan", False)
        
        try:
            # Get OpenAI client
            client = get_openai_client()
            if not client:
                raise HTTPException(status_code=500, detail="OpenAI client not configured")
            
            # Force fresh detection
            result = await _scan_items_logic(image_data, client, image_hash)
            
            # Add debugging info
            result.debug_info = result.debug_info or {}
            result.debug_info['forced_fresh'] = True
            result.debug_info['cache_bypassed'] = True
            result.debug_info['mock_temporarily_disabled'] = original_mock_state
            
            return result
            
        finally:
            # Restore original mock state
            if original_mock_state:
                set_mock("ocr_scan", True)
        
    except Exception as e:
        logger.error(f"Error in forced fresh detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in forced detection: {str(e)}")

# === CONFIGURATION ENDPOINTS ===

@router.post("/configure-mock-data", summary="Toggle mock data usage")
async def configure_mock_data(config: MockDataConfig):
    """Toggle the use of mock data for OCR endpoints"""
    # Update RemoteControl instead of local variable
    set_mock("ocr_scan", config.use_mock_data)
    logger.info(f"Mock data {'enabled' if config.use_mock_data else 'disabled'}")
    return {
        "success": True,
        "use_mock_data": config.use_mock_data,
        "message": f"Mock data {'enabled' if config.use_mock_data else 'disabled'}"
    }

@router.get("/mock-data-status", summary="Get current mock data status")
async def get_mock_data_status():
    """Get the current status of mock data status"""
    return {
        "use_mock_data": is_ocr_mock_enabled(),
        "message": f"Mock data is {'enabled' if is_ocr_mock_enabled() else 'disabled'}"
    }