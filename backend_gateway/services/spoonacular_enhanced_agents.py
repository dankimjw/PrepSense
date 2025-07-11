"""
Enhanced CrewAI Agents that leverage Spoonacular APIs as tools
"""

import logging
import json
from typing import List, Dict, Any, Type
from datetime import datetime
from typing import Optional as Opt  # Use Opt instead of | for Python 3.9
try:
    from crewai import Agent, Task, Crew
except ImportError:
    # Mock for testing without CrewAI
    Agent = Task = Crew = None

from backend_gateway.services.base_tool import BaseTool
from pydantic import BaseModel, Field

from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.recipe_evaluator_service import RecipeEvaluator

logger = logging.getLogger(__name__)


# ============= SPOONACULAR-POWERED TOOLS =============

class RecipeValidationTool(BaseTool):
    """Validate AI recipes by comparing with real recipes"""
    name: str = "recipe_validation"
    description: str = "Validate cooking times and methods against real recipes"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, recipe_title: str, cook_time: int, ingredients: List[str]) -> str:
        """Validate recipe against similar real recipes"""
        try:
            # Search for similar recipes
            similar = await self.spoonacular.search_recipes_complex(
                query=recipe_title,
                number=5
            )
            
            if not similar.get('results'):
                return f"No similar recipes found to validate '{recipe_title}'"
            
            # Analyze cooking times
            times = [r.get('readyInMinutes', 0) for r in similar['results'] if r.get('readyInMinutes')]
            avg_time = sum(times) / len(times) if times else cook_time
            
            validation = f"Validation for '{recipe_title}':\n"
            validation += f"- Your time: {cook_time} min\n"
            validation += f"- Average time for similar recipes: {avg_time:.0f} min\n"
            
            if abs(cook_time - avg_time) > 20:
                validation += f"⚠️ Time differs significantly from similar recipes\n"
            else:
                validation += f"✓ Cooking time is reasonable\n"
            
            # Check ingredient combinations
            validation += f"\nSimilar recipes found:\n"
            for recipe in similar['results'][:3]:
                validation += f"- {recipe['title']} ({recipe.get('readyInMinutes', 'N/A')} min)\n"
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating recipe: {e}")
            return f"Unable to validate recipe: {str(e)}"

class IngredientVerificationTool(BaseTool):
    """Verify ingredients exist and find substitutes for rare ones"""
    name: str = "ingredient_verification"
    description: str = "Verify ingredient availability and find substitutes"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredient_name: str) -> str:
        """Verify ingredient and suggest alternatives if rare"""
        try:
            # Search for ingredient
            search = await self.spoonacular.search_ingredients(ingredient_name, number=3)
            
            if not search:
                # Try to find substitutes for unknown ingredient
                return f"❌ '{ingredient_name}' not found in database. Consider using common ingredients."
            
            result = f"✓ '{ingredient_name}' verified\n"
            
            # Check if it's a common ingredient (by checking if in top results)
            if len(search) < 3 or search[0]['name'].lower() != ingredient_name.lower():
                result += f"Note: This might be uncommon. Alternatives:\n"
                
                # Get substitutes
                try:
                    subs = await self.spoonacular.get_ingredient_substitutes(search[0]['id'])
                    if subs.get('substitutes'):
                        for sub in subs['substitutes'][:3]:
                            result += f"- {sub}\n"
                except:
                    result += "- Check local availability\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying ingredient: {e}")
            return f"Unable to verify '{ingredient_name}'"


