import logging
import re
from decimal import Decimal

from src.tools.unit_convert import to_canonical

logger = logging.getLogger(__name__)


class UnitCanon:
    """UnitCanon agent for standardizing units and quantities"""

    def __init__(self):
        self.name = "unit_canon"

    async def run(self, categorized_items: list[dict]):
        """
        Input: [{'canonical_name': 'chicken breast', 'category': 'Poultry', 'fdc_id': 123, 'raw_line': '2 lb chicken breast'}...]
        Output: [{'canonical_name': 'chicken breast', 'category': 'Poultry', 'fdc_id': 123, 'raw_line': '2 lb chicken breast',
                 'qty_canon': Decimal('0.907'), 'canon_unit': 'kilogram'}...]
        """
        if not categorized_items:
            return []

        out = []
        for item in categorized_items:
            try:
                # Extract quantity and unit from raw_line
                raw_line = item.get("raw_line", "").strip()
                if not raw_line:
                    logger.warning(f"Empty raw_line for item: {item}")
                    continue

                qty, unit = self._extract_quantity_unit(raw_line)
                if qty is None or unit is None:
                    logger.debug(f"Could not parse quantity/unit from: {raw_line}")
                    # Default to 1 count if no quantity/unit found
                    qty, unit = 1.0, "each"

                # Get density for volume/mass conversion if needed
                density = self._get_density(item.get("category", ""))

                # Convert to canonical units
                try:
                    qty_canon, canon_unit = to_canonical(qty, unit, density)

                    out.append(
                        {
                            **item,
                            "qty_original": qty,
                            "unit_original": unit,
                            "qty_canon": qty_canon,
                            "canon_unit": canon_unit,
                            "density_used": density,
                        }
                    )
                except Exception as e:
                    logger.error(f"Unit conversion failed for {qty} {unit}: {e}")
                    # Fall back to original values
                    out.append(
                        {
                            **item,
                            "qty_original": qty,
                            "unit_original": unit,
                            "qty_canon": Decimal(str(qty)),
                            "canon_unit": unit,
                            "conversion_error": str(e),
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing item {item}: {e}")
                continue

        logger.info(f"Canonicalized units for {len(out)} out of {len(categorized_items)} items")
        return out

    def _extract_quantity_unit(self, raw_line: str) -> tuple[float | None, str | None]:
        """Extract quantity and unit from raw text like '2 lb chicken breast'"""
        # Common patterns for quantity and unit extraction
        patterns = [
            r"(\d+\.?\d*)\s*(lb|lbs|pound|pounds)",
            r"(\d+\.?\d*)\s*(oz|ounce|ounces)",
            r"(\d+\.?\d*)\s*(kg|kilogram|kilograms)",
            r"(\d+\.?\d*)\s*(g|gram|grams)",
            r"(\d+\.?\d*)\s*(cup|cups)",
            r"(\d+\.?\d*)\s*(tbsp|tablespoon|tablespoons)",
            r"(\d+\.?\d*)\s*(tsp|teaspoon|teaspoons)",
            r"(\d+\.?\d*)\s*(ml|milliliter|milliliters)",
            r"(\d+\.?\d*)\s*(l|liter|liters)",
            r"(\d+\.?\d*)\s*(gallon|gallons)",
            r"(\d+\.?\d*)\s*(quart|quarts)",
            r"(\d+\.?\d*)\s*(pint|pints)",
            r"(\d+\.?\d*)\s*(fl\s*oz|fluid\s*ounce|fluid\s*ounces)",
            r"(\d+\.?\d*)\s*(dozen)",
            r"(\d+\.?\d*)\s*(each|count|item|items)",
            # Fallback: just number at start
            r"^(\d+\.?\d*)\s*(\w+)?",
        ]

        raw_lower = raw_line.lower().strip()

        for pattern in patterns:
            match = re.search(pattern, raw_lower)
            if match:
                qty_str = match.group(1)
                unit_str = match.group(2) if len(match.groups()) > 1 and match.group(2) else "each"

                try:
                    qty = float(qty_str)
                    # Normalize unit names
                    unit = self._normalize_unit_name(unit_str)
                    return qty, unit
                except ValueError:
                    continue

        return None, None

    def _normalize_unit_name(self, unit: str) -> str:
        """Normalize unit names to standard forms"""
        unit = unit.lower().strip()

        # Mapping of common variations to standard forms
        unit_mapping = {
            "lb": "pound",
            "lbs": "pound",
            "pounds": "pound",
            "oz": "ounce",
            "ounces": "ounce",
            "kg": "kilogram",
            "kilograms": "kilogram",
            "g": "gram",
            "grams": "gram",
            "cups": "cup",
            "tbsp": "tablespoon",
            "tablespoons": "tablespoon",
            "tsp": "teaspoon",
            "teaspoons": "teaspoon",
            "ml": "milliliter",
            "milliliters": "milliliter",
            "l": "liter",
            "liters": "liter",
            "gallons": "gallon",
            "quarts": "quart",
            "pints": "pint",
            "fl oz": "fluid_ounce",
            "fluid ounce": "fluid_ounce",
            "fluid ounces": "fluid_ounce",
            "count": "each",
            "item": "each",
            "items": "each",
        }

        return unit_mapping.get(unit, unit)

    def _get_density(self, category: str) -> float | None:
        """Get estimated density for category to enable volume/mass conversion"""
        # Rough density estimates (g/mL) for common food categories
        density_map = {
            "dairy and egg products": 1.03,
            "fats and oils": 0.92,
            "poultry products": 1.05,
            "beef products": 1.05,
            "pork products": 1.05,
            "lamb, veal, and game products": 1.05,
            "finfish and shellfish products": 1.05,
            "vegetables and vegetable products": 1.00,
            "fruits and fruit juices": 1.00,
            "nut and seed products": 0.60,
            "legumes and legume products": 1.20,
            "grains and cereals": 0.75,
            "beverages": 1.00,
            "soups, sauces, and gravies": 1.00,
        }

        category_lower = category.lower() if category else ""
        return density_map.get(category_lower, None)
