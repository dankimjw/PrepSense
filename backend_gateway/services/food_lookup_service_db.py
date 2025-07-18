"""Food lookup service using local USDA database instead of API calls."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..models.nutrition import NutrientProfile, FoodItem
from ..config.database import get_database_service

logger = logging.getLogger(__name__)

@dataclass
class USDAFoodResult:
    """USDA food search result."""
    fdc_id: int
    description: str
    food_category: Optional[str] = None
    brand_name: Optional[str] = None
    nutrients: Optional[Dict[str, float]] = None
    serving_size: Optional[float] = None
    serving_size_unit: Optional[str] = None
    relevance_score: float = 0.0

class FoodLookupServiceDB:
    """Service for looking up food nutrition from local USDA database."""
    
    def __init__(self):
        """Initialize the food lookup service."""
        self.db_service = get_database_service()
        
    def search_foods(self, query: str, limit: int = 10, category: Optional[str] = None) -> List[USDAFoodResult]:
        """Search for foods in local USDA database."""
        try:
            logger.info(f"Searching USDA database for: {query}")
            
            # Build query with full-text search
            sql = """
                SELECT 
                    fdc_id,
                    description,
                    food_category,
                    brand_name,
                    serving_size,
                    serving_size_unit,
                    -- Calculate relevance score
                    CASE 
                        WHEN LOWER(description) = LOWER(%(query)s) THEN 1.0
                        WHEN LOWER(description) LIKE LOWER(%(query)s) || '%%' THEN 0.9
                        WHEN LOWER(description) LIKE '%%' || LOWER(%(query)s) || '%%' THEN 0.7
                        ELSE similarity(description, %(query)s)
                    END as relevance_score
                FROM usda_foods
                WHERE 
                    description ILIKE '%%' || %(query)s || '%%'
                    OR similarity(description, %(query)s) > 0.3
            """
            
            params = {"query": query}
            
            if category:
                sql += " AND food_category = %(category)s"
                params["category"] = category
                
            sql += """
                ORDER BY relevance_score DESC, description
                LIMIT %(limit)s
            """
            params["limit"] = limit
            
            results = self.db_service.execute_query(sql, params)
            
            foods = []
            for row in results:
                foods.append(USDAFoodResult(
                    fdc_id=row['fdc_id'],
                    description=row['description'],
                    food_category=row.get('food_category'),
                    brand_name=row.get('brand_name'),
                    serving_size=row.get('serving_size'),
                    serving_size_unit=row.get('serving_size_unit'),
                    relevance_score=row.get('relevance_score', 0.0)
                ))
                
            logger.info(f"Found {len(foods)} foods for query: {query}")
            return foods
            
        except Exception as e:
            logger.error(f"Error searching USDA database: {e}")
            return []
    
    def get_food_nutrition(self, fdc_id: int) -> Optional[USDAFoodResult]:
        """Get detailed nutrition for a specific food."""
        try:
            logger.info(f"Getting nutrition for FDC ID: {fdc_id}")
            
            # Try materialized view first (faster)
            sql = """
                SELECT 
                    fdc_id,
                    description,
                    food_category,
                    brand_name,
                    serving_size,
                    serving_size_unit,
                    nutrients
                FROM usda_food_nutrition
                WHERE fdc_id = %(fdc_id)s
            """
            
            results = self.db_service.execute_query(sql, {"fdc_id": fdc_id})
            
            if results:
                row = results[0]
                return USDAFoodResult(
                    fdc_id=row['fdc_id'],
                    description=row['description'],
                    food_category=row.get('food_category'),
                    brand_name=row.get('brand_name'),
                    serving_size=row.get('serving_size'),
                    serving_size_unit=row.get('serving_size_unit'),
                    nutrients=row.get('nutrients', {})
                )
            
            # Fallback to join query if materialized view doesn't have it
            sql = """
                SELECT 
                    f.fdc_id,
                    f.description,
                    f.food_category,
                    f.brand_name,
                    f.serving_size,
                    f.serving_size_unit,
                    n.nutrient_id,
                    n.amount,
                    n.unit
                FROM usda_foods f
                LEFT JOIN usda_nutrients n ON f.fdc_id = n.fdc_id
                WHERE f.fdc_id = %(fdc_id)s
                    AND n.nutrient_id IN (
                        1008, 1003, 1004, 1005, 1079, 2000, 1258, 
                        1093, 1087, 1089, 1162, 1106, 1114, 1092
                    )
            """
            
            results = self.db_service.execute_query(sql, {"fdc_id": fdc_id})
            
            if not results:
                return None
                
            # Build nutrient profile
            food_info = results[0]
            nutrients = {}
            
            nutrient_mapping = {
                1008: "calories",
                1003: "protein", 
                1004: "total_fat",
                1005: "carbohydrates",
                1079: "fiber",
                2000: "sugar",
                1258: "saturated_fat",
                1093: "sodium",
                1087: "calcium",
                1089: "iron",
                1162: "vitamin_c",
                1106: "vitamin_a",
                1114: "vitamin_d",
                1092: "potassium"
            }
            
            for row in results:
                nutrient_id = row.get('nutrient_id')
                if nutrient_id in nutrient_mapping:
                    nutrients[nutrient_mapping[nutrient_id]] = row.get('amount', 0.0)
            
            return USDAFoodResult(
                fdc_id=food_info['fdc_id'],
                description=food_info['description'],
                food_category=food_info.get('food_category'),
                brand_name=food_info.get('brand_name'),
                serving_size=food_info.get('serving_size'),
                serving_size_unit=food_info.get('serving_size_unit'),
                nutrients=nutrients
            )
            
        except Exception as e:
            logger.error(f"Error getting food nutrition: {e}")
            return None
    
    def lookup_food_nutrition(self, food_name: str, quantity: float = 1.0) -> Optional[FoodItem]:
        """Look up nutrition information for a food item."""
        try:
            # Search for the food
            search_results = self.search_foods(food_name, limit=5)
            
            if not search_results:
                logger.warning(f"No results found for: {food_name}")
                return None
            
            # Get the best match
            best_match = search_results[0]
            
            # Get detailed nutrition
            food_details = self.get_food_nutrition(best_match.fdc_id)
            
            if not food_details or not food_details.nutrients:
                logger.warning(f"No nutrition data found for: {food_name}")
                return None
            
            # Convert to NutrientProfile
            nutrient_profile = NutrientProfile(
                calories=food_details.nutrients.get("calories", 0),
                protein=food_details.nutrients.get("protein", 0),
                carbohydrates=food_details.nutrients.get("carbohydrates", 0),
                fiber=food_details.nutrients.get("fiber", 0),
                total_fat=food_details.nutrients.get("total_fat", 0),
                saturated_fat=food_details.nutrients.get("saturated_fat", 0),
                sugar=food_details.nutrients.get("sugar", 0),
                sodium=food_details.nutrients.get("sodium", 0),
                calcium=food_details.nutrients.get("calcium", 0),
                iron=food_details.nutrients.get("iron", 0),
                vitamin_c=food_details.nutrients.get("vitamin_c", 0),
                vitamin_a=food_details.nutrients.get("vitamin_a", 0),
                vitamin_d=food_details.nutrients.get("vitamin_d", 0),
                potassium=food_details.nutrients.get("potassium", 0)
            )
            
            # Adjust for quantity
            if quantity != 1.0 and food_details.serving_size:
                # Calculate factor based on serving size
                factor = quantity / food_details.serving_size
                nutrient_profile = nutrient_profile * factor
            
            # Create FoodItem
            food_item = FoodItem(
                name=food_details.description,
                usda_id=str(food_details.fdc_id),
                brand=food_details.brand_name,
                serving_size=food_details.serving_size or 100.0,
                serving_unit=food_details.serving_size_unit or "g",
                nutrients=nutrient_profile
            )
            
            logger.info(f"Successfully looked up nutrition for: {food_name}")
            return food_item
            
        except Exception as e:
            logger.error(f"Error looking up food nutrition: {e}")
            return None
    
    def batch_lookup_foods(self, food_names: List[str]) -> Dict[str, Optional[FoodItem]]:
        """Look up nutrition for multiple foods efficiently."""
        results = {}
        
        # Build a single query for all foods
        if not food_names:
            return results
            
        try:
            # Search for all foods in one query
            placeholders = ', '.join(['%s'] * len(food_names))
            sql = f"""
                WITH search_terms AS (
                    SELECT unnest(ARRAY[{placeholders}]) as term
                )
                SELECT DISTINCT ON (s.term)
                    s.term as search_term,
                    f.fdc_id,
                    f.description,
                    f.food_category,
                    f.brand_name,
                    f.serving_size,
                    f.serving_size_unit,
                    fn.nutrients,
                    similarity(f.description, s.term) as relevance_score
                FROM search_terms s
                CROSS JOIN LATERAL (
                    SELECT * FROM usda_foods
                    WHERE description ILIKE '%%' || s.term || '%%'
                        OR similarity(description, s.term) > 0.3
                    ORDER BY 
                        CASE 
                            WHEN LOWER(description) = LOWER(s.term) THEN 1.0
                            WHEN LOWER(description) LIKE LOWER(s.term) || '%%' THEN 0.9
                            ELSE similarity(description, s.term)
                        END DESC
                    LIMIT 1
                ) f
                LEFT JOIN usda_food_nutrition fn ON f.fdc_id = fn.fdc_id
                ORDER BY s.term, relevance_score DESC
            """
            
            batch_results = self.db_service.execute_query(sql, food_names)
            
            # Process results
            for row in batch_results:
                search_term = row['search_term']
                
                if row['fdc_id'] and row.get('nutrients'):
                    nutrients = row['nutrients']
                    
                    nutrient_profile = NutrientProfile(
                        calories=nutrients.get("calories", 0),
                        protein=nutrients.get("protein", 0),
                        carbohydrates=nutrients.get("carbohydrates", 0),
                        fiber=nutrients.get("fiber", 0),
                        total_fat=nutrients.get("total_fat", 0),
                        saturated_fat=nutrients.get("saturated_fat", 0),
                        sugar=nutrients.get("sugar", 0),
                        sodium=nutrients.get("sodium", 0),
                        calcium=nutrients.get("calcium", 0),
                        iron=nutrients.get("iron", 0),
                        vitamin_c=nutrients.get("vitamin_c", 0)
                    )
                    
                    food_item = FoodItem(
                        name=row['description'],
                        usda_id=str(row['fdc_id']),
                        brand=row.get('brand_name'),
                        serving_size=row.get('serving_size', 100.0),
                        serving_unit=row.get('serving_size_unit', 'g'),
                        nutrients=nutrient_profile
                    )
                    
                    results[search_term] = food_item
                else:
                    results[search_term] = None
                    
            # Add None for any not found
            for food_name in food_names:
                if food_name not in results:
                    results[food_name] = None
                    
        except Exception as e:
            logger.error(f"Error in batch lookup: {e}")
            # Return None for all on error
            for food_name in food_names:
                results[food_name] = None
                
        return results
    
    def get_food_suggestions(self, partial_name: str, max_suggestions: int = 10) -> List[str]:
        """Get food name suggestions for autocomplete."""
        try:
            sql = """
                SELECT DISTINCT description
                FROM usda_foods
                WHERE description ILIKE %(partial)s || '%%'
                    OR description ILIKE '%%' || %(partial)s || '%%'
                ORDER BY 
                    CASE 
                        WHEN description ILIKE %(partial)s || '%%' THEN 0
                        ELSE 1
                    END,
                    LENGTH(description),
                    description
                LIMIT %(limit)s
            """
            
            results = self.db_service.execute_query(
                sql, 
                {"partial": partial_name, "limit": max_suggestions}
            )
            
            return [row['description'] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting food suggestions: {e}")
            return []
    
    def refresh_materialized_view(self):
        """Refresh the materialized view for faster lookups."""
        try:
            sql = "REFRESH MATERIALIZED VIEW CONCURRENTLY usda_food_nutrition"
            self.db_service.execute_query(sql, {})
            logger.info("Refreshed USDA nutrition materialized view")
        except Exception as e:
            logger.error(f"Error refreshing materialized view: {e}")

# Create a singleton instance
food_lookup_service_db = FoodLookupServiceDB()