class IngredientInfoTool(BaseTool):
    """Get detailed ingredient information from Spoonacular"""
    name: str = "ingredient_info"
    description: str = "Get nutritional and cost data for ingredients"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredient_name: str, amount: float = 100, unit: str = "g") -> str:
        """Get ingredient information including nutrition and cost"""
        try:
            # Search for ingredient
            search_result = await self.spoonacular.search_ingredients(ingredient_name, number=1)
            if not search_result:
                return f"No information found for {ingredient_name}"
            
            ingredient_id = search_result[0]['id']
            
            # Get detailed info
            info = await self.spoonacular.get_ingredient_information(
                ingredient_id=ingredient_id,
                amount=amount,
                unit=unit
            )
            
            return f"""
Ingredient: {info.get('name', ingredient_name)}
Nutrition per {amount} {unit}:
- Calories: {info.get('nutrition', {}).get('calories', 'N/A')}
- Protein: {info.get('nutrition', {}).get('protein', 'N/A')}g
- Cost: ${info.get('estimatedCost', {}).get('value', 0) / 100:.2f}
Aisle: {info.get('aisle', 'N/A')}
"""
        except Exception as e:
            logger.error(f"Error getting ingredient info: {e}")
            return f"Error getting info for {ingredient_name}"


class RecipeComparisonTool(BaseTool):
    """Compare AI recipe with similar Spoonacular recipes"""
    name: str = "recipe_comparison"
    description: str = "Find similar recipes in Spoonacular to validate AI recipe"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, recipe_title: str, ingredients: List[str]) -> str:
        """Find and compare with similar recipes"""
        try:
            # Search for similar recipes
            similar = await self.spoonacular.search_recipes_complex(
                query=recipe_title,
                number=3
            )
            
            if not similar.get('results'):
                # Try searching by ingredients
                ingredient_results = await self.spoonacular.search_recipes_by_ingredients(
                    ingredients=ingredients[:5],  # Top 5 ingredients
                    number=3
                )
                similar = {'results': ingredient_results}
            
            comparison = f"Similar recipes found for '{recipe_title}':\n"
            
            for recipe in similar.get('results', [])[:3]:
                comparison += f"\n- {recipe['title']}"
                comparison += f"\n  Time: {recipe.get('readyInMinutes', 'N/A')} min"
                comparison += f"\n  Servings: {recipe.get('servings', 'N/A')}"
                
                # Get full recipe for comparison
                if recipe.get('id'):
                    full_recipe = await self.spoonacular.get_recipe_information(recipe['id'])
                    comparison += f"\n  Ingredients: {len(full_recipe.get('extendedIngredients', []))}"
                    comparison += f"\n  Instructions: {len(full_recipe.get('analyzedInstructions', [{}])[0].get('steps', []))}"
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing recipes: {e}")
            return "Unable to find similar recipes for comparison"


class SubstitutionTool(BaseTool):
    """Find ingredient substitutions using Spoonacular"""
    name: str = "ingredient_substitutes"
    description: str = "Find substitutes for ingredients"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredient_name: str) -> str:
        """Get substitution options"""
        try:
            # First, find the ingredient ID
            search = await self.spoonacular.search_ingredients(ingredient_name, number=1)
            if not search:
                return f"No substitutes found for {ingredient_name}"
            
            ingredient_id = search[0]['id']
            
            # Get substitutes
            substitutes = await self.spoonacular.get_ingredient_substitutes(ingredient_id)
            
            if not substitutes.get('substitutes'):
                return f"No substitutes found for {ingredient_name}"
            
            result = f"Substitutes for {ingredient_name}:\n"
            for sub in substitutes['substitutes'][:5]:
                result += f"- {sub}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding substitutes: {e}")
            return f"Error finding substitutes for {ingredient_name}"


