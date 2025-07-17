"""
Smart Unit Conversion Service
Handles intelligent unit conversions using food-specific densities and rules
"""

import json
import os
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
import logging

from ..constants.food_category_unit_rules import UnitCategory

logger = logging.getLogger(__name__)

class SmartUnitConversionService:
    def __init__(self):
        # Load density data
        density_file = os.path.join(
            os.path.dirname(__file__), 
            '../constants/common_food_densities.json'
        )
        with open(density_file, 'r') as f:
            self.density_data = json.load(f)
        
        # Base unit conversions (everything converts to these)
        self.base_units = {
            UnitCategory.MASS: 'g',      # grams
            UnitCategory.VOLUME: 'ml',    # millilitres
            UnitCategory.COUNT: 'ea'      # each
        }
        
        # Standard conversions to base units
        self.to_base_conversions = {
            # Mass to grams
            'g': 1.0,
            'kg': 1000.0,
            'mg': 0.001,
            'oz': 28.3495,
            'lb': 453.592,
            
            # Volume to millilitres
            'ml': 1.0,
            'l': 1000.0,
            'tsp': 4.929,
            'tbsp': 14.787,
            'cup': 236.588,
            'floz': 29.574,
            'pt': 473.176,
            'qt': 946.353,
            'gal': 3785.41,
            
            # Count to each
            'ea': 1.0,
            'dozen': 12.0,
            'pair': 2.0,
            
            # Special units that need context
            'pinch': 0.3,      # ~0.3ml
            'dash': 0.6,       # ~0.6ml
            'drop': 0.05,      # ~0.05ml
            'handful': 60.0,   # ~1/4 cup = 60ml
        }
    
    def get_unit_category(self, unit: str) -> Optional[UnitCategory]:
        """Determine the category of a unit"""
        # Mass units
        if unit in ['g', 'kg', 'mg', 'oz', 'lb']:
            return UnitCategory.MASS
        
        # Volume units
        elif unit in ['ml', 'l', 'tsp', 'tbsp', 'cup', 'floz', 'pt', 'qt', 'gal', 
                      'pinch', 'dash', 'drop', 'handful']:
            return UnitCategory.VOLUME
        
        # Count units
        elif unit in ['ea', 'each', 'dozen', 'pair', 'head', 'bunch', 'loaf', 
                      'slice', 'can', 'bottle', 'box', 'bag', 'jar', 'stick', 
                      'clove', 'packet']:
            return UnitCategory.COUNT
        
        return None
    
    def can_convert(self, from_unit: str, to_unit: str, item_name: Optional[str] = None) -> bool:
        """Check if units can be converted"""
        from_category = self.get_unit_category(from_unit)
        to_category = self.get_unit_category(to_unit)
        
        if not from_category or not to_category:
            return False
        
        # Same category conversions are always possible
        if from_category == to_category:
            return True
        
        # Cross-category conversions need item-specific data
        if item_name and from_category != to_category:
            return self._has_density_data(item_name, from_category, to_category)
        
        return False
    
    def convert(
        self, 
        quantity: float, 
        from_unit: str, 
        to_unit: str, 
        item_name: Optional[str] = None
    ) -> Tuple[float, str, Optional[str]]:
        """
        Convert quantity from one unit to another
        Returns: (converted_quantity, status, message)
        Status can be: 'success', 'warning', 'error'
        """
        from_category = self.get_unit_category(from_unit)
        to_category = self.get_unit_category(to_unit)
        
        if not from_category or not to_category:
            return (0.0, 'error', f"Unknown unit: {from_unit} or {to_unit}")
        
        # Same category conversion
        if from_category == to_category:
            return self._convert_same_category(quantity, from_unit, to_unit)
        
        # Cross-category conversion (needs item info)
        if not item_name:
            return (0.0, 'error', f"Cannot convert {from_unit} to {to_unit} without knowing the item")
        
        return self._convert_cross_category(quantity, from_unit, to_unit, item_name)
    
    def _convert_same_category(
        self, 
        quantity: float, 
        from_unit: str, 
        to_unit: str
    ) -> Tuple[float, str, Optional[str]]:
        """Convert within the same category"""
        # Get conversion factors to base unit
        from_factor = self.to_base_conversions.get(from_unit, 1.0)
        to_factor = self.to_base_conversions.get(to_unit, 1.0)
        
        # Convert: from_unit -> base_unit -> to_unit
        base_quantity = quantity * from_factor
        result = base_quantity / to_factor
        
        # Round to reasonable precision
        result = float(Decimal(str(result)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return (result, 'success', None)
    
    def _convert_cross_category(
        self, 
        quantity: float, 
        from_unit: str, 
        to_unit: str, 
        item_name: str
    ) -> Tuple[float, str, Optional[str]]:
        """Convert between different categories using density data"""
        item_key = self._normalize_item_name(item_name)
        
        # Check density conversions
        if item_key in self.density_data['density_conversions']:
            item_data = self.density_data['density_conversions'][item_key]
            
            # Volume to Mass conversions
            if from_unit == 'cup' and to_unit in ['g', 'kg']:
                if 'cup_to_grams' in item_data:
                    grams = quantity * item_data['cup_to_grams']
                    if to_unit == 'kg':
                        result = grams / 1000
                    else:
                        result = grams
                    return (result, 'success', f"Using density for {item_data['name']}")
            
            elif from_unit == 'tbsp' and to_unit in ['g', 'kg']:
                if 'tablespoon_to_grams' in item_data:
                    grams = quantity * item_data['tablespoon_to_grams']
                    if to_unit == 'kg':
                        result = grams / 1000
                    else:
                        result = grams
                    return (result, 'success', f"Using density for {item_data['name']}")
            
            # Mass to Volume conversions (reverse)
            elif from_unit in ['g', 'kg'] and to_unit == 'cup':
                if 'cup_to_grams' in item_data:
                    grams = quantity if from_unit == 'g' else quantity * 1000
                    result = grams / item_data['cup_to_grams']
                    return (result, 'success', f"Using density for {item_data['name']}")
        
        # Check common conversions
        if item_key in self.density_data['common_conversions']:
            conversion_data = self.density_data['common_conversions'][item_key]
            
            # Handle specific conversions like loaf to slices
            if from_unit == 'loaf' and to_unit == 'slice':
                if 'loaf_to_slices' in conversion_data:
                    result = quantity * conversion_data['loaf_to_slices']
                    return (result, 'success', None)
            
            elif from_unit == 'slice' and to_unit == 'loaf':
                if 'loaf_to_slices' in conversion_data:
                    result = quantity / conversion_data['loaf_to_slices']
                    return (result, 'warning', "Partial loaves rounded")
        
        return (0.0, 'error', f"No conversion data for {item_name} from {from_unit} to {to_unit}")
    
    def _has_density_data(self, item_name: str, from_category: UnitCategory, to_category: UnitCategory) -> bool:
        """Check if we have density data for cross-category conversion"""
        item_key = self._normalize_item_name(item_name)
        
        # Check if we have the item in our density data
        if item_key in self.density_data['density_conversions']:
            item_data = self.density_data['density_conversions'][item_key]
            
            # Check if we have the needed conversion factors
            if from_category == UnitCategory.VOLUME and to_category == UnitCategory.MASS:
                return any(key in item_data for key in ['cup_to_grams', 'density_g_per_ml'])
            elif from_category == UnitCategory.MASS and to_category == UnitCategory.VOLUME:
                return any(key in item_data for key in ['cup_to_grams', 'density_g_per_ml'])
        
        # Check common conversions
        if item_key in self.density_data['common_conversions']:
            return True
        
        return False
    
    def _normalize_item_name(self, item_name: str) -> str:
        """Normalize item name for lookup"""
        # Convert to lowercase and remove common words
        normalized = item_name.lower().strip()
        
        # Remove common descriptors
        remove_words = ['all-purpose', 'whole', 'fresh', 'dried', 'raw', 'cooked']
        for word in remove_words:
            normalized = normalized.replace(word, '').strip()
        
        # Map common variations
        mappings = {
            'flour': 'flour',
            'ap flour': 'flour',
            'sugar': 'sugar',
            'white sugar': 'sugar',
            'granulated sugar': 'sugar',
            'milk': 'milk',
            'eggs': 'eggs',
            'egg': 'eggs',
            'butter': 'butter',
            'oil': 'oil',
            'vegetable oil': 'oil',
            'olive oil': 'olive_oil',
        }
        
        for variant, canonical in mappings.items():
            if variant in normalized:
                return canonical
        
        # Replace spaces with underscores for keys
        return normalized.replace(' ', '_')
    
    def get_suggested_unit(self, item_name: str, food_category: str) -> Tuple[str, UnitCategory]:
        """Get suggested unit for an item based on its name and category"""
        # This would integrate with the food_category_unit_rules
        # For now, return sensible defaults
        
        item_key = self._normalize_item_name(item_name)
        
        # Check if we have specific data for this item
        if item_key in self.density_data['density_conversions']:
            # Items with density data are typically measured by weight
            return ('g', UnitCategory.MASS)
        
        # Otherwise use category defaults
        category_defaults = {
            'produce': ('ea', UnitCategory.COUNT),
            'dairy': ('ml', UnitCategory.VOLUME),
            'meat': ('g', UnitCategory.MASS),
            'beverages': ('ml', UnitCategory.VOLUME),
            'grains': ('g', UnitCategory.MASS),
            'baking': ('g', UnitCategory.MASS),
        }
        
        default = category_defaults.get(food_category.lower(), ('ea', UnitCategory.COUNT))
        return default