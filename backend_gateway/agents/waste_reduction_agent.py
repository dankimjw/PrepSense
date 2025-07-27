"""
Waste Reduction Agent for CrewAI - Minimizes food waste through smart recommendations
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from crewai import Agent, Task
from langchain.tools import Tool
from backend_gateway.services.food_waste_service import get_food_waste_service
from backend_gateway.services.environmental_impact_service import get_environmental_impact_service

logger = logging.getLogger(__name__)


class WasteRiskAnalysisTool(Tool):
    """Tool for analyzing waste risk of pantry items"""
    
    def __init__(self):
        self.waste_service = get_food_waste_service()
        self.impact_service = get_environmental_impact_service()
        super().__init__(
            name="Waste Risk Analysis",
            description="Analyze waste risk for pantry items and suggest priorities",
            func=self._analyze
        )
    
    def _analyze(self, query: str) -> str:
        """Analyze waste risk based on query"""
        try:
            # Parse query - expecting pantry items in JSON format
            import json
            pantry_items = json.loads(query)
            
            # Prioritize by waste risk
            prioritized = self.waste_service.prioritize_pantry_by_waste_risk(pantry_items)
            
            # Format response
            result = "Waste Risk Analysis Results:\n\n"
            
            # High risk items
            high_risk = [item for item in prioritized if item['risk_category'] in ['very_high', 'high']]
            if high_risk:
                result += "🚨 HIGH RISK ITEMS (Use within 48 hours):\n"
                for item in high_risk[:5]:
                    result += f"- {item['product_name']}: {item['risk_score']:.0f}/100 risk\n"
                    result += f"  → {item['recommended_action']}\n"
                    result += f"  → Typical waste rate: {item['base_loss_rate']*100:.0f}%\n"
                result += "\n"
            
            # Summary statistics
            total_items = len(prioritized)
            avg_risk = sum(item['risk_score'] for item in prioritized) / total_items if total_items > 0 else 0
            
            result += f"Summary:\n"
            result += f"- Total items: {total_items}\n"
            result += f"- Average risk score: {avg_risk:.1f}/100\n"
            result += f"- Items needing immediate attention: {len(high_risk)}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in waste risk analysis: {str(e)}")
            return f"Error analyzing waste risk: {str(e)}"


class RecipeWastePrioritizationTool(Tool):
    """Tool for prioritizing recipes based on waste reduction potential"""
    
    def __init__(self):
        self.waste_service = get_food_waste_service()
        super().__init__(
            name="Recipe Waste Prioritization",
            description="Prioritize recipes that use high-waste-risk ingredients",
            func=self._prioritize
        )
    
    def _prioritize(self, query: str) -> str:
        """Prioritize recipes by waste reduction potential"""
        try:
            import json
            data = json.loads(query)
            high_risk_items = data.get('high_risk_items', [])
            recipes = data.get('available_recipes', [])
            
            # Get prioritized recipes
            prioritized = self.waste_service.suggest_waste_reduction_recipes(
                high_risk_items, recipes
            )
            
            result = "Recipe Prioritization for Waste Reduction:\n\n"
            
            # Top recommendations
            result += "🌟 TOP RECOMMENDATIONS (Use high-risk ingredients):\n"
            for recipe, score in prioritized[:3]:
                result += f"\n{recipe['title']}:\n"
                result += f"- Waste reduction score: {score:.0f}\n"
                result += f"- Uses: "
                
                # List which high-risk items it uses
                used_items = []
                for ing in recipe.get('ingredients', []):
                    for risk_item in high_risk_items:
                        if risk_item.lower() in ing.get('name', '').lower():
                            used_items.append(risk_item)
                
                result += ", ".join(set(used_items)) + "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error prioritizing recipes: {str(e)}")
            return f"Error in recipe prioritization: {str(e)}"


class WasteImpactCalculatorTool(Tool):
    """Tool for calculating economic and environmental impact of food waste"""
    
    def __init__(self):
        self.waste_service = get_food_waste_service()
        self.impact_service = get_environmental_impact_service()
        super().__init__(
            name="Waste Impact Calculator",
            description="Calculate economic and environmental impact of potential food waste",
            func=self._calculate
        )
    
    def _calculate(self, query: str) -> str:
        """Calculate waste impact for specified items"""
        try:
            import json
            items = json.loads(query)
            
            total_economic = 0
            total_co2_saved = 0
            result = "Waste Impact Analysis:\n\n"
            
            for item in items:
                food_name = item['name']
                quantity_kg = item.get('quantity_kg', 1.0)
                price_per_kg = item.get('price_per_kg', 5.0)  # Default $5/kg
                
                # Get waste data
                waste_data = self.waste_service.calculate_waste_impact(
                    food_name, quantity_kg, price_per_kg
                )
                
                # Get environmental data
                env_impact = self.impact_service.get_food_impact(food_name)
                
                result += f"{food_name.title()}:\n"
                result += f"- Potential waste: {waste_data['potential_waste_kg']} kg "
                result += f"({waste_data['waste_percentage']}% typical loss)\n"
                
                if 'economic_loss' in waste_data:
                    result += f"- Economic value at risk: ${waste_data['economic_loss']:.2f}\n"
                    total_economic += waste_data['economic_loss']
                
                if env_impact:
                    ghg = env_impact['environmental'].get('ghg_kg_co2e_per_kg', 0)
                    co2_saved = waste_data['potential_waste_kg'] * ghg
                    result += f"- CO₂ saved by preventing waste: {co2_saved:.1f} kg\n"
                    total_co2_saved += co2_saved
                
                result += "\n"
            
            # Totals
            result += f"TOTAL IMPACT:\n"
            result += f"- Economic value at risk: ${total_economic:.2f}\n"
            result += f"- CO₂ emissions preventable: {total_co2_saved:.1f} kg\n"
            result += f"- Equivalent to driving: {total_co2_saved * 2.5:.0f} miles\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating impact: {str(e)}")
            return f"Error in impact calculation: {str(e)}"


class SmartStorageTipsTool(Tool):
    """Tool for providing storage tips based on food type and waste rates"""
    
    def __init__(self):
        self.waste_service = get_food_waste_service()
        super().__init__(
            name="Smart Storage Tips",
            description="Provide storage tips to reduce waste for specific foods",
            func=self._provide_tips
        )
    
    def _provide_tips(self, food_name: str) -> str:
        """Provide storage tips for a specific food"""
        loss_rate = self.waste_service.get_loss_rate(food_name)
        
        # Storage tips database (simplified)
        storage_tips = {
            'high_waste': {
                'leafy_greens': "Store in crisper drawer with paper towel to absorb moisture",
                'berries': "Don't wash until ready to eat; store in original container",
                'herbs': "Trim stems and store like flowers in water",
                'avocados': "Store unripe at room temp, ripe in fridge",
            },
            'medium_waste': {
                'dairy': "Keep in coldest part of fridge (not door)",
                'bread': "Freeze half if you won't use within 3 days",
                'leftovers': "Label with date and use within 3-4 days",
            },
            'low_waste': {
                'grains': "Store in airtight containers in cool, dry place",
                'canned': "Check dates but most last years past 'best by'",
            }
        }
        
        result = f"Storage Tips for {food_name.title()}:\n"
        result += f"Typical waste rate: {loss_rate*100:.0f}%\n\n"
        
        # Provide category-specific tips
        if loss_rate > 0.20:
            category = 'high_waste'
            result += "⚠️ This is a HIGH-WASTE item. Extra care needed!\n"
        elif loss_rate > 0.10:
            category = 'medium_waste'
            result += "📋 This has MODERATE waste rates.\n"
        else:
            category = 'low_waste'
            result += "✅ This has LOW waste rates.\n"
        
        # Add specific tips (simplified logic)
        result += "\nBest practices:\n"
        result += "- Check daily if high-waste item\n"
        result += "- Use FIFO (First In, First Out) method\n"
        result += "- Consider freezing if you can't use in time\n"
        
        return result


class WasteReductionAgent(Agent):
    """Agent specialized in reducing household food waste"""
    
    def __init__(self):
        # Initialize tools
        self.tools = [
            WasteRiskAnalysisTool(),
            RecipeWastePrioritizationTool(),
            WasteImpactCalculatorTool(),
            SmartStorageTipsTool()
        ]
        
        # Initialize services
        self.waste_service = get_food_waste_service()
        self.impact_service = get_environmental_impact_service()
        
        # Define agent characteristics
        super().__init__(
            role="Food Waste Prevention Specialist",
            goal="Help families reduce food waste through smart planning, timely alerts, and practical tips",
            backstory="""You are an expert in food preservation and waste reduction with years of 
            experience helping households save money and reduce environmental impact. You understand 
            that food waste happens for many reasons - busy schedules, poor planning, confusion about 
            dates, and storage mistakes. You provide practical, non-judgmental advice that fits into 
            real family life. You're especially good at identifying which foods are most at risk and 
            suggesting creative ways to use them before they spoil.""",
            tools=self.tools,
            verbose=True,
            allow_delegation=True
        )
    
    def create_weekly_waste_prevention_plan(self, pantry_data: Dict) -> Dict[str, Any]:
        """Create a weekly plan to minimize waste"""
        
        # Analyze current pantry
        pantry_items = pantry_data.get('items', [])
        prioritized = self.waste_service.prioritize_pantry_by_waste_risk(pantry_items)
        
        # Categorize by urgency
        immediate = []  # Use today
        very_soon = []  # Use in 1-2 days
        this_week = []  # Use within week
        monitor = []    # Just monitor
        
        for item in prioritized:
            if item['risk_category'] == 'very_high':
                immediate.append(item)
            elif item['risk_category'] == 'high':
                very_soon.append(item)
            elif item['risk_category'] == 'medium':
                this_week.append(item)
            else:
                monitor.append(item)
        
        # Create action plan
        plan = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'items_at_risk': len(immediate) + len(very_soon),
                'potential_savings': self._calculate_total_savings(immediate + very_soon),
                'priority_level': 'urgent' if immediate else 'normal'
            },
            'immediate_actions': [
                {
                    'item': item['product_name'],
                    'action': item['recommended_action'],
                    'quantity': item.get('quantity', 'Unknown'),
                    'reason': f"{item['risk_score']:.0f}% waste risk"
                }
                for item in immediate[:3]  # Top 3 most urgent
            ],
            'meal_suggestions': self._generate_meal_suggestions(immediate + very_soon),
            'storage_improvements': self._suggest_storage_improvements(prioritized),
            'weekly_checkpoints': [
                'Monday: Check all produce',
                'Wednesday: Review dairy dates',
                'Friday: Plan weekend meals using oldest items',
                'Sunday: Prep and freeze anything not used'
            ]
        }
        
        return plan
    
    def _calculate_total_savings(self, items: List[Dict]) -> Dict[str, float]:
        """Calculate potential savings from preventing waste"""
        total_economic = 0
        total_environmental = 0
        
        for item in items:
            # Estimate economic value (simplified)
            quantity = item.get('quantity', 1)
            price_estimate = 5.0  # $5/unit average
            economic = quantity * price_estimate * item.get('adjusted_loss_rate', 0.1)
            total_economic += economic
            
            # Environmental impact
            env_data = self.impact_service.get_food_impact(item['product_name'])
            if env_data:
                ghg = env_data['environmental'].get('ghg_kg_co2e_per_kg', 0)
                environmental = quantity * 0.5 * ghg  # Assume 0.5kg average weight
                total_environmental += environmental
        
        return {
            'economic_usd': round(total_economic, 2),
            'environmental_kg_co2': round(total_environmental, 2)
        }
    
    def _generate_meal_suggestions(self, high_risk_items: List[Dict]) -> List[str]:
        """Generate meal ideas using high-risk items"""
        suggestions = []
        
        # Simple meal matching (in production, would use recipe database)
        meal_templates = {
            'vegetables': ['stir-fry', 'soup', 'roasted veggie bowl', 'frittata'],
            'fruits': ['smoothie', 'fruit salad', 'baked goods', 'compote'],
            'dairy': ['quiche', 'cheese sauce', 'smoothie', 'baked pasta'],
            'proteins': ['meal prep bowls', 'casserole', 'tacos', 'fried rice']
        }
        
        for item in high_risk_items[:5]:  # Top 5 items
            food_type = self._categorize_food_type(item['product_name'])
            if food_type in meal_templates:
                meal = f"{meal_templates[food_type][0]} using {item['product_name']}"
                suggestions.append(meal)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _categorize_food_type(self, food_name: str) -> str:
        """Simple food categorization"""
        food_lower = food_name.lower()
        if any(veg in food_lower for veg in ['carrot', 'broccoli', 'spinach', 'tomato']):
            return 'vegetables'
        elif any(fruit in food_lower for fruit in ['apple', 'banana', 'berry']):
            return 'fruits'
        elif any(dairy in food_lower for dairy in ['milk', 'cheese', 'yogurt']):
            return 'dairy'
        elif any(protein in food_lower for protein in ['chicken', 'beef', 'fish', 'egg']):
            return 'proteins'
        return 'other'
    
    def _suggest_storage_improvements(self, items: List[Dict]) -> List[str]:
        """Suggest storage improvements based on waste patterns"""
        suggestions = []
        
        # Analyze patterns
        high_waste_items = [i for i in items if i.get('base_loss_rate', 0) > 0.20]
        
        if any('produce' in str(i.get('product_name', '')).lower() for i in high_waste_items):
            suggestions.append("Consider produce storage containers with humidity control")
        
        if len(high_waste_items) > 5:
            suggestions.append("Implement a 'use first' shelf in your fridge")
        
        suggestions.append("Label items with 'use by' dates when storing")
        
        return suggestions[:3]


def create_waste_reduction_agent() -> WasteReductionAgent:
    """Factory function to create a Waste Reduction agent"""
    return WasteReductionAgent()


# Example tasks for the Waste Reduction Agent
def create_waste_reduction_tasks(user_context: Dict) -> List[Task]:
    """Create tasks for waste reduction analysis"""
    
    agent = create_waste_reduction_agent()
    tasks = []
    
    # Task 1: Analyze pantry waste risk
    pantry_analysis_task = Task(
        description=f"""Analyze the waste risk for the user's pantry items.
        Pantry data: {user_context.get('pantry_items', [])}
        
        Provide:
        1. Items at highest risk of being wasted
        2. Economic and environmental impact of potential waste
        3. Specific actions to take today
        4. Storage tips for high-risk items
        """,
        agent=agent,
        expected_output="A comprehensive waste risk analysis with actionable recommendations"
    )
    tasks.append(pantry_analysis_task)
    
    # Task 2: Create waste-prevention meal plan
    if user_context.get('request_meal_plan'):
        meal_plan_task = Task(
            description=f"""Create a meal plan that prioritizes using high-waste-risk items.
            Focus on:
            1. Using items expiring in next 3 days first
            2. Creative ways to use items with high waste rates
            3. Batch cooking suggestions for items that can be frozen
            4. Shopping list that avoids creating more waste
            
            Family size: {user_context.get('family_size', 4)}
            Dietary restrictions: {user_context.get('dietary_restrictions', [])}
            """,
            agent=agent,
            expected_output="A waste-conscious meal plan for the week"
        )
        tasks.append(meal_plan_task)
    
    return tasks