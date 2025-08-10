"""
Barcode lookup router using USDA database.
Provides instant product information from barcode scans.
"""

import logging
from typing import Any, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend_gateway.core.database import get_db_pool
from backend_gateway.services.usda_food_service import USDAFoodService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/barcode", tags=["Barcode"])


class BarcodeProduct(BaseModel):
    """Product information from barcode lookup."""

    barcode: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[float] = None
    serving_size_unit: Optional[str] = None
    fdc_id: int
    ingredients: Optional[str] = None
    nutritional_available: bool = True


class BarcodeLookupResponse(BaseModel):
    """Response for barcode lookup."""

    found: bool
    product: Optional[BarcodeProduct] = None
    message: Optional[str] = None


class NutritionalInfo(BaseModel):
    """Nutritional information per serving."""

    calories: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None


@router.get("/lookup/{barcode}", response_model=BarcodeLookupResponse)
async def lookup_barcode(barcode: str, db_pool: asyncpg.Pool = Depends(get_db_pool)):
    """
    Look up product information by barcode.

    Args:
        barcode: UPC/EAN barcode (will be cleaned automatically)

    Returns:
        Product information if found
    """
    # Clean barcode - remove spaces and leading zeros
    clean_barcode = barcode.strip().lstrip("0")

    if not clean_barcode or not clean_barcode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid barcode format. Must be numeric.")

    usda_service = USDAFoodService(db_pool)

    # Search by barcode
    results = await usda_service.search_foods(barcode=clean_barcode, limit=1)

    if not results:
        return BarcodeLookupResponse(
            found=False, message=f"No product found for barcode: {barcode}"
        )

    # Get detailed information
    product_data = results[0]
    details = await usda_service.get_food_details(product_data["fdc_id"])

    if details:
        product = BarcodeProduct(
            barcode=clean_barcode,
            name=details["description"],
            brand=details.get("brand_owner") or details.get("brand_name"),
            category=details.get("category_name"),
            serving_size=details.get("serving_size"),
            serving_size_unit=details.get("serving_size_unit"),
            fdc_id=details["fdc_id"],
            ingredients=details.get("ingredients"),
        )
    else:
        # Fallback to basic info
        product = BarcodeProduct(
            barcode=clean_barcode,
            name=product_data["description"],
            brand=product_data.get("brand_info"),
            category=product_data.get("category"),
            fdc_id=product_data["fdc_id"],
        )

    return BarcodeLookupResponse(found=True, product=product, message="Product found successfully")


@router.get("/nutrition/{barcode}")
async def get_barcode_nutrition(
    barcode: str, db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> dict[str, Any]:
    """
    Get nutritional information for a product by barcode.

    Returns detailed nutritional facts per serving.
    """
    # Clean barcode
    clean_barcode = barcode.strip().lstrip("0")

    usda_service = USDAFoodService(db_pool)

    # Find product
    results = await usda_service.search_foods(barcode=clean_barcode, limit=1)

    if not results:
        raise HTTPException(status_code=404, detail=f"No product found for barcode: {barcode}")

    # Get nutritional details
    fdc_id = results[0]["fdc_id"]
    details = await usda_service.get_food_details(fdc_id)

    if not details or not details.get("nutrients"):
        raise HTTPException(
            status_code=404, detail="Nutritional information not available for this product"
        )

    # Extract key nutrients
    nutrients_map = {
        "Energy": "calories",
        "Protein": "protein_g",
        "Total lipid (fat)": "fat_g",
        "Carbohydrate, by difference": "carbs_g",
        "Fiber, total dietary": "fiber_g",
        "Sugars, total including NLEA": "sugar_g",
        "Sodium, Na": "sodium_mg",
    }

    nutrition = {}
    for nutrient in details["nutrients"]:
        nutrient_name = nutrient["name"]
        if nutrient_name in nutrients_map:
            nutrition[nutrients_map[nutrient_name]] = nutrient["amount"]

    return {
        "product_name": details["description"],
        "brand": details.get("brand_owner"),
        "serving_size": details.get("serving_size"),
        "serving_size_unit": details.get("serving_size_unit"),
        "nutrition_per_serving": nutrition,
        "all_nutrients": [
            {"name": n["name"], "amount": n["amount"], "unit": n["unit_name"]}
            for n in details["nutrients"]
        ],
    }


@router.get("/search")
async def search_by_barcode_pattern(
    pattern: str = Query(..., description="Partial barcode or pattern"),
    limit: int = Query(10, ge=1, le=50),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
):
    """
    Search for products by partial barcode.

    Useful for damaged barcodes or pattern matching.
    """
    if len(pattern) < 3:
        raise HTTPException(status_code=400, detail="Pattern must be at least 3 characters")

    async with db_pool.acquire() as conn:
        # Search for barcodes containing the pattern
        results = await conn.fetch(
            """
            SELECT
                fdc_id,
                description,
                brand_owner,
                brand_name,
                gtin_upc as barcode,
                food_category_id
            FROM usda_foods
            WHERE gtin_upc LIKE $1
            AND gtin_upc IS NOT NULL
            ORDER BY description
            LIMIT $2
        """,
            f"%{pattern}%",
            limit,
        )

        products = []
        for row in results:
            products.append(
                {
                    "barcode": row["barcode"],
                    "name": row["description"],
                    "brand": row["brand_owner"] or row["brand_name"],
                    "fdc_id": row["fdc_id"],
                }
            )

        return {"found": len(products), "products": products}