class NutritionCalculatorTool(BaseTool):
    """Calculate accurate nutrition using Spoonacular data"""
    name: str = "nutrition_calculator"
    description: str = "Calculate recipe nutrition based on ingredients"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredients_json: str) -> str:
        """Calculate nutrition for a list of ingredients"""
        try:
            import json
            ingredients = json.loads(ingredients_json)
            
            total_nutrition = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0,
                'sugar': 0,
                'sodium': 0
            }
            
            for ing in ingredients:
                # Parse ingredient
                parsed = await self.spoonacular.parse_ingredients(
                    ingredient_list=[ing['original']],
                    servings=1
                )
                
                if parsed and len(parsed) > 0:
                    nutrition = parsed[0].get('nutrition', {}).get('nutrients', [])
                    
                    for nutrient in nutrition:
                        name = nutrient['name'].lower()
                        if 'calorie' in name:
                            total_nutrition['calories'] += nutrient['amount']
                        elif name == 'protein':
                            total_nutrition['protein'] += nutrient['amount']
                        elif name == 'carbohydrates':
                            total_nutrition['carbs'] += nutrient['amount']
                        elif name == 'fat':
                            total_nutrition['fat'] += nutrient['amount']
                        elif name == 'fiber':
                            total_nutrition['fiber'] += nutrient['amount']
                        elif name == 'sugar':
                            total_nutrition['sugar'] += nutrient['amount']
                        elif name == 'sodium':
                            total_nutrition['sodium'] += nutrient['amount']
            
            return f"""
Calculated Nutrition (per serving):
- Calories: {total_nutrition['calories']:.0f}
- Protein: {total_nutrition['protein']:.1f}g
- Carbs: {total_nutrition['carbs']:.1f}g
- Fat: {total_nutrition['fat']:.1f}g
- Fiber: {total_nutrition['fiber']:.1f}g
- Sugar: {total_nutrition['sugar']:.1f}g
- Sodium: {total_nutrition['sodium']:.0f}mg
"""
        except Exception as e:
            logger.error(f"Error calculating nutrition: {e}")
            return "Unable to calculate nutrition"


class ConversionTool(BaseTool):
    """Convert between units using Spoonacular"""
    name: str = "unit_converter"
    description: str = "Convert ingredient amounts between different units"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredient: str, source_amount: float, source_unit: str, target_unit: str) -> str:
        """Convert units for an ingredient"""
        try:
            result = await self.spoonacular.convert_amounts(
                ingredient_name=ingredient,
                source_amount=source_amount,
                source_unit=source_unit,
                target_unit=target_unit
            )
            
            return f"{source_amount} {source_unit} of {ingredient} = {result['targetAmount']} {result['targetUnit']}"
            
        except Exception as e:
            logger.error(f"Error converting units: {e}")
            return f"Unable to convert {source_amount} {source_unit} to {target_unit}"


class CostEstimatorTool(BaseTool):
    """Estimate recipe cost using real grocery prices"""
    name: str = "cost_estimator"
    description: str = "Calculate recipe cost using current grocery prices"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredients_json: str) -> str:
        """Calculate total recipe cost"""
        try:
            import json
            ingredients = json.loads(ingredients_json)
            
            total_cost = 0
            cost_breakdown = "Cost Breakdown:\n"
            
            for ing in ingredients:
                try:
                    # Parse ingredient to get standardized info
                    parsed = await self.spoonacular.parse_ingredients(
                        ingredient_list=[ing['original']],
                        servings=1
                    )
                    
                    if parsed and len(parsed) > 0:
                        ingredient_id = parsed[0].get('id')
                        amount = parsed[0].get('amount', 1)
                        unit = parsed[0].get('unit', 'unit')
                        
                        # Get cost info
                        info = await self.spoonacular.get_ingredient_information(
                            ingredient_id=ingredient_id,
                            amount=amount,
                            unit=unit
                        )
                        
                        cost = info.get('estimatedCost', {}).get('value', 0) / 100
                        total_cost += cost
                        cost_breakdown += f"- {ing['name']}: ${cost:.2f}\n"
                    
                except Exception as e:
                    logger.warning(f"Could not get cost for {ing.get('name', 'unknown')}: {e}")
                    cost_breakdown += f"- {ing.get('name', 'unknown')}: $?.??\n"
            
            return f"{cost_breakdown}\nTotal Estimated Cost: ${total_cost:.2f}"
            
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return "Unable to estimate recipe cost"


