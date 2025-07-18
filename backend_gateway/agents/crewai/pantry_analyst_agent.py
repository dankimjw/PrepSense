"""PantryAnalyst Agent for analyzing pantry items and identifying key insights."""

from typing import Dict, List, Any, Optional
import logging
from crewai import Agent
from langchain_openai import ChatOpenAI

from backend_gateway.tools.pantry_tool import create_pantry_tool
from backend_gateway.tools.database_tool import create_database_tool
from backend_gateway.core.config_utils import get_openai_api_key

logger = logging.getLogger(__name__)


class PantryAnalystAgent:
    """Agent specialized in analyzing pantry items and providing insights."""
    
    def __init__(self):
        """Initialize the PantryAnalyst agent."""
        self.pantry_tool = create_pantry_tool()
        self.database_tool = create_database_tool()
        
        # Initialize OpenAI LLM
        api_key = get_openai_api_key()
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0.3)
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Pantry Analyst",
            goal="Analyze pantry items to identify expiring ingredients, categorize items, and provide insights for recipe planning",
            backstory=(
                "You are a meticulous pantry analyst with expertise in food storage, "
                "ingredient categorization, and meal planning. You excel at identifying "
                "patterns in pantry items, highlighting expiring ingredients, and providing "
                "actionable insights for efficient meal preparation. Your analysis helps "
                "users make the most of their available ingredients while minimizing food waste."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_pantry(self, user_id: int, focus_area: str = "general") -> Dict[str, Any]:
        """
        Analyze user's pantry based on focus area.
        
        Args:
            user_id: The user's ID
            focus_area: Focus area for analysis (general, expiring, categories, proteins, etc.)
            
        Returns:
            Dict containing pantry analysis results
        """
        try:
            logger.info(f"PantryAnalyst analyzing pantry for user {user_id}, focus: {focus_area}")
            
            if focus_area == "expiring":
                return self._analyze_expiring_items(user_id)
            elif focus_area == "categories":
                return self._analyze_categories(user_id)
            elif focus_area == "proteins":
                return self._analyze_proteins(user_id)
            elif focus_area == "staples":
                return self._analyze_staples(user_id)
            elif focus_area == "available":
                return self._analyze_available_ingredients(user_id)
            else:
                return self._analyze_comprehensive(user_id)
                
        except Exception as e:
            logger.error(f"PantryAnalyst error: {str(e)}")
            return {"error": f"Pantry analysis failed: {str(e)}"}
    
    def _analyze_expiring_items(self, user_id: int) -> Dict[str, Any]:
        """Focus on expiring items analysis."""
        expiring_result = self.pantry_tool._run("expiring", user_id, days=7)
        
        if "error" in expiring_result:
            return expiring_result
        
        expiring_items = expiring_result.get("expiring_items", [])
        
        analysis = {
            "focus_area": "expiring",
            "user_id": user_id,
            "expiring_items": expiring_items,
            "count": len(expiring_items),
            "urgency_levels": self._categorize_by_urgency(expiring_items),
            "recommendations": self._generate_expiring_recommendations(expiring_items)
        }
        
        return analysis
    
    def _analyze_categories(self, user_id: int) -> Dict[str, Any]:
        """Focus on ingredient categories analysis."""
        categories_result = self.pantry_tool._run("categories", user_id)
        
        if "error" in categories_result:
            return categories_result
        
        categories = categories_result.get("categories", {})
        category_counts = categories_result.get("category_counts", {})
        
        analysis = {
            "focus_area": "categories",
            "user_id": user_id,
            "categories": categories,
            "category_counts": category_counts,
            "dominant_categories": self._identify_dominant_categories(category_counts),
            "meal_suggestions": self._suggest_meals_by_category(categories)
        }
        
        return analysis
    
    def _analyze_proteins(self, user_id: int) -> Dict[str, Any]:
        """Focus on protein sources analysis."""
        proteins_result = self.pantry_tool._run("proteins", user_id)
        
        if "error" in proteins_result:
            return proteins_result
        
        proteins = proteins_result.get("protein_sources", [])
        
        analysis = {
            "focus_area": "proteins",
            "user_id": user_id,
            "protein_sources": proteins,
            "count": len(proteins),
            "protein_types": self._categorize_protein_types(proteins),
            "meal_planning": self._suggest_protein_meals(proteins)
        }
        
        return analysis
    
    def _analyze_staples(self, user_id: int) -> Dict[str, Any]:
        """Focus on staple items analysis."""
        staples_result = self.pantry_tool._run("staples", user_id)
        
        if "error" in staples_result:
            return staples_result
        
        staples = staples_result.get("staple_items", [])
        
        analysis = {
            "focus_area": "staples",
            "user_id": user_id,
            "staple_items": staples,
            "count": len(staples),
            "staple_types": self._categorize_staple_types(staples),
            "base_recipes": self._suggest_staple_based_recipes(staples)
        }
        
        return analysis
    
    def _analyze_available_ingredients(self, user_id: int) -> Dict[str, Any]:
        """Focus on all available ingredients analysis."""
        available_result = self.pantry_tool._run("available_ingredients", user_id)
        
        if "error" in available_result:
            return available_result
        
        ingredients = available_result.get("available_ingredients", [])
        ingredient_names = available_result.get("ingredient_names", [])
        
        analysis = {
            "focus_area": "available",
            "user_id": user_id,
            "available_ingredients": ingredients,
            "ingredient_names": ingredient_names,
            "count": len(ingredients),
            "recipe_potential": self._assess_recipe_potential(ingredients),
            "cooking_strategies": self._suggest_cooking_strategies(ingredients)
        }
        
        return analysis
    
    def _analyze_comprehensive(self, user_id: int) -> Dict[str, Any]:
        """Comprehensive pantry analysis."""
        comprehensive_result = self.pantry_tool._run("analyze", user_id)
        
        if "error" in comprehensive_result:
            return comprehensive_result
        
        analysis = {
            "focus_area": "comprehensive",
            "user_id": user_id,
            "pantry_overview": comprehensive_result,
            "key_insights": self._extract_key_insights(comprehensive_result),
            "action_items": self._generate_action_items(comprehensive_result),
            "meal_planning_advice": self._generate_meal_planning_advice(comprehensive_result)
        }
        
        return analysis
    
    def _categorize_by_urgency(self, expiring_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize expiring items by urgency."""
        urgency_levels = {
            "immediate": [],  # 0-1 days
            "urgent": [],     # 2-3 days
            "soon": []        # 4-7 days
        }
        
        for item in expiring_items:
            days = item.get("days", 0)
            if days <= 1:
                urgency_levels["immediate"].append(item)
            elif days <= 3:
                urgency_levels["urgent"].append(item)
            else:
                urgency_levels["soon"].append(item)
        
        return urgency_levels
    
    def _generate_expiring_recommendations(self, expiring_items: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for expiring items."""
        recommendations = []
        
        if not expiring_items:
            return ["No items expiring soon - great pantry management!"]
        
        # Immediate items
        immediate_items = [item for item in expiring_items if item.get("days", 0) <= 1]
        if immediate_items:
            item_names = [item["name"] for item in immediate_items]
            recommendations.append(f"Use immediately: {', '.join(item_names)}")
        
        # Urgent items
        urgent_items = [item for item in expiring_items if 2 <= item.get("days", 0) <= 3]
        if urgent_items:
            item_names = [item["name"] for item in urgent_items]
            recommendations.append(f"Use within 2-3 days: {', '.join(item_names)}")
        
        # General advice
        if len(expiring_items) > 3:
            recommendations.append("Consider meal prep to use multiple expiring items efficiently")
        
        return recommendations
    
    def _identify_dominant_categories(self, category_counts: Dict[str, int]) -> List[Dict[str, Any]]:
        """Identify dominant ingredient categories."""
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        dominant = []
        for category, count in sorted_categories[:3]:  # Top 3 categories
            dominant.append({
                "category": category,
                "count": count,
                "percentage": round((count / sum(category_counts.values())) * 100, 1) if category_counts else 0
            })
        
        return dominant
    
    def _suggest_meals_by_category(self, categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Suggest meals based on available categories."""
        suggestions = {}
        
        if "proteins" in categories or "meat" in categories:
            suggestions["protein_based"] = [
                "Grilled protein with sides",
                "Protein stir-fry",
                "Protein salad bowls"
            ]
        
        if "vegetables" in categories or "produce" in categories:
            suggestions["vegetable_focused"] = [
                "Roasted vegetable medley",
                "Fresh salads",
                "Vegetable soups"
            ]
        
        if "grains" in categories or "pantry" in categories:
            suggestions["grain_based"] = [
                "Grain bowls",
                "Pasta dishes",
                "Rice-based meals"
            ]
        
        return suggestions
    
    def _categorize_protein_types(self, proteins: List[str]) -> Dict[str, List[str]]:
        """Categorize protein types."""
        protein_types = {
            "meat": [],
            "poultry": [],
            "seafood": [],
            "plant_based": [],
            "dairy": []
        }
        
        for protein in proteins:
            protein_lower = protein.lower()
            
            if any(meat in protein_lower for meat in ["beef", "pork", "lamb"]):
                protein_types["meat"].append(protein)
            elif any(poultry in protein_lower for poultry in ["chicken", "turkey"]):
                protein_types["poultry"].append(protein)
            elif any(seafood in protein_lower for seafood in ["fish", "salmon", "tuna", "shrimp"]):
                protein_types["seafood"].append(protein)
            elif any(plant in protein_lower for plant in ["beans", "tofu", "tempeh", "lentils"]):
                protein_types["plant_based"].append(protein)
            elif any(dairy in protein_lower for dairy in ["cheese", "yogurt", "milk"]):
                protein_types["dairy"].append(protein)
        
        # Remove empty categories
        return {k: v for k, v in protein_types.items() if v}
    
    def _suggest_protein_meals(self, proteins: List[str]) -> List[str]:
        """Suggest meals based on available proteins."""
        suggestions = []
        
        if any("chicken" in p.lower() for p in proteins):
            suggestions.extend(["Chicken stir-fry", "Grilled chicken salad", "Chicken soup"])
        
        if any("fish" in p.lower() or "salmon" in p.lower() for p in proteins):
            suggestions.extend(["Baked fish with vegetables", "Fish tacos", "Salmon pasta"])
        
        if any("beef" in p.lower() for p in proteins):
            suggestions.extend(["Beef stir-fry", "Beef and vegetable stew", "Beef tacos"])
        
        if any("tofu" in p.lower() or "beans" in p.lower() for p in proteins):
            suggestions.extend(["Tofu scramble", "Bean chili", "Protein-packed salad"])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _categorize_staple_types(self, staples: List[str]) -> Dict[str, List[str]]:
        """Categorize staple types."""
        staple_types = {
            "grains": [],
            "carbs": [],
            "basics": []
        }
        
        for staple in staples:
            staple_lower = staple.lower()
            
            if any(grain in staple_lower for grain in ["rice", "quinoa", "oats"]):
                staple_types["grains"].append(staple)
            elif any(carb in staple_lower for carb in ["pasta", "bread", "potato"]):
                staple_types["carbs"].append(staple)
            else:
                staple_types["basics"].append(staple)
        
        return {k: v for k, v in staple_types.items() if v}
    
    def _suggest_staple_based_recipes(self, staples: List[str]) -> List[str]:
        """Suggest recipes based on available staples."""
        suggestions = []
        
        if any("rice" in s.lower() for s in staples):
            suggestions.extend(["Rice bowls", "Fried rice", "Rice pilaf"])
        
        if any("pasta" in s.lower() for s in staples):
            suggestions.extend(["Pasta primavera", "Spaghetti with sauce", "Pasta salad"])
        
        if any("potato" in s.lower() for s in staples):
            suggestions.extend(["Roasted potatoes", "Potato salad", "Mashed potatoes"])
        
        return suggestions[:5]
    
    def _assess_recipe_potential(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess recipe making potential."""
        ingredient_count = len(ingredients)
        
        # Simple scoring based on ingredient count and variety
        if ingredient_count >= 15:
            potential = "High"
            description = "Excellent variety for multiple recipe options"
        elif ingredient_count >= 10:
            potential = "Medium"
            description = "Good selection for several recipes"
        elif ingredient_count >= 5:
            potential = "Low"
            description = "Limited ingredients, consider simple recipes"
        else:
            potential = "Very Low"
            description = "Very few ingredients available"
        
        return {
            "level": potential,
            "description": description,
            "ingredient_count": ingredient_count,
            "suggestions": self._get_potential_suggestions(potential)
        }
    
    def _suggest_cooking_strategies(self, ingredients: List[Dict[str, Any]]) -> List[str]:
        """Suggest cooking strategies based on available ingredients."""
        strategies = []
        
        ingredient_count = len(ingredients)
        
        if ingredient_count >= 10:
            strategies.append("Consider meal prep for the week")
            strategies.append("Try complex recipes with multiple components")
        elif ingredient_count >= 5:
            strategies.append("Focus on one-pot meals")
            strategies.append("Combine ingredients creatively")
        else:
            strategies.append("Keep it simple with basic recipes")
            strategies.append("Consider grocery shopping for more options")
        
        return strategies
    
    def _get_potential_suggestions(self, potential: str) -> List[str]:
        """Get suggestions based on recipe potential."""
        suggestions = {
            "High": ["Try complex recipes", "Experiment with new cuisines", "Consider meal prep"],
            "Medium": ["Focus on balanced meals", "Try one-pot dishes", "Mix and match ingredients"],
            "Low": ["Stick to simple recipes", "Consider ingredient substitutions", "Plan grocery shopping"],
            "Very Low": ["Make simple snacks", "Plan a grocery trip", "Use what you have creatively"]
        }
        
        return suggestions.get(potential, ["Assess your pantry and plan accordingly"])
    
    def _extract_key_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract key insights from comprehensive analysis."""
        insights = []
        
        total_items = analysis.get("total_items", 0)
        expiring_count = len(analysis.get("expiring_soon", []))
        categories_count = len(analysis.get("categories", {}))
        proteins_count = len(analysis.get("protein_sources", []))
        
        insights.append(f"You have {total_items} total items in your pantry")
        
        if expiring_count > 0:
            insights.append(f"{expiring_count} items are expiring soon - prioritize these")
        
        if categories_count > 0:
            insights.append(f"Your pantry spans {categories_count} different categories")
        
        if proteins_count > 0:
            insights.append(f"You have {proteins_count} protein sources available")
        
        return insights
    
    def _generate_action_items(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate action items from analysis."""
        actions = []
        
        expiring_items = analysis.get("expiring_soon", [])
        if expiring_items:
            actions.append(f"Use {len(expiring_items)} expiring items within the next week")
        
        if analysis.get("protein_sources"):
            actions.append("Plan protein-centered meals this week")
        
        if analysis.get("staples"):
            actions.append("Use staple items as base for multiple meals")
        
        if analysis.get("categories"):
            actions.append("Create balanced meals using items from different categories")
        
        return actions
    
    def _generate_meal_planning_advice(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate meal planning advice."""
        advice = []
        
        total_items = analysis.get("total_items", 0)
        
        if total_items >= 20:
            advice.append("You have plenty of ingredients for diverse meal planning")
        elif total_items >= 10:
            advice.append("Good ingredient variety for several days of meals")
        else:
            advice.append("Consider grocery shopping to expand meal options")
        
        if analysis.get("expiring_soon"):
            advice.append("Prioritize expiring items in this week's meal plan")
        
        if analysis.get("protein_sources") and analysis.get("staples"):
            advice.append("You have good protein and carb options for balanced meals")
        
        return advice


def create_pantry_analyst_agent() -> PantryAnalystAgent:
    """Create and return a PantryAnalystAgent instance."""
    return PantryAnalystAgent()