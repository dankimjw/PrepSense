"""Unit Converter Tool for CrewAI

Wraps the existing UnitConversionService to convert between different measurement units.
"""

from crewai.tools import BaseTool
from backend_gateway.services.unit_conversion_service import UnitConversionService
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UnitConverterTool(BaseTool):
    name: str = "unit_converter"
    description: str = "Convert units using existing unit conversion service"
    
    def _run(self, quantity: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Use existing unit conversion service"""
        try:
            converter = UnitConversionService()
            result = converter.convert_unit(quantity, from_unit, to_unit)
            return {
                "status": "success",
                "original": {
                    "quantity": quantity,
                    "unit": from_unit
                },
                "converted": {
                    "quantity": result["converted_quantity"] if isinstance(result, dict) else result,
                    "unit": to_unit
                },
                "conversion_factor": result.get("conversion_factor") if isinstance(result, dict) else None
            }
        except Exception as e:
            logger.error(f"Unit conversion failed for {quantity} {from_unit} to {to_unit}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "original": {
                    "quantity": quantity,
                    "unit": from_unit
                },
                "converted": None
            }