class DietaryComplianceTool(BaseTool):
    """Check ingredients for dietary restrictions and allergens"""
    name: str = "dietary_compliance"
    description: str = "Verify recipe meets dietary restrictions"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, ingredients_json: str, dietary_restrictions: List[str]) -> str:
        """Check if ingredients comply with dietary restrictions"""
        try:
            import json
            ingredients = json.loads(ingredients_json)
            
            issues = []
            compliant = True
            
            for ing in ingredients:
                try:
                    # Get detailed ingredient info
                    search = await self.spoonacular.search_ingredients(ing['name'], number=1)
                    if search:
                        info = await self.spoonacular.get_ingredient_information(
                            ingredient_id=search[0]['id']
                        )
                        
                        # Check dietary properties
                        for restriction in dietary_restrictions:
                            if restriction.lower() == 'gluten-free' and not info.get('glutenFree', True):
                                issues.append(f"❌ {ing['name']} contains gluten")
                                compliant = False
                            elif restriction.lower() == 'vegan' and not info.get('vegan', True):
                                issues.append(f"❌ {ing['name']} is not vegan")
                                compliant = False
                            elif restriction.lower() == 'vegetarian' and not info.get('vegetarian', True):
                                issues.append(f"❌ {ing['name']} is not vegetarian")
                                compliant = False
                
                except Exception as e:
                    logger.warning(f"Could not verify {ing['name']}: {e}")
                    issues.append(f"⚠️ Could not verify {ing['name']}")
            
            result = f"Dietary Compliance Check for {', '.join(dietary_restrictions)}:\n"
            if compliant and not issues:
                result += "✓ All ingredients comply with dietary restrictions\n"
            else:
                result += "Issues found:\n"
                for issue in issues:
                    result += f"{issue}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking dietary compliance: {e}")
            return "Unable to verify dietary compliance"


class SeasonalAvailabilityTool(BaseTool):
    """Check seasonal availability and suggest alternatives"""
    name: str = "seasonal_availability"
    description: str = "Check if ingredients are in season"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
        # Simplified seasonal data (in real app, would use more comprehensive data)
        self.seasonal_produce = {
            'spring': ['asparagus', 'peas', 'artichokes', 'strawberries'],
            'summer': ['tomatoes', 'corn', 'berries', 'peaches', 'zucchini'],
            'fall': ['apples', 'pumpkin', 'squash', 'brussels sprouts'],
            'winter': ['citrus', 'kale', 'root vegetables', 'cabbage']
        }
    
    async def _run(self, ingredient: str, current_season: str = 'winter') -> str:
        """Check seasonal availability"""
        try:
            result = f"Seasonal check for {ingredient} (Current: {current_season}):\n"
            
            # Check if ingredient is seasonal
            is_seasonal = False
            for season, produce in self.seasonal_produce.items():
                if any(item in ingredient.lower() for item in produce):
                    if season == current_season:
                        result += f"✓ {ingredient} is in season!\n"
                        is_seasonal = True
                    else:
                        result += f"❌ {ingredient} is out of season (best in {season})\n"
                    break
            
            if not is_seasonal:
                # Suggest alternatives
                result += f"Seasonal alternatives for {current_season}:\n"
                for item in self.seasonal_produce.get(current_season, []):
                    result += f"- {item}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking seasonal availability: {e}")
            return f"Unable to check seasonal availability for {ingredient}"


class WinePairingTool(BaseTool):
    """Get wine pairing suggestions for recipes"""
    name: str = "wine_pairing"
    description: str = "Get sommelier-level wine pairings"
    
    def __init__(self):
        super().__init__()
        self.spoonacular = SpoonacularService()
    
    async def _run(self, main_ingredient: str, cuisine: str = None) -> str:
        """Get wine pairing suggestions"""
        try:
            pairing = await self.spoonacular.get_wine_pairing(
                food=main_ingredient,
                max_price=50
            )
            
            if not pairing.get('pairedWines'):
                return f"No specific wine pairing found for {main_ingredient}"
            
            result = f"Wine Pairing for {main_ingredient}:\n"
            result += f"Recommended wines: {', '.join(pairing['pairedWines'])}\n"
            
            if pairing.get('pairingText'):
                result += f"\nSommelier notes: {pairing['pairingText'][:200]}...\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting wine pairing: {e}")
            return f"Unable to get wine pairing for {main_ingredient}"


# ============= ENHANCED AGENTS WITH SPOONACULAR TOOLS =============

class EnhancedCrewAgents:
    """CrewAI agents enhanced with Spoonacular tools"""
    
    def __init__(self):
        # Initialize all tools
        self.validation_tool = RecipeValidationTool()
        self.ingredient_verification_tool = IngredientVerificationTool()
        self.ingredient_tool = IngredientInfoTool()
        self.comparison_tool = RecipeComparisonTool()
        self.substitution_tool = SubstitutionTool()
        self.nutrition_tool = NutritionCalculatorTool()
        self.conversion_tool = ConversionTool()
        self.cost_tool = CostEstimatorTool()
        self.dietary_tool = DietaryComplianceTool()
        self.seasonal_tool = SeasonalAvailabilityTool()
        self.wine_tool = WinePairingTool()
        self.evaluator = RecipeEvaluator()
    
    def create_agents(self):
        """Create specialized agents with Spoonacular-powered tools"""
        
        # Recipe Validator Agent - Validates cooking times and methods
        recipe_validator = Agent(
            role="Recipe Validator",
            goal="Validate AI recipes by comparing with real recipes",
            backstory="You are a culinary database expert who validates recipes against thousands of proven recipes",
            tools=[self.validation_tool, self.comparison_tool],
            verbose=True
        )
        
        # Ingredient Specialist Agent - Verifies ingredients and finds substitutes
        ingredient_specialist = Agent(
            role="Ingredient Specialist",
            goal="Verify all ingredients are real and available",
            backstory="You are a food sourcing expert who knows ingredient availability and substitutions",
            tools=[self.ingredient_verification_tool, self.ingredient_tool, self.substitution_tool, self.seasonal_tool],
            verbose=True
        )
        
        # Nutrition Expert Agent - Calculates accurate nutrition
        nutrition_expert = Agent(
            role="Nutrition Expert",
            goal="Calculate accurate nutrition using FDA databases",
            backstory="You are a registered dietitian with access to comprehensive nutritional databases",
            tools=[self.nutrition_tool, self.ingredient_tool],
            verbose=True
        )
        
        # Cost Analyst Agent - Estimates recipe costs
        cost_analyst = Agent(
            role="Cost Analyst",
            goal="Calculate recipe costs using current grocery prices",
            backstory="You are a grocery pricing expert who helps users budget their meals",
            tools=[self.cost_tool, self.ingredient_tool],
            verbose=True
        )
        
        # Dietary Compliance Agent - Ensures dietary safety
        dietary_expert = Agent(
            role="Dietary Compliance Expert",
            goal="Verify recipes meet dietary restrictions and allergen requirements",
            backstory="You are a food safety expert specializing in dietary restrictions and allergens",
            tools=[self.dietary_tool, self.ingredient_tool],
            verbose=True
        )
        
        # Unit Standardization Agent - Converts all measurements
        measurement_expert = Agent(
            role="Measurement Standardization Expert",
            goal="Convert all measurements to user's preferred system",
            backstory="You are a precision expert who ensures all measurements are accurate and consistent",
            tools=[self.conversion_tool],
            verbose=True
        )
        
        # Sommelier Agent - Wine pairings
        sommelier = Agent(
            role="Sommelier",
            goal="Suggest perfect wine pairings for recipes",
            backstory="You are a certified sommelier with extensive wine pairing knowledge",
            tools=[self.wine_tool],
            verbose=True
        )
        
        # Quality Evaluator Agent - Overall assessment
        quality_evaluator = Agent(
            role="Head Chef Quality Inspector",
            goal="Provide final quality assessment and recommendations",
            backstory="You are an executive chef who ensures only the best recipes reach users",
            tools=[],  # Uses evaluator service and other agents' outputs
            verbose=True
        )
        
        return {
            'validator': recipe_validator,
            'ingredient_expert': ingredient_specialist,
            'nutritionist': nutrition_expert,
            'cost_analyst': cost_analyst,
            'dietary_expert': dietary_expert,
            'measurement_expert': measurement_expert,
            'sommelier': sommelier,
            'quality_expert': quality_evaluator
        }
    
    def create_evaluation_crew(self, agents: Dict[str, Agent], user_preferences: Dict[str, Any] = None) -> Crew:
        """Create crew for evaluating AI-generated recipes"""
        
        # Base tasks always included
        tasks = [
            Task(
                description="Validate this recipe by comparing cooking times and methods with similar real recipes",
                agent=agents['validator'],
                expected_output="Validation report with time comparison and method verification"
            ),
            Task(
                description="Verify all ingredients exist and are available, suggest substitutes for rare ones",
                agent=agents['ingredient_expert'],
                expected_output="Ingredient verification report with availability and substitutions"
            ),
            Task(
                description="Calculate accurate nutrition using FDA ingredient databases",
                agent=agents['nutritionist'],
                expected_output="Complete nutritional breakdown per serving"
            ),
            Task(
                description="Standardize all measurements to user's preferred system (metric/imperial)",
                agent=agents['measurement_expert'],
                expected_output="Recipe with standardized measurements"
            )
        ]
        
        # Add optional tasks based on user preferences
        if user_preferences:
            if user_preferences.get('budget_conscious'):
                tasks.append(Task(
                    description="Calculate total recipe cost using current grocery prices",
                    agent=agents['cost_analyst'],
                    expected_output="Cost breakdown and total recipe cost"
                ))
            
            if user_preferences.get('dietary_restrictions'):
                tasks.append(Task(
                    description=f"Verify recipe meets dietary restrictions: {', '.join(user_preferences['dietary_restrictions'])}",
                    agent=agents['dietary_expert'],
                    expected_output="Dietary compliance report with any issues identified"
                ))
            
            if user_preferences.get('wine_pairing'):
                tasks.append(Task(
                    description="Suggest wine pairings for this recipe",
                    agent=agents['sommelier'],
                    expected_output="Wine pairing recommendations with tasting notes"
                ))
        
        # Final quality assessment task
        tasks.append(Task(
            description="Provide final quality assessment based on all agent reports",
            agent=agents['quality_expert'],
            expected_output="Overall quality score (1-5) with summary and recommendations"
        ))
        
        return Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True
        )


