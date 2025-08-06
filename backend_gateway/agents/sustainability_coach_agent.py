"""Sustainability Coach Agent for CrewAI - Environmental impact advisor"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Task
from langchain.tools import Tool

from backend_gateway.services.environmental_impact_service import get_environmental_impact_service

logger = logging.getLogger(__name__)


class SustainabilityAnalysisTool(Tool):
    """Tool for analyzing environmental impact of foods and recipes"""

    def __init__(self):
        self.impact_service = get_environmental_impact_service()
        super().__init__(
            name="Sustainability Analysis",
            description="Analyze environmental impact of ingredients and recipes",
            func=self._analyze,
        )

    def _analyze(self, query: str) -> str:
        """Analyze environmental impact based on query"""
        try:
            # Parse query to determine analysis type
            if "recipe:" in query.lower():
                # Analyze recipe impact
                recipe_name = query.split("recipe:")[-1].strip()
                return self._analyze_recipe(recipe_name)
            elif "ingredient:" in query.lower():
                # Analyze single ingredient
                ingredient = query.split("ingredient:")[-1].strip()
                return self._analyze_ingredient(ingredient)
            else:
                return "Please specify 'recipe:' or 'ingredient:' followed by the item to analyze"

        except Exception as e:
            logger.error(f"Error in sustainability analysis: {str(e)}")
            return f"Error analyzing impact: {str(e)}"

    def _analyze_ingredient(self, ingredient: str) -> str:
        """Analyze environmental impact of a single ingredient"""
        impact = self.impact_service.get_food_impact(ingredient)

        if not impact:
            return f"No environmental data available for {ingredient}"

        env = impact["environmental"]
        profile = impact["sustainability_profile"]

        result = f"Environmental Impact of {ingredient}:\n"
        result += f"- GHG Emissions: {env.get('ghg_kg_co2e_per_kg', 'N/A')} kg CO₂e per kg\n"
        result += f"- Land Use: {env.get('land_m2_per_kg', 'N/A')} m² per kg\n"
        result += f"- Water Use: {env.get('water_L_per_kg', 'N/A')} L per kg\n"
        result += f"- Impact Category: {profile['impact_category']} {profile['ghg_visual']}\n"
        result += f"- Planet Score: {profile['planet_score']}/10\n"

        # Add supply chain breakdown if available
        if env.get("supply_chain_breakdown"):
            result += "\nSupply Chain Breakdown:\n"
            for stage, percentage in env["supply_chain_breakdown"].items():
                if percentage > 0:
                    result += f"  - {stage.title()}: {percentage*100:.1f}%\n"

        return result

    def _analyze_recipe(self, recipe_info: str) -> str:
        """Analyze environmental impact of a recipe"""
        # For now, return a placeholder - this would integrate with recipe service
        return f"Recipe impact analysis for '{recipe_info}' - Feature coming soon!"


class SwapSuggestionTool(Tool):
    """Tool for suggesting sustainable ingredient swaps"""

    def __init__(self):
        self.impact_service = get_environmental_impact_service()
        super().__init__(
            name="Sustainable Swap Suggestions",
            description="Suggest lower-impact alternatives for ingredients",
            func=self._suggest_swaps,
        )

    def _suggest_swaps(self, ingredient: str) -> str:
        """Suggest sustainable swaps for an ingredient"""
        try:
            swaps = self.impact_service.suggest_sustainable_swaps(ingredient)

            if not swaps:
                return f"No lower-impact alternatives found for {ingredient}"

            result = f"Sustainable alternatives to {ingredient}:\n\n"

            for i, swap in enumerate(swaps, 1):
                result += f"{i}. {swap['ingredient'].title()}\n"
                result += f"   - CO₂ Savings: {swap['co2_savings_per_kg']} kg per kg ({swap['percentage_reduction']}% reduction)\n"
                result += f"   - Planet Score: {swap['planet_score']}/10\n"
                result += f"   - Impact Level: {swap['impact_category']}\n\n"

            return result

        except Exception as e:
            logger.error(f"Error suggesting swaps: {str(e)}")
            return f"Error finding alternatives: {str(e)}"


class ImpactComparisonTool(Tool):
    """Tool for comparing environmental impact between foods"""

    def __init__(self):
        self.impact_service = get_environmental_impact_service()
        super().__init__(
            name="Impact Comparison",
            description="Compare environmental impact between different foods",
            func=self._compare,
        )

    def _compare(self, query: str) -> str:
        """Compare environmental impact between foods"""
        try:
            # Parse query expecting format: "food1 vs food2"
            if " vs " not in query.lower():
                return "Please format as: 'food1 vs food2' (e.g., 'beef vs lentils')"

            foods = [f.strip() for f in query.lower().split(" vs ")]
            if len(foods) != 2:
                return "Please compare exactly two foods"

            # Get impact data for both foods
            impacts = []
            for food in foods:
                impact = self.impact_service.get_food_impact(food)
                if impact:
                    impacts.append((food, impact))
                else:
                    return f"No environmental data available for {food}"

            # Compare impacts
            result = (
                f"Environmental Impact Comparison: {foods[0].title()} vs {foods[1].title()}\n\n"
            )

            # Compare GHG emissions
            ghg1 = impacts[0][1]["environmental"].get("ghg_kg_co2e_per_kg", 0)
            ghg2 = impacts[1][1]["environmental"].get("ghg_kg_co2e_per_kg", 0)

            if ghg1 and ghg2:
                ratio = ghg1 / ghg2 if ghg2 > 0 else float("inf")
                result += f"GHG Emissions:\n"
                result += f"- {foods[0].title()}: {ghg1} kg CO₂e/kg\n"
                result += f"- {foods[1].title()}: {ghg2} kg CO₂e/kg\n"

                if ratio > 1:
                    result += f"→ {foods[0].title()} has {ratio:.1f}x higher emissions\n\n"
                else:
                    result += f"→ {foods[1].title()} has {1/ratio:.1f}x higher emissions\n\n"

            # Compare other metrics
            for metric, unit in [("land_m2_per_kg", "m²"), ("water_L_per_kg", "L")]:
                val1 = impacts[0][1]["environmental"].get(metric, 0)
                val2 = impacts[1][1]["environmental"].get(metric, 0)

                if val1 and val2:
                    metric_name = metric.replace("_per_kg", "").replace("_", " ").title()
                    result += f"{metric_name}:\n"
                    result += f"- {foods[0].title()}: {val1} {unit}/kg\n"
                    result += f"- {foods[1].title()}: {val2} {unit}/kg\n\n"

            # Add planet scores
            score1 = impacts[0][1]["sustainability_profile"]["planet_score"]
            score2 = impacts[1][1]["sustainability_profile"]["planet_score"]
            result += f"Planet Scores:\n"
            result += f"- {foods[0].title()}: {score1}/10\n"
            result += f"- {foods[1].title()}: {score2}/10\n"

            return result

        except Exception as e:
            logger.error(f"Error comparing foods: {str(e)}")
            return f"Error comparing foods: {str(e)}"


class SustainabilityCoachAgent(Agent):
    """Agent specialized in environmental impact and sustainability advice"""

    def __init__(self):
        # Initialize tools
        self.tools = [SustainabilityAnalysisTool(), SwapSuggestionTool(), ImpactComparisonTool()]

        # Initialize the impact service
        self.impact_service = get_environmental_impact_service()

        # Define agent characteristics
        super().__init__(
            role="Environmental Impact Advisor",
            goal="Help families reduce their food's environmental impact while maintaining nutrition, taste, and budget",
            backstory="""You are a passionate sustainability expert with deep knowledge of food systems 
            and environmental science. You understand that sustainable eating isn't just about the planet - 
            it's also about health, budget, and family preferences. You excel at finding win-win solutions 
            that benefit both people and the planet. You present information in a friendly, non-judgmental 
            way that empowers families to make better choices without feeling guilty.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=True,
        )

    def analyze_pantry_sustainability(self, pantry_items: List[Dict]) -> Dict[str, Any]:
        """Analyze the environmental impact of a user's pantry"""
        total_impact = {
            "total_ghg": 0,
            "total_land": 0,
            "total_water": 0,
            "high_impact_items": [],
            "low_impact_items": [],
            "swap_opportunities": [],
        }

        for item in pantry_items:
            food_name = item.get("product_name", "")
            quantity_kg = item.get("quantity", 0) * 0.453592  # Convert lbs to kg if needed

            impact = self.impact_service.get_food_impact(food_name)
            if impact:
                env = impact["environmental"]
                ghg = env.get("ghg_kg_co2e_per_kg", 0) * quantity_kg

                total_impact["total_ghg"] += ghg

                # Categorize items
                if impact["sustainability_profile"]["impact_category"] in ["high", "very_high"]:
                    total_impact["high_impact_items"].append(
                        {
                            "name": food_name,
                            "ghg": ghg,
                            "category": impact["sustainability_profile"]["impact_category"],
                        }
                    )

                    # Get swap suggestions
                    swaps = self.impact_service.suggest_sustainable_swaps(food_name)
                    if swaps:
                        total_impact["swap_opportunities"].append(
                            {"item": food_name, "swaps": swaps[:2]}  # Top 2 suggestions
                        )

                elif impact["sustainability_profile"]["impact_category"] in ["low", "very_low"]:
                    total_impact["low_impact_items"].append(food_name)

        return total_impact

    def create_sustainability_report(self, analysis: Dict) -> str:
        """Create a friendly sustainability report"""
        report = "🌍 Your Pantry Sustainability Report\n\n"

        # Overall impact
        total_ghg = analysis["total_ghg"]
        driving_miles = total_ghg * 2.5

        report += f"Total Environmental Impact:\n"
        report += f"• Carbon footprint: {total_ghg:.1f} kg CO₂e\n"
        report += f"• Equivalent to driving: {driving_miles:.0f} miles\n\n"

        # Highlight positives first
        if analysis["low_impact_items"]:
            report += "🌱 Great Choices:\n"
            for item in analysis["low_impact_items"][:5]:
                report += f"• {item.title()}\n"
            report += "\n"

        # Improvement opportunities
        if analysis["swap_opportunities"]:
            report += "💡 Easy Wins for the Planet:\n"
            for opp in analysis["swap_opportunities"][:3]:
                swap = opp["swaps"][0]
                report += f"• Swap {opp['item']} → {swap['ingredient']}\n"
                report += f"  (Save {swap['co2_savings_per_kg']:.1f} kg CO₂e per kg)\n"
            report += "\n"

        # Positive messaging
        report += (
            "Remember: Every small change adds up! Even one swap per week makes a difference.\n"
        )

        return report


