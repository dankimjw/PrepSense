"""
Sustainability and Environmental Impact Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from backend_gateway.services.environmental_impact_service import get_environmental_impact_service
from backend_gateway.config.database import get_database_service
from backend_gateway.agents.sustainability_coach_agent import create_sustainability_coach_agent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/sustainability",
    tags=["sustainability"]
)


@router.get("/food-impact/{food_name}")
async def get_food_environmental_impact(food_name: str):
    """
    Get environmental impact data for a specific food item
    
    Args:
        food_name: Name of the food item
        
    Returns:
        Environmental impact data including CO2, land use, water use, and sustainability scores
    """
    try:
        impact_service = get_environmental_impact_service()
        impact_data = impact_service.get_food_impact(food_name)
        
        if not impact_data:
            raise HTTPException(
                status_code=404,
                detail=f"No environmental data found for {food_name}"
            )
        
        return {
            "food_name": food_name,
            "environmental_impact": impact_data['environmental'],
            "sustainability_profile": impact_data['sustainability_profile'],
            "owid_source": impact_data.get('owid_product', 'Unknown')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting food impact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipe-impact")
async def calculate_recipe_environmental_impact(
    ingredients: List[str] = Query(..., description="List of ingredients with quantities"),
    servings: int = Query(4, description="Number of servings")
):
    """
    Calculate total environmental impact for a recipe
    
    Args:
        ingredients: List of ingredient strings like "500g beef", "200g rice"
        servings: Number of servings to calculate per-serving impact
        
    Returns:
        Total and per-serving environmental impact
    """
    try:
        impact_service = get_environmental_impact_service()
        
        # Parse ingredients (simple parsing for now)
        parsed_ingredients = []
        for ing in ingredients:
            # Simple parsing: assume format "XXXg name" or "XXXkg name"
            parts = ing.split()
            if len(parts) >= 2:
                quantity_str = parts[0]
                name = ' '.join(parts[1:])
                
                # Convert to kg
                if quantity_str.endswith('g'):
                    quantity_kg = float(quantity_str[:-1]) / 1000
                elif quantity_str.endswith('kg'):
                    quantity_kg = float(quantity_str[:-2])
                else:
                    quantity_kg = 0.1  # Default 100g
                
                parsed_ingredients.append({
                    'name': name,
                    'quantity_kg': quantity_kg
                })
        
        # Calculate impact
        impact = impact_service.calculate_recipe_impact(parsed_ingredients)
        
        # Add per-serving calculations
        if servings > 0:
            impact['per_serving'] = {
                'ghg_kg_co2e': round(impact['total_ghg_kg_co2e'] / servings, 2),
                'land_m2': round(impact['total_land_m2'] / servings, 2),
                'water_L': round(impact['total_water_L'] / servings, 2)
            }
        
        return impact
        
    except Exception as e:
        logger.error(f"Error calculating recipe impact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sustainable-swaps/{ingredient}")
async def get_sustainable_swaps(
    ingredient: str,
    max_suggestions: int = Query(5, description="Maximum number of suggestions")
):
    """
    Get sustainable swap suggestions for an ingredient
    
    Args:
        ingredient: The ingredient to find swaps for
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        List of lower-impact alternatives with CO2 savings
    """
    try:
        impact_service = get_environmental_impact_service()
        swaps = impact_service.suggest_sustainable_swaps(ingredient, max_suggestions)
        
        if not swaps:
            return {
                "ingredient": ingredient,
                "message": f"No lower-impact alternatives found for {ingredient}",
                "suggestions": []
            }
        
        return {
            "ingredient": ingredient,
            "suggestions": swaps
        }
        
    except Exception as e:
        logger.error(f"Error getting sustainable swaps: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pantry-analysis")
async def analyze_pantry_sustainability(user_id: str):
    """
    Analyze the environmental impact of a user's pantry
    
    Args:
        user_id: The user's ID
        
    Returns:
        Sustainability analysis with total impact and improvement suggestions
    """
    try:
        # Get user's pantry items
        postgres_service = get_database_service()
        
        query = """
            SELECT 
                p.product_name,
                pi.quantity,
                p.ghg_kg_co2e_per_kg,
                p.impact_category,
                p.planet_score
            FROM pantry_items pi
            JOIN products p ON pi.product_id = p.product_id
            WHERE pi.user_id = %s AND pi.is_active = true
        """
        
        pantry_items = postgres_service.execute_query(
            query, 
            {'user_id': user_id}
        )
        
        if not pantry_items:
            return {
                "user_id": user_id,
                "message": "No items found in pantry",
                "total_impact": {},
                "suggestions": []
            }
        
        # Use the Sustainability Coach agent to analyze
        coach = create_sustainability_coach_agent()
        analysis = coach.analyze_pantry_sustainability(pantry_items)
        report = coach.create_sustainability_report(analysis)
        
        return {
            "user_id": user_id,
            "analysis": analysis,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Error analyzing pantry sustainability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eco-score/{product_id}")
async def get_product_eco_score(product_id: str):
    """
    Get the eco-score for a specific product
    
    Args:
        product_id: The product's ID
        
    Returns:
        Eco-score and environmental metrics
    """
    try:
        postgres_service = get_database_service()
        
        query = """
            SELECT 
                product_name,
                ghg_kg_co2e_per_kg,
                land_m2_per_kg,
                water_l_per_kg,
                impact_category,
                planet_score,
                ghg_visual
            FROM products
            WHERE product_id = %s
        """
        
        product = postgres_service.execute_query(
            query,
            {'product_id': product_id},
            fetch="one"
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Calculate eco-score (A-E rating based on planet_score)
        planet_score = product.get('planet_score', 5)
        if planet_score >= 8:
            eco_grade = 'A'
        elif planet_score >= 6:
            eco_grade = 'B'
        elif planet_score >= 4:
            eco_grade = 'C'
        elif planet_score >= 2:
            eco_grade = 'D'
        else:
            eco_grade = 'E'
        
        return {
            "product_id": product_id,
            "product_name": product['product_name'],
            "eco_score": {
                "grade": eco_grade,
                "planet_score": planet_score,
                "impact_category": product['impact_category'],
                "visual": product['ghg_visual']
            },
            "environmental_metrics": {
                "ghg_kg_co2e_per_kg": product['ghg_kg_co2e_per_kg'],
                "land_m2_per_kg": product['land_m2_per_kg'],
                "water_l_per_kg": product['water_l_per_kg']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting eco-score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))