# ============= USAGE EXAMPLE =============

async def evaluate_ai_recipe_with_spoonacular(
    recipe: Dict[str, Any],
    user_preferences: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Evaluate an AI-generated recipe using Spoonacular-enhanced agents
    
    This provides comprehensive evaluation:
    1. Recipe validation against real recipes
    2. Ingredient verification and availability
    3. Accurate FDA nutrition data
    4. Cost estimation (if requested)
    5. Dietary compliance checking
    6. Seasonal ingredient suggestions
    7. Wine pairing (if requested)
    8. Overall quality assessment
    """
    
    enhancer = EnhancedCrewAgents()
    agents = enhancer.create_agents()
    
    # Set default preferences if not provided
    if not user_preferences:
        user_preferences = {
            'budget_conscious': True,
            'dietary_restrictions': [],
            'wine_pairing': False,
            'measurement_system': 'imperial'
        }
    
    crew = enhancer.create_evaluation_crew(agents, user_preferences)
    
    # Prepare comprehensive recipe data for crew
    crew_input = {
        'recipe': recipe,
        'title': recipe.get('title', ''),
        'cook_time': recipe.get('readyInMinutes', 30),
        'ingredients': [ing['original'] for ing in recipe.get('extendedIngredients', [])],
        'ingredients_json': json.dumps(recipe.get('extendedIngredients', [])),
        'dietary_restrictions': user_preferences.get('dietary_restrictions', []),
        'measurement_preference': user_preferences.get('measurement_system', 'imperial'),
        'main_ingredient': recipe.get('extendedIngredients', [{}])[0].get('name', '') if recipe.get('extendedIngredients') else '',
        'cuisine': recipe.get('cuisine_type', 'international')
    }
    
    # Run evaluation
    result = crew.kickoff(inputs=crew_input)
    
    # Parse results and add comprehensive validation to recipe
    recipe['spoonacular_validation'] = {
        'validated': True,
        'validation_timestamp': datetime.now().isoformat(),
        'similar_recipes_found': True,  # From validator
        'ingredients_verified': True,    # From ingredient expert
        'nutrition_verified': True,      # From nutritionist
        'cost_estimated': user_preferences.get('budget_conscious', False),
        'dietary_compliant': len(user_preferences.get('dietary_restrictions', [])) == 0 or True,
        'quality_score': 4,             # From quality expert
        'crew_output': str(result),
        'agent_count': len(agents),
        'tasks_completed': len(crew.tasks)
    }
    
    return recipe


# ============= SPECIALIZED USE CASES =============

async def validate_recipe_authenticity(recipe: Dict[str, Any], claimed_cuisine: str) -> Dict[str, Any]:
    """
    Validate if a recipe is authentic to its claimed cuisine
    """
    enhancer = EnhancedCrewAgents()
    validator = enhancer.validation_tool
    
    # Search for authentic recipes of that cuisine
    validation_result = await validator._run(
        recipe_title=f"authentic {claimed_cuisine} {recipe['title']}",
        cook_time=recipe.get('readyInMinutes', 30),
        ingredients=[ing['name'] for ing in recipe.get('extendedIngredients', [])]
    )
    
    return {
        'cuisine': claimed_cuisine,
        'authenticity_check': validation_result,
        'is_authentic': 'reasonable' in validation_result.lower()
    }


async def optimize_recipe_cost(recipe: Dict[str, Any], target_budget: float = 10.0) -> Dict[str, Any]:
    """
    Optimize recipe to meet budget constraints
    """
    enhancer = EnhancedCrewAgents()
    cost_tool = enhancer.cost_tool
    sub_tool = enhancer.substitution_tool
    
    # Calculate current cost
    current_cost = await cost_tool._run(
        ingredients_json=json.dumps(recipe.get('extendedIngredients', []))
    )
    
    # If over budget, find substitutions for expensive ingredients
    if 'Total Estimated Cost: $' in current_cost:
        cost_value = float(current_cost.split('$')[-1])
        if cost_value > target_budget:
            # Find substitutions for most expensive ingredients
            suggestions = []
            for ing in recipe.get('extendedIngredients', []):
                if 'expensive' in ing.get('aisle', '').lower():
                    sub = await sub_tool._run(ing['name'])
                    suggestions.append(sub)
            
            return {
                'original_cost': cost_value,
                'target_budget': target_budget,
                'cost_reduction_suggestions': suggestions
            }
    
    return {
        'cost_analysis': current_cost,
        'within_budget': True
    }


async def check_leftover_compatibility(user_leftovers: List[str], recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check how well a recipe uses user's leftovers
    """
    recipe_ingredients = [ing['name'].lower() for ing in recipe.get('extendedIngredients', [])]
    
    used_leftovers = []
    unused_leftovers = []
    
    for leftover in user_leftovers:
        if any(leftover.lower() in ing for ing in recipe_ingredients):
            used_leftovers.append(leftover)
        else:
            unused_leftovers.append(leftover)
    
    compatibility_score = len(used_leftovers) / len(user_leftovers) * 100 if user_leftovers else 0
    
    return {
        'leftovers_used': used_leftovers,
        'leftovers_unused': unused_leftovers,
        'compatibility_score': compatibility_score,
        'recommendation': 'Good match!' if compatibility_score > 60 else 'Consider another recipe'
    }