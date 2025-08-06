"""
Receipt Scanner Service using Agentic AI
Uses OpenAI Vision API to intelligently extract and parse receipt data
"""

import base64
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GroceryItem(BaseModel):
    """Structured grocery item from receipt"""

    name: str = Field(description="Clean product name (e.g., 'Oreo Cookies' not 'OREO COOKIE FC')")
    quantity: Optional[float] = Field(default=1, description="Quantity purchased")
    unit: Optional[str] = Field(default=None, description="Unit of measurement if applicable")
    price: Optional[float] = Field(default=None, description="Price of the item")
    category: Optional[str] = Field(
        default=None, description="Category (produce, dairy, meat, etc.)"
    )


class ReceiptData(BaseModel):
    """Structured receipt data"""

    store_name: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    items: List[GroceryItem] = Field(default_factory=list)
    total: Optional[float] = Field(default=None)


class ReceiptScannerService:
    def __init__(self):
        """Initialize the receipt scanner service."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        self.client = openai.OpenAI()

    async def scan_receipt(self, image_data: str) -> Dict[str, Any]:
        """
        Scan a receipt image and extract structured data using AI agent.

        Args:
            image_data: Base64 encoded image data

        Returns:
            Dict containing extracted receipt data
        """
        try:
            # Prepare the vision API request
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert receipt scanner AI. Extract grocery items from receipts and:
1. Clean up product names (e.g., "OREO COOKIE FC" → "Oreo Cookies")
2. Identify quantities if shown (e.g., "2 @ $2.99 ea" means quantity=2)
3. Categorize items and use appropriate units:
   - PRODUCE: Use 'lb', 'oz', 'each', 'bunch', 'bag' (NOT ml, L)
   - DAIRY: Liquid='gallon', 'quart', 'pint'; Solid='oz', 'lb'; Eggs='dozen'
   - MEAT/SEAFOOD: Use 'lb', 'oz', 'piece' (NOT ml, each)
   - BEVERAGES: Use 'bottle', 'can', 'liter', 'fl oz' (NOT lb)
   - BAKERY: Use 'loaf', 'each', 'package'
   - CANNED GOODS: Use 'can', 'oz', 'jar'
   - PANTRY/SPICES: Use 'oz', 'container', 'jar' for spices; 'lb', 'bag' for staples
4. Extract store name, date, and total
5. Ignore non-food items like cleaning supplies, cosmetics
6. Format all data as clean, user-friendly text

Return data in the exact JSON format specified.""",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all grocery items from this receipt. Clean up the names and categorize them.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                        },
                    ],
                },
            ]

            # Call OpenAI Vision API with structured output
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=messages,
                response_format=ReceiptData,
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent parsing
            )

            # Extract the parsed data
            receipt_data = response.choices[0].message.parsed

            # Convert to dict for API response
            result = {
                "success": True,
                "data": {
                    "store_name": receipt_data.store_name,
                    "date": receipt_data.date,
                    "total": receipt_data.total,
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit": item.unit,
                            "price": item.price,
                            "category": item.category,
                        }
                        for item in receipt_data.items
                    ],
                },
                "items_count": len(receipt_data.items),
            }

            logger.info(f"Successfully extracted {len(receipt_data.items)} items from receipt")
            return result

        except Exception as e:
            logger.error(f"Error scanning receipt: {str(e)}")
            return {"success": False, "error": str(e), "data": None}

    async def add_items_to_pantry(
        self, user_id: int, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add extracted items to user's pantry.

        Args:
            user_id: User ID
            items: List of items to add

        Returns:
            Result of the operation
        """
        try:
            added_items = []
            skipped_items = []

            # Import here to avoid circular imports
            from backend_gateway.services.pantry_service import PantryService

            pantry_service = PantryService()

            for item in items:
                try:
                    # Prepare item data for pantry
                    pantry_item = {
                        "product_name": item["name"],
                        "quantity": item.get("quantity", 1),
                        "unit": item.get("unit", "piece"),
                        "category": item.get("category", "other"),
                        "purchase_date": datetime.now().isoformat(),
                        "source": "receipt_scan",
                    }

                    # Add to pantry
                    result = await pantry_service.add_item(user_id, pantry_item)
                    added_items.append(item["name"])

                except Exception as e:
                    logger.warning(f"Failed to add item {item['name']}: {str(e)}")
                    skipped_items.append(item["name"])

            return {
                "success": True,
                "added": added_items,
                "skipped": skipped_items,
                "total_added": len(added_items),
                "total_skipped": len(skipped_items),
            }

        except Exception as e:
            logger.error(f"Error adding items to pantry: {str(e)}")
            return {"success": False, "error": str(e)}
