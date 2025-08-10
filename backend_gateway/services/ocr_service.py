"""
Core business logic for OCR-based product identification.
Handles caching, mock data, OpenAI API calls, response parsing,
and post-processing (unit validation, categorization, expiration).
"""

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from openai import AuthenticationError

from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.models.ocr_models import OCRResponse, ParsedItem
from backend_gateway.RemoteControl_7 import is_mock_enabled
from backend_gateway.services.fallback_unit_service import fallback_unit_service
from backend_gateway.services.practical_food_categorization import (
    PracticalFoodCategorizationService,
)
from backend_gateway.utils.smart_cache import get_cache, invalidate_pattern_cache

logger = logging.getLogger(__name__)

# Constants
CACHE_TTL = 3600  # Cache entries live for 1 hour
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # Max upload size: 10MB

# Enhanced mock data with diverse categories for better testing
MOCK_SCANNED_ITEMS = [
    {
        "name": "Bananas",
        "quantity": 6,
        "unit": "each",
        "category": "Produce",
        "brand": "Dole",
        "product_name": "Dole Bananas",
        "expiration_date": "2025-08-12",
    },
    {
        "name": "Whole Milk",
        "quantity": 1,
        "unit": "gallon",
        "category": "Dairy",
        "brand": "Organic Valley",
        "product_name": "Organic Valley Whole Milk",
        "expiration_date": "2025-08-15",
    },
    {
        "name": "Ground Beef",
        "quantity": 1,
        "unit": "lb",
        "category": "Meat",
        "brand": "Grass Run Farms",
        "product_name": "Grass Run Farms Ground Beef",
        "expiration_date": "2025-08-08",
    },
    {
        "name": "Orange Juice",
        "quantity": 64,
        "unit": "fl oz",
        "category": "Beverages",
        "brand": "Simply",
        "product_name": "Simply Orange Juice",
        "expiration_date": "2025-08-20",
    },
    {
        "name": "Canned Tomatoes",
        "quantity": 14.5,
        "unit": "oz",
        "category": "Canned Goods",
        "brand": "Hunt's",
        "product_name": "Hunt's Canned Tomatoes",
        "expiration_date": "2026-08-05",
    },
    {
        "name": "Salmon Fillet",
        "quantity": 8,
        "unit": "oz",
        "category": "Seafood",
        "brand": "Wild Planet",
        "product_name": "Wild Planet Salmon Fillet",
        "expiration_date": "2025-08-07",
    },
    {
        "name": "Greek Yogurt",
        "quantity": 32,
        "unit": "oz",
        "category": "Dairy",
        "brand": "Fage",
        "product_name": "Fage Greek Yogurt",
        "expiration_date": "2025-08-18",
    },
    {
        "name": "Sourdough Bread",
        "quantity": 1,
        "unit": "loaf",
        "category": "Bakery",
        "brand": "Dave's Killer Bread",
        "product_name": "Dave's Killer Bread Sourdough",
        "expiration_date": "2025-08-10",
    },
]


