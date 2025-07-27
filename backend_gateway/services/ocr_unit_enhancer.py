"""
OCR Unit Enhancement Service
Fixes unit issues in OCR-extracted items before adding to pantry.
"""

import logging
from typing import List, Dict, Any
import asyncpg

from backend_gateway.services.smart_unit_validator import SmartUnitValidator

logger = logging.getLogger(__name__)


class OCRUnitEnhancer:
    """Enhances OCR results by fixing inappropriate units."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.validator = SmartUnitValidator(db_pool)
    
    async def enhance_ocr_units(
        self, 
        ocr_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fix unit issues in OCR-extracted items.
        
        Args:
            ocr_items: List of items from OCR with fields:
                - name: Item name
                - quantity: Quantity amount
                - unit: Current unit (possibly wrong)
                
        Returns:
            Enhanced items with corrected units
        """
        enhanced_items = []
        
        for item in ocr_items:
            try:
                enhanced_item = await self._enhance_single_item(item)
                enhanced_items.append(enhanced_item)
            except Exception as e:
                logger.error(f"Failed to enhance unit for {item.get('name')}: {e}")
                # Return original item with error flag
                enhanced_items.append({
                    **item,
                    'unit_enhancement_error': str(e),
                    'unit_enhanced': False
                })
        
        return enhanced_items
    
    async def _enhance_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single OCR item's unit."""
        
        name = item.get('name', '')
        current_unit = item.get('unit', 'each')
        quantity = item.get('quantity', 1.0)
        
        # Validate current unit
        validation = await self.validator.validate_and_suggest_unit(
            name, 
            current_unit, 
            quantity
        )
        
        # Build enhanced item
        enhanced = {
            **item,
            'unit_enhanced': True,
            'original_unit': current_unit,
            'unit_validation': validation
        }
        
        # Update unit if needed
        if not validation['is_valid'] and validation['suggested_unit']:
            enhanced['unit'] = validation['suggested_unit']
            enhanced['unit_changed'] = True
            enhanced['unit_change_reason'] = validation['reason']
        else:
            enhanced['unit'] = current_unit
            enhanced['unit_changed'] = False
        
        return enhanced
    
    async def get_unit_fix_summary(
        self, 
        ocr_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get summary of unit fixes that would be applied.
        
        Useful for showing user what changes before applying.
        """
        fixes = []
        error_count = 0
        warning_count = 0
        changed_count = 0
        
        for item in ocr_items:
            name = item.get('name', '')
            current_unit = item.get('unit', 'each')
            quantity = item.get('quantity', 1.0)
            
            try:
                validation = await self.validator.validate_and_suggest_unit(
                    name, current_unit, quantity
                )
                
                fix_info = {
                    'item_name': name,
                    'current_unit': current_unit,
                    'suggested_unit': validation['suggested_unit'],
                    'severity': validation['severity'],
                    'reason': validation['reason'],
                    'would_change': not validation['is_valid'] and validation['suggested_unit']
                }
                
                fixes.append(fix_info)
                
                if validation['severity'] == 'error':
                    error_count += 1
                elif validation['severity'] == 'warning':
                    warning_count += 1
                
                if fix_info['would_change']:
                    changed_count += 1
                    
            except Exception as e:
                error_count += 1
                fixes.append({
                    'item_name': name,
                    'current_unit': current_unit,
                    'error': str(e),
                    'would_change': False
                })
        
        return {
            'total_items': len(ocr_items),
            'units_to_fix': changed_count,
            'errors': error_count,
            'warnings': warning_count,
            'fixes': fixes
        }