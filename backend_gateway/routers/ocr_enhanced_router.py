"""
Enhanced OCR Router with USDA Integration
Improves OCR accuracy by matching extracted items with USDA food database.
"""

import logging
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from backend_gateway.core.database import get_db_pool
from backend_gateway.core.openai_client import get_openai_client
from backend_gateway.routers.ocr_router import ParsedItem, ScanRequest
from backend_gateway.routers.ocr_router import scan_items as original_scan_items
from backend_gateway.routers.ocr_router import scan_receipt as original_scan_receipt
from backend_gateway.services.ocr_usda_enhancer import OCRUSDAEnhancer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr-enhanced", tags=["OCR Enhanced"])


class EnhancedParsedItem(ParsedItem):
    """Extended parsed item with USDA data."""

    matched_name: Optional[str] = None
    brand: Optional[str] = None
    fdc_id: Optional[int] = None
    confidence: Optional[float] = None
    nutritional_available: Optional[bool] = False
    enhanced: bool = False


class EnhancedOCRResponse(BaseModel):
    """Enhanced OCR response with USDA matches."""

    success: bool
    items: list[EnhancedParsedItem]
    enhanced_count: int
    message: Optional[str] = None
    processing_time: Optional[float] = None


@router.post("/scan-receipt", response_model=EnhancedOCRResponse)
async def scan_receipt_enhanced(
    request: ScanRequest,
    client: OpenAI = Depends(get_openai_client),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Enhanced receipt scanning with USDA food matching.

    This endpoint:
    1. Performs standard OCR on the receipt
    2. Matches extracted items with USDA database
    3. Returns enhanced results with standardized names and categories
    """
    import time

    start_time = time.time()

    # First, get standard OCR results
    ocr_response = await original_scan_receipt(request, client)

    if not ocr_response.success:
        return EnhancedOCRResponse(
            success=False, items=[], enhanced_count=0, message=ocr_response.message
        )

    # Convert to format for enhancement
    ocr_items = [
        {
            "item_name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "barcode": item.barcode,
        }
        for item in ocr_response.items
    ]

    # Enhance with USDA data
    enhancer = OCRUSDAEnhancer(db_pool)
    enhanced_results = await enhancer.enhance_ocr_results(ocr_items)

    # Convert to response format
    enhanced_items = []
    enhanced_count = 0

    for idx, enhanced in enumerate(enhanced_results):
        original_item = ocr_response.items[idx]

        if enhanced.get("enhanced", False):
            enhanced_count += 1
            enhanced_item = EnhancedParsedItem(
                name=original_item.name,
                quantity=original_item.quantity,
                unit=original_item.unit,
                category=enhanced.get("category", original_item.category),
                barcode=enhanced.get("barcode", original_item.barcode),
                brand=enhanced.get("brand"),
                product_name=enhanced.get("matched_name", original_item.product_name),
                matched_name=enhanced.get("matched_name"),
                fdc_id=enhanced.get("fdc_id"),
                confidence=enhanced.get("confidence"),
                nutritional_available=enhanced.get("nutritional_available", False),
                enhanced=True,
                expiration_date=original_item.expiration_date,
            )
        else:
            # Include cleaned name even if no match
            enhanced_item = EnhancedParsedItem(
                **original_item.dict(), matched_name=enhanced.get("cleaned_name"), enhanced=False
            )

        enhanced_items.append(enhanced_item)

    processing_time = time.time() - start_time

    return EnhancedOCRResponse(
        success=True,
        items=enhanced_items,
        enhanced_count=enhanced_count,
        message=f"Extracted {len(enhanced_items)} items, enhanced {enhanced_count} with USDA data",
        processing_time=round(processing_time, 2),
    )


@router.post("/scan-items", response_model=EnhancedOCRResponse)
async def scan_items_enhanced(
    request: ScanRequest,
    client: OpenAI = Depends(get_openai_client),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Enhanced item scanning with USDA food matching.

    Similar to receipt scanning but optimized for pantry/fridge photos.
    """
    import time

    start_time = time.time()

    # Get standard OCR results
    ocr_response = await original_scan_items(request, client)

    if not ocr_response.success:
        return EnhancedOCRResponse(
            success=False, items=[], enhanced_count=0, message=ocr_response.message
        )

    # Convert and enhance
    ocr_items = [
        {
            "item_name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "barcode": item.barcode,
        }
        for item in ocr_response.items
    ]

    enhancer = OCRUSDAEnhancer(db_pool)
    enhanced_results = await enhancer.enhance_ocr_results(ocr_items)

    # Build response
    enhanced_items = []
    enhanced_count = 0

    for idx, enhanced in enumerate(enhanced_results):
        original_item = ocr_response.items[idx]

        if enhanced.get("enhanced", False):
            enhanced_count += 1

        enhanced_item = EnhancedParsedItem(
            name=original_item.name,
            quantity=original_item.quantity,
            unit=original_item.unit,
            category=enhanced.get("category", original_item.category),
            barcode=enhanced.get("barcode", original_item.barcode),
            brand=enhanced.get("brand", original_item.brand),
            product_name=enhanced.get("matched_name", original_item.product_name),
            matched_name=enhanced.get("matched_name"),
            fdc_id=enhanced.get("fdc_id"),
            confidence=enhanced.get("confidence"),
            nutritional_available=enhanced.get("nutritional_available", False),
            enhanced=enhanced.get("enhanced", False),
            expiration_date=original_item.expiration_date,
        )

        enhanced_items.append(enhanced_item)

    processing_time = time.time() - start_time

    return EnhancedOCRResponse(
        success=True,
        items=enhanced_items,
        enhanced_count=enhanced_count,
        message=f"Identified {len(enhanced_items)} items, enhanced {enhanced_count} with USDA data",
        processing_time=round(processing_time, 2),
    )


@router.get("/nutrition/{fdc_id}")
async def get_item_nutrition(fdc_id: int, db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """
    Get nutritional information for an item by its USDA FDC ID.
    """
    enhancer = OCRUSDAEnhancer(db_pool)
    nutrition = await enhancer.get_nutrition_for_item(fdc_id)

    if not nutrition:
        raise HTTPException(status_code=404, detail="Nutritional information not found")

    return nutrition