class OcrService:
    """
    Service encapsulating OCR processing logic:
    - Mock vs cache vs fresh API call path
    - OpenAI Vision API invocation
    - Parsing and fallback processing
    """

    def __init__(self) -> None:
        """Initialize the OCR service with cache and categorization service."""
        self.cache = get_cache()
        self.categorizer = PracticalFoodCategorizationService()
        # Track recent detections for debugging
        self.recent_detections: list[dict[str, Any]] = []

    def _generate_image_hash(self, data: bytes) -> str:
        """Compute an MD5 hash for the input bytes for cache keys."""
        return hashlib.md5(data).hexdigest()

    def _get_mime_type(self, data: bytes) -> str:
        """Infer MIME type by inspecting the magic bytes of image data."""
        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif data.startswith(b"GIF8"):
            return "image/gif"
        elif data.startswith(b"\x00\x00\x00\x00ftyp"):
            return "image/heic"
        else:
            return "image/jpeg"  # Default fallback

    def _build_system_prompt(self) -> str:
        """Construct the system prompt for the OpenAI Vision API call."""
        return """
        You are a product identifier analyzing receipt/product images. Your job is to extract FOOD ITEMS and their packaging information, NOT prices.

        CRITICAL: IGNORE ALL PRICE INFORMATION
        - Prices appear as: "$3.99", "2.49 B", "1.29", etc.
        - NEVER use price numbers as quantities
        - NEVER use "B" or currency symbols as units
        - Look ONLY at product packaging for actual quantities

        Extract these fields for each FOOD ITEM:
        - name: Product name from packaging (e.g., "Organic Spinach", "Whole Milk")
        - brand: Brand name if visible (null if not visible)
        - quantity: ONLY from product label (e.g., "16 oz", "1 gallon", "5 lb bag")
          * If no quantity visible on packaging, use 1
          * IGNORE price numbers like 3.99, 2.49, etc.
        - unit: Appropriate unit from packaging:
          * PRODUCE: 'each', 'lb', 'oz', 'bunch', 'bag'
          * DAIRY: 'gallon', 'quart', 'pint', 'oz', 'dozen' (for eggs)
          * MEAT/SEAFOOD: 'lb', 'oz', 'piece'
          * BEVERAGES: 'bottle', 'can', 'fl oz', 'liter'
          * CANNED GOODS: 'can', 'oz', 'jar'
          * PANTRY: 'lb', 'oz', 'bag', 'box'
          * SNACKS: 'bag', 'oz', 'each'
        - category: One of: 'Produce', 'Dairy', 'Meat', 'Seafood', 'Beverages', 'Bakery', 'Frozen', 'Canned Goods', 'Pantry', 'Snacks', 'Other'

        EXAMPLES OF WHAT TO IGNORE:
        - "BANANAS    $2.99 B" → Extract: name="Bananas", quantity=1, unit="each" (IGNORE the $2.99 B)
        - "MILK 1GAL   $3.49" → Extract: name="Milk", quantity=1, unit="gallon" (IGNORE the $3.49)
        - "CHIPS      $1.29 B" → Extract: name="Chips", quantity=1, unit="bag" (IGNORE the $1.29 B)

        EXAMPLES OF WHAT TO EXTRACT:
        - "Organic Spinach 5 oz" → name="Organic Spinach", quantity=5, unit="oz"
        - "Whole Milk 1 Gallon" → name="Whole Milk", quantity=1, unit="gallon"
        - "Ground Beef 1 lb" → name="Ground Beef", quantity=1, unit="lb"

        Return JSON format:
        {
            "items": [
                {
                    "name": "Product Name",
                    "brand": "Brand Name or null",
                    "quantity": 1,
                    "unit": "appropriate_unit",
                    "category": "Category"
                }
            ]
        }
        """

    async def _call_openai_api(self, image_data: bytes) -> str:
        """
        Invoke the OpenAI Vision API to analyze the image and extract structured data.
        Returns the raw JSON string from the model's response.
        """
        client = get_openai_client()
        if not client:
            raise RuntimeError("OpenAI client not configured")

        # Encode image as base64 for inline data URL
        mime_type = self._get_mime_type(image_data)
        processed_image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Prepare chat messages for vision input
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{processed_image_base64}",
                            "detail": "high",
                        },
                    }
                ],
            },
        ]

        logger.info("Calling OpenAI API for item scan with model: gpt-4o")

        # Call the chat completion endpoint
        response = client.chat.completions.create(
            model="gpt-5-nano-2025-08-07", messages=messages, max_completion_tokens=1500
        )

        logger.info(
            f"OpenAI API response received - Model: {response.model}, Usage: {response.usage}"
        )
        return response.choices[0].message.content

    def _parse_openai_response(self, content: str) -> list[dict[str, Any]]:
        """
        Parse the JSON content from the OpenAI response.
        Handles both raw JSON and JSON wrapped in markdown code blocks.
        """
        try:
            # Try to extract JSON from markdown code blocks first
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            json_str = json_match.group(1) if json_match else content

            parsed_json = json.loads(json_str)
            items = parsed_json.get("items", [])
            logger.info(f"Parsed JSON successfully. Found {len(items)} items")
            return items

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.debug(f"Raw response content: {content[:500]}...")
            raise

    async def _post_process_item(self, raw_item: dict[str, Any]) -> Optional[ParsedItem]:
        """
        Post-process a single raw item from OpenAI response:
        - Validate and fix quantity/unit pairs
        - Determine category using fallback logic
        - Calculate expiration date
        """
        try:
            display_name = raw_item.get("name", "Unknown Item")
            brand = raw_item.get("brand")
            product_name = f"{brand} {display_name}" if brand else display_name

            # Extract raw quantity and unit from OpenAI response
            raw_quantity = raw_item.get("quantity", 1)
            raw_unit = raw_item.get("unit", "each")

            # Validate and fix quantity/unit using fallback service
            quantity, unit = fallback_unit_service.validate_and_fix_quantity_unit(
                item_name=display_name,
                quantity=float(raw_quantity) if raw_quantity else 1.0,
                unit=raw_unit or "each",
                category=raw_item.get("category"),
            )

            logger.info(
                f"Quantity/unit validation for '{display_name}': {raw_quantity} {raw_unit} -> {quantity} {unit}"
            )

            # Determine category using OpenAI result or fallback to categorization service
            openai_category = raw_item.get("category")
            if openai_category and openai_category != "Other":
                category = openai_category
                logger.info(f"Using OpenAI category for {product_name}: {category}")
            else:
                # Use categorization service as fallback
                try:
                    categorization_result = await self.categorizer.categorize_food_item(
                        display_name
                    )
                    # Map internal categories to display categories
                    category_mapping = {
                        "produce_countable": "Produce",
                        "produce_measurable": "Produce",
                        "liquids": "Beverages",
                        "dry_goods": "Pantry",
                        "meat_seafood": "Meat",
                        "dairy": "Dairy",
                        "snacks_bars": "Snacks",
                        "packaged_snacks": "Snacks",
                        "frozen_foods": "Frozen",
                    }
                    category = category_mapping.get(categorization_result.category, "Other")
                    logger.info(
                        f"Categorized {product_name} as: {category} (from {categorization_result.category})"
                    )
                except Exception as cat_error:
                    logger.error(f"Error categorizing {product_name}: {str(cat_error)}")
                    category = self._determine_fallback_category(display_name)
                    logger.info(f"Using fallback category for {product_name}: {category}")

            # Calculate expiration date based on category
            expiration_date = None
            if category:
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
                    "Other": 30,
                }.get(category, 30)
                exp_date = datetime.now().date() + timedelta(days=expiration_days)
                expiration_date = exp_date.isoformat()

            return ParsedItem(
                name=display_name,
                quantity=quantity,
                unit=unit,
                category=category,
                barcode=raw_item.get("barcode"),
                brand=brand,
                product_name=product_name,
                nutrition_info=raw_item.get("nutrition_info"),
                expiration_date=expiration_date,
            )

        except Exception as item_error:
            logger.error(f"Error processing item {raw_item}: {str(item_error)}")
            return None

    def _determine_fallback_category(self, item_name: str) -> str:
        """
        Intelligent fallback category determination based on item name patterns.
        """
        item_lower = item_name.lower()

        # Check specific patterns (most specific to least specific)
        if any(
            word in item_lower
            for word in ["juice", "soda", "water", "coffee", "tea", "beer", "wine", "drink"]
        ):
            return "Beverages"

        if any(word in item_lower for word in ["canned", "can", "jar", "sauce", "soup"]):
            return "Canned Goods"

        if any(word in item_lower for word in ["frozen", "ice cream"]):
            return "Frozen"

        if any(
            word in item_lower
            for word in [
                "apple",
                "banana",
                "orange",
                "tomato",
                "potato",
                "onion",
                "carrot",
                "lettuce",
                "spinach",
                "broccoli",
                "fruit",
                "vegetable",
            ]
        ):
            return "Produce"

        if any(
            word in item_lower for word in ["milk", "cheese", "yogurt", "butter", "cream", "egg"]
        ):
            return "Dairy"

        if any(
            word in item_lower
            for word in ["chicken", "beef", "pork", "fish", "salmon", "turkey", "ham", "bacon"]
        ):
            return "Meat"

        if any(
            word in item_lower
            for word in ["bread", "roll", "bagel", "muffin", "cake", "cookie", "pastry"]
        ):
            return "Bakery"

        if any(
            word in item_lower for word in ["chips", "crackers", "bar", "nuts", "popcorn", "candy"]
        ):
            return "Snacks"

        # Default to Pantry for dry goods and unknown items
        return "Pantry"

    async def process_image(
        self, image_data: bytes, source_info: Optional[dict[str, Any]] = None
    ) -> OCRResponse:
        """
        Main entrypoint for OCR scanning flow:
        1. Validate size
        2. Determine mock vs cache vs API path
        3. Post-process items (quantity/unit, category, expiration)
        4. Cache and return structured OCRResponse
        """
        # Reject oversized payloads
        if len(image_data) > MAX_IMAGE_SIZE:
            raise ValueError(f"Image exceeds maximum size of {MAX_IMAGE_SIZE // (1024*1024)}MB")

        # Generate image hash for caching
        image_hash = self._generate_image_hash(image_data)
        cache_key = f"ocr_scan_{image_hash}"

        # Collect debug details
        debug_info: dict[str, Any] = {
            "image_hash": image_hash,
            "cache_key": cache_key,
            "mock_enabled": is_mock_enabled("ocr_scan"),
            "cache_hit": False,
            "openai_called": False,
        }

        if source_info:
            debug_info.update(source_info)

        # -- Mock mode shortcut --
        if is_mock_enabled("ocr_scan"):
            logger.info("🎭 Using mock data for item scan")
            debug_info["source"] = "mock"

            processed_items = []
            for item in MOCK_SCANNED_ITEMS:
                processed_items.append(
                    ParsedItem(
                        name=item["name"],
                        quantity=item["quantity"],
                        unit=item["unit"],
                        category=item["category"],
                        barcode=item.get("barcode"),
                        brand=item["brand"],
                        product_name=item["product_name"],
                        nutrition_info=item.get("nutrition_info"),
                        expiration_date=item["expiration_date"],
                    )
                )

            return OCRResponse(
                success=True,
                items=processed_items,
                message=f"Successfully identified {len(processed_items)} item(s) (mock data)",
                debug_info=debug_info,
            )

        # -- Cache lookup --
        cached_result = self.cache.get(cache_key, ttl=CACHE_TTL)
        if cached_result:
            logger.info(f"📋 Cache hit for image hash: {image_hash}")
            debug_info["cache_hit"] = True
            debug_info["source"] = "cache"

            # Return cached result with updated debug info
            if hasattr(cached_result, "debug_info"):
                return OCRResponse(
                    success=cached_result.success,
                    items=cached_result.items,
                    raw_text=cached_result.raw_text,
                    message=cached_result.message,
                    debug_info=debug_info,
                )

            return cached_result

        # -- Fresh API call --
        logger.info(f"🚀 Making fresh OpenAI detection call for image hash: {image_hash}")
        debug_info["openai_called"] = True
        debug_info["source"] = "openai_fresh"

        try:
            # Call OpenAI API
            raw_content = await self._call_openai_api(image_data)

            # Parse response
            try:
                raw_items = self._parse_openai_response(raw_content)
            except Exception as parse_error:
                logger.error(f"Failed to parse OpenAI response: {parse_error}")
                debug_info["parse_error"] = str(parse_error)
                debug_info["raw_response"] = (
                    raw_content[:500] + "..." if len(raw_content) > 500 else raw_content
                )

                return OCRResponse(
                    success=False,
                    items=[],
                    raw_text=raw_content,
                    message="Could not parse items from the image analysis.",
                    debug_info=debug_info,
                )

            # Post-process each item
            processed_items = []
            logger.info(f"Processing {len(raw_items)} items from OpenAI response")

            for raw_item in raw_items:
                processed_item = await self._post_process_item(raw_item)
                if processed_item:
                    processed_items.append(processed_item)
                    logger.info(
                        f"Successfully processed item: {processed_item.name} with category: {processed_item.category}"
                    )

            debug_info["processed_items_count"] = len(processed_items)

            # Build response
            response = OCRResponse(
                success=bool(processed_items),
                items=processed_items,
                raw_text=raw_content if not processed_items else None,
                message=(
                    f"Successfully identified {len(processed_items)} item(s)"
                    if processed_items
                    else "No items could be identified in the image"
                ),
                debug_info=debug_info,
            )

            # Cache successful results
            if processed_items:
                self.cache.set(cache_key, response, ttl=CACHE_TTL)
                logger.info(f"💾 Cached result for image hash: {image_hash}")

            # Track detection for debugging
            self._track_detection(image_hash, response, source_info)

            if processed_items:
                logger.info(
                    f"✅ FINAL RESULT: Returning {len(processed_items)} processed items to client"
                )
                for _i, item in enumerate(processed_items[:3]):  # Log first 3 items
                    logger.info(
                        f"  ➤ {item.name}: {item.quantity} {item.unit} (Category: {item.category})"
                    )
                if len(processed_items) > 3:
                    logger.info(f"  ➤ ... and {len(processed_items) - 3} more items")
            else:
                logger.warning("⚠️  No items identified in the image")

            return response

        except AuthenticationError:
            logger.error("OpenAI authentication failed")
            raise
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            raise

    def _track_detection(
        self, image_hash: str, response: OCRResponse, source_info: Optional[dict[str, Any]] = None
    ):
        """Track detection results for debugging purposes."""
        detection_record = {
            "timestamp": datetime.now().isoformat(),
            "image_hash": image_hash,
            "success": response.success,
            "items_count": len(response.items),
            "mock_used": is_mock_enabled("ocr_scan"),
        }

        if source_info:
            detection_record.update(source_info)

        self.recent_detections.append(detection_record)

        # Keep only last 10 detections
        if len(self.recent_detections) > 10:
            self.recent_detections.pop(0)

    def get_recent_detections(self) -> list[dict[str, Any]]:
        """Get recent detection results for debugging."""
        return self.recent_detections.copy()

    def clear_cache(self) -> dict[str, Any]:
        """Clear OCR-related cache entries."""
        try:
            # Find and clear OCR-related cache entries
            ocr_keys = [key for key in self.cache.cache if "ocr_scan_" in key]

            for key in ocr_keys:
                self.cache.delete(key)

            # Also use the pattern invalidation function
            invalidate_pattern_cache("ocr_scan_")

            logger.info(f"🧹 Cleared {len(ocr_keys)} OCR cache entries")

            return {
                "success": True,
                "cleared_entries": len(ocr_keys),
                "message": f"Cleared {len(ocr_keys)} OCR cache entries",
            }

        except Exception as e:
            logger.error(f"Error clearing OCR cache: {e}")
            raise RuntimeError(f"Error clearing cache: {str(e)}") from e


# Global service instance
ocr_service = OcrService()
