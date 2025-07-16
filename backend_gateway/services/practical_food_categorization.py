"""
Practical food categorization service using only Spoonacular + enhanced patterns
Since we only have Spoonacular API access, this focuses on what we can actually implement
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)

@dataclass
class FoodCategorization:
    item_name: str
    category: str
    allowed_units: List[str]
    default_unit: str
    confidence: float
    source: str
    reasoning: str = ""

class PracticalFoodCategorizationService:
    """
    Practical food categorization using Spoonacular + comprehensive pattern matching
    Designed to work with actual available APIs
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.spoonacular = SpoonacularService()
        self.cache = {}  # In-memory cache
        self.cache_expiry = timedelta(hours=24)
        
        # Comprehensive categorization patterns based on real food knowledge
        self.category_patterns = {
            'produce_countable': {
                'patterns': [
                    r'\b(apple|apples|banana|bananas|orange|oranges|lemon|lemons|lime|limes)\b',
                    r'\b(avocado|avocados|tomato|tomatoes|potato|potatoes|onion|onions)\b',
                    r'\b(carrot|carrots|bell pepper|peppers|cucumber|cucumbers|zucchini)\b',
                    r'\b(egg|eggs|whole egg|large egg|medium egg|small egg)\b',
                    r'\b(peach|peaches|pear|pears|plum|plums|mango|mangoes|kiwi|kiwis)\b'
                ],
                'allowed': ['each', 'piece', 'whole', 'bag', 'package', 'g', 'oz', 'lb', 'kg'],
                'default': 'each',
                'forbidden': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon', 'pint', 'quart'],
                'reasoning': 'Countable produce items are typically measured by pieces or weight'
            },
            
            'produce_measurable': {
                'patterns': [
                    r'\b(lettuce|spinach|kale|arugula|mixed greens|salad)\b',
                    r'\b(broccoli|cauliflower|cabbage|brussels sprouts)\b',
                    r'\b(herbs|cilantro|parsley|basil|oregano|thyme|rosemary)\b',
                    r'\b(berries|blueberries|strawberries|raspberries|blackberries)\b',
                    r'\b(grapes|cherries|cranberries)\b'
                ],
                'allowed': ['g', 'oz', 'lb', 'kg', 'cup', 'bunch', 'head', 'bag', 'package', 'container'],
                'default': 'cup',
                'forbidden': ['ml', 'l', 'fl oz', 'tbsp', 'tsp', 'gallon', 'pint', 'quart'],
                'reasoning': 'Leafy/small produce typically measured by volume (cups) or weight'
            },
            
            'liquids': {
                'patterns': [
                    r'\b(milk|water|juice|oil|vinegar|wine|beer|soda|coffee|tea)\b',
                    r'\b(syrup|honey|sauce|dressing|broth|stock)\b',
                    r'\b(coconut milk|almond milk|oat milk|soy milk)\b',
                    r'\b(olive oil|vegetable oil|canola oil|cooking oil)\b',
                    r'\b(orange juice|apple juice|cranberry juice|grape juice)\b'
                ],
                'allowed': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon', 'pint', 'quart', 'bottle', 'can'],
                'default': 'cup',
                'forbidden': ['each', 'piece', 'whole'],
                'reasoning': 'Liquids are measured by volume'
            },
            
            'dry_goods': {
                'patterns': [
                    r'\b(flour|sugar|salt|pepper|rice|pasta|quinoa|oats)\b',
                    r'\b(cereal|granola|nuts|seeds|dried fruit)\b',
                    r'\b(spice|seasoning|powder|extract|baking powder|baking soda)\b',
                    r'\b(brown rice|white rice|wild rice|jasmine rice|basmati rice)\b',
                    r'\b(all[- ]purpose flour|whole wheat flour|almond flour)\b'
                ],
                'allowed': ['g', 'oz', 'lb', 'kg', 'cup', 'tbsp', 'tsp', 'bag', 'package', 'box'],
                'default': 'cup',
                'forbidden': ['ml', 'l', 'fl oz', 'gallon', 'pint', 'quart'],
                'reasoning': 'Dry goods can be measured by weight or volume (cups/spoons)'
            },
            
            'meat_seafood': {
                'patterns': [
                    r'\b(chicken|beef|pork|turkey|fish|salmon|tuna|shrimp|lamb)\b',
                    r'\b(ground beef|ground turkey|ground chicken)\b',
                    r'\b(chicken breast|chicken thigh|chicken wing|drumstick)\b',
                    r'\b(steak|roast|fillet|cutlet|chop)\b',
                    r'\b(cod|tilapia|mahi mahi|halibut|sea bass|trout)\b'
                ],
                'allowed': ['g', 'oz', 'lb', 'kg', 'piece', 'fillet', 'package', 'serving'],
                'default': 'oz',
                'forbidden': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon'],
                'reasoning': 'Meat and seafood are measured by weight or pieces'
            },
            
            'dairy': {
                'patterns': [
                    r'\b(cheese|yogurt|butter|cream|sour cream|cottage cheese)\b',
                    r'\b(cheddar|mozzarella|parmesan|swiss|gouda|brie)\b',
                    r'\b(greek yogurt|plain yogurt|vanilla yogurt)\b',
                    r'\b(heavy cream|whipping cream|half and half)\b'
                ],
                'allowed': ['g', 'oz', 'lb', 'kg', 'ml', 'l', 'fl oz', 'cup', 'tbsp', 'container', 'package', 'slice'],
                'default': 'oz',
                'forbidden': ['each', 'piece', 'whole'],
                'reasoning': 'Dairy can be solid (cheese) or liquid (milk), allowing both weight and volume'
            },
            
            'snacks_bars': {
                'patterns': [
                    # Generic bar patterns
                    r'\b(bar|bars)\b.*\b(cereal|granola|protein|energy|snack|nutrition)\b',
                    r'\b(cereal|granola|protein|energy|snack|nutrition)\b.*\b(bar|bars)\b',
                    # Brand-specific patterns
                    r'\btrader joe\'?s.*bar\b',
                    r'\bkind.*bar\b',
                    r'\bclif.*bar\b',
                    r'\bquest.*bar\b',
                    r'\brxbar\b',
                    r'\bpower.*bar\b',
                    r'\bnature valley.*bar\b',
                    # Additional bar types
                    r'\b(chocolate bar|candy bar|breakfast bar|meal bar)\b'
                ],
                'allowed': ['each', 'piece', 'bar', 'package', 'box', 'g', 'oz'],
                'default': 'each',
                'forbidden': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon', 'pint', 'quart'],
                'reasoning': 'Bars are solid items counted by pieces or measured by weight'
            },
            
            'packaged_snacks': {
                'patterns': [
                    r'\b(chips|crackers|cookies|pretzels|popcorn)\b',
                    r'\b(trail mix|mixed nuts|dried fruit|raisins)\b',
                    r'\b(goldfish|cheez[- ]its|doritos|lays|pringles)\b',
                    r'\b(oreos|chips ahoy|pepperidge farm)\b'
                ],
                'allowed': ['g', 'oz', 'bag', 'package', 'box', 'container', 'piece', 'serving'],
                'default': 'oz',
                'forbidden': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon'],
                'reasoning': 'Packaged snacks are typically measured by weight or package size'
            },
            
            'frozen_foods': {
                'patterns': [
                    r'\b(frozen.*|.*frozen)\b',
                    r'\b(ice cream|frozen yogurt|sherbet|sorbet)\b',
                    r'\b(frozen pizza|frozen meal|tv dinner)\b',
                    r'\b(frozen vegetables|frozen fruit|frozen berries)\b'
                ],
                'allowed': ['g', 'oz', 'lb', 'kg', 'cup', 'package', 'container', 'piece', 'serving'],
                'default': 'cup',
                'forbidden': ['ml', 'l', 'fl oz', 'tbsp', 'tsp', 'gallon'],
                'reasoning': 'Frozen foods vary - ice cream by volume, frozen meals by package, etc.'
            }
        }
        
        # Special validation rules for common mistakes
        self.validation_rules = {
            'bars_no_liquid': {
                'condition': lambda item: 'bar' in item.lower(),
                'forbidden_units': ['ml', 'l', 'fl oz', 'cup', 'tbsp', 'tsp', 'gallon', 'pint', 'quart'],
                'message': "Bars cannot be measured in liquid units. Try 'each', 'piece', or 'package'.",
                'suggested_units': ['each', 'piece', 'package', 'g', 'oz']
            },
            'meat_no_volume': {
                'condition': lambda item: any(meat in item.lower() for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']),
                'forbidden_units': ['ml', 'l', 'fl oz', 'gallon', 'pint', 'quart'],
                'message': "Meat should be measured by weight or pieces, not volume.",
                'suggested_units': ['oz', 'lb', 'g', 'kg', 'piece', 'fillet']
            },
            'produce_count_no_volume': {
                'condition': lambda item: any(fruit in item.lower() for fruit in ['apple', 'banana', 'orange', 'potato', 'onion']),
                'forbidden_units': ['ml', 'l', 'fl oz', 'gallon', 'pint', 'quart'],
                'message': "Whole fruits/vegetables should be counted or weighed, not measured by volume.",
                'suggested_units': ['each', 'piece', 'g', 'oz', 'lb']
            }
        }
    
    async def categorize_food_item(self, item_name: str, use_cache: bool = True) -> FoodCategorization:
        """
        Categorize a food item using Spoonacular + enhanced pattern matching
        """
        item_name_lower = item_name.lower().strip()
        
        # Check cache first
        if use_cache and item_name_lower in self.cache:
            cached_result = self.cache[item_name_lower]
            if datetime.now() - cached_result['timestamp'] < self.cache_expiry:
                return cached_result['categorization']
        
        # Try Spoonacular first (our only external API)
        try:
            spoon_result = await self._categorize_with_spoonacular(item_name)
            if spoon_result and spoon_result.confidence > 0.7:
                self._cache_result(item_name_lower, spoon_result)
                return spoon_result
        except Exception as e:
            logger.warning(f"Spoonacular categorization failed: {e}")
        
        # Fallback to enhanced pattern matching
        pattern_result = self._categorize_with_enhanced_patterns(item_name)
        self._cache_result(item_name_lower, pattern_result)
        
        return pattern_result
    
    async def _categorize_with_spoonacular(self, item_name: str) -> Optional[FoodCategorization]:
        """Categorize using Spoonacular API"""
        try:
            # Use the parse ingredients endpoint
            parsed = self.spoonacular.parse_ingredients([item_name])
            if parsed and len(parsed) > 0:
                ingredient = parsed[0]
                
                # Map Spoonacular category to our categories
                spoon_category = ingredient.get('category', '').lower()
                our_category = self._map_spoonacular_category(spoon_category, item_name)
                
                category_info = self.category_patterns.get(our_category, self.category_patterns['produce_countable'])
                
                return FoodCategorization(
                    item_name=item_name,
                    category=our_category,
                    allowed_units=category_info['allowed'],
                    default_unit=category_info['default'],
                    confidence=0.8,
                    source='spoonacular',
                    reasoning=f"Spoonacular classified as '{spoon_category}', mapped to {our_category}"
                )
        except Exception as e:
            logger.error(f"Spoonacular categorization error: {e}")
            return None
    
    def _categorize_with_enhanced_patterns(self, item_name: str) -> FoodCategorization:
        """Enhanced pattern matching with specific brand and product recognition"""
        item_lower = item_name.lower()
        
        # Score each category
        category_scores = {}
        
        for category, info in self.category_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in info['patterns']:
                if re.search(pattern, item_lower):
                    score += 1
                    matched_patterns.append(pattern)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'patterns': matched_patterns,
                    'info': info
                }
        
        # Find best match
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
            best_info = category_scores[best_category]
            
            confidence = min(0.7, 0.3 + (best_info['score'] * 0.1))  # Scale confidence based on matches
            
            return FoodCategorization(
                item_name=item_name,
                category=best_category,
                allowed_units=best_info['info']['allowed'],
                default_unit=best_info['info']['default'],
                confidence=confidence,
                source='enhanced_patterns',
                reasoning=f"Matched {best_info['score']} pattern(s) for {best_category}: {best_info['patterns']}"
            )
        
        # Default fallback
        return FoodCategorization(
            item_name=item_name,
            category='dry_goods',  # Safe default that allows both weight and volume
            allowed_units=self.category_patterns['dry_goods']['allowed'],
            default_unit=self.category_patterns['dry_goods']['default'],
            confidence=0.2,
            source='fallback',
            reasoning="No specific patterns matched, using dry_goods as safe default"
        )
    
    def _map_spoonacular_category(self, spoon_category: str, item_name: str) -> str:
        """Map Spoonacular category to our internal categories"""
        category_mapping = {
            'produce': self._determine_produce_type(item_name),
            'dairy': 'dairy',
            'meat': 'meat_seafood',
            'seafood': 'meat_seafood',
            'beverage': 'liquids',
            'condiment': 'liquids' if any(liquid in item_name.lower() for liquid in ['sauce', 'dressing', 'syrup']) else 'dry_goods',
            'baking': 'dry_goods',
            'snack': 'snacks_bars' if 'bar' in item_name.lower() else 'packaged_snacks'
        }
        return category_mapping.get(spoon_category, 'dry_goods')
    
    def _determine_produce_type(self, item_name: str) -> str:
        """Determine if produce is countable or measurable"""
        countable_items = ['apple', 'banana', 'orange', 'lemon', 'lime', 'avocado', 'tomato', 'potato', 'onion', 'carrot', 'pepper']
        item_lower = item_name.lower()
        
        if any(item in item_lower for item in countable_items):
            return 'produce_countable'
        return 'produce_measurable'
    
    async def validate_unit_for_item(self, item_name: str, unit: str) -> Dict[str, Any]:
        """
        Validate if a unit is appropriate for a given item
        """
        categorization = await self.categorize_food_item(item_name)
        
        unit_lower = unit.lower().strip()
        allowed_units = [u.lower() for u in categorization.allowed_units]
        
        # Check basic validity
        is_valid = unit_lower in allowed_units
        
        result = {
            'is_valid': is_valid,
            'item_name': item_name,
            'unit': unit,
            'category': categorization.category,
            'confidence': categorization.confidence,
            'source': categorization.source,
            'reasoning': categorization.reasoning
        }
        
        # Check special validation rules
        for rule_name, rule in self.validation_rules.items():
            if rule['condition'](item_name) and unit_lower in [u.lower() for u in rule['forbidden_units']]:
                result['is_valid'] = False
                result['error'] = rule['message']
                result['suggested_units'] = rule['suggested_units']
                result['rule_triggered'] = rule_name
                break
        
        if not is_valid and 'error' not in result:
            result['error'] = f"Unit '{unit}' is not appropriate for {item_name} (category: {categorization.category})"
            result['suggested_units'] = categorization.allowed_units[:5]
            result['default_unit'] = categorization.default_unit
        
        return result
    
    def _cache_result(self, item_name: str, categorization: FoodCategorization):
        """Cache categorization result in memory"""
        self.cache[item_name] = {
            'categorization': categorization,
            'timestamp': datetime.now()
        }
    
    def get_suggested_units_for_category(self, category: str) -> List[str]:
        """Get suggested units for a given category"""
        return self.category_patterns.get(category, {}).get('allowed', ['each', 'g', 'oz', 'cup'])
    
    def get_default_unit_for_category(self, category: str) -> str:
        """Get default unit for a given category"""
        return self.category_patterns.get(category, {}).get('default', 'each')

# Global service instance
_practical_food_service = None

def get_practical_food_service(db_service=None) -> PracticalFoodCategorizationService:
    """Get singleton instance of PracticalFoodCategorizationService"""
    global _practical_food_service
    if _practical_food_service is None:
        _practical_food_service = PracticalFoodCategorizationService(db_service)
    return _practical_food_service