def create_sustainability_coach_agent() -> SustainabilityCoachAgent:
    """Factory function to create a Sustainability Coach agent"""
    return SustainabilityCoachAgent()


# Example tasks for the Sustainability Coach
def create_sustainability_tasks(user_context: Dict) -> List[Task]:
    """Create tasks for sustainability analysis"""

    coach = create_sustainability_coach_agent()

    tasks = []

    # Task 1: Analyze current pantry impact
    pantry_analysis_task = Task(
        description=f"""Analyze the environmental impact of the user's pantry items.
        Pantry items: {user_context.get('pantry_items', [])}
        
        Provide:
        1. Total carbon footprint
        2. Identification of high-impact items
        3. Specific swap suggestions with CO2 savings
        4. Positive reinforcement for low-impact choices
        """,
        agent=coach,
        expected_output="A comprehensive but friendly sustainability analysis",
    )
    tasks.append(pantry_analysis_task)

    # Task 2: Create sustainable meal plan
    if user_context.get("request_meal_plan"):
        meal_plan_task = Task(
            description=f"""Create a sustainable meal plan that:
            1. Uses mostly low-impact ingredients
            2. Includes 1-2 familiar high-impact items as treats
            3. Balances nutrition, taste, and environmental impact
            4. Provides specific CO2 savings compared to typical meals
            
            Dietary restrictions: {user_context.get('dietary_restrictions', [])}
            Family size: {user_context.get('family_size', 4)}
            """,
            agent=coach,
            expected_output="A week-long sustainable meal plan with impact metrics",
        )
        tasks.append(meal_plan_task)

    return tasks
