"""
Comprehensive CrewAI Monitoring Integration Example

This module demonstrates how to integrate all monitoring components:
- Enhanced agent monitoring with retry and circuit breaker
- Tool usage tracking and performance monitoring
- Decision point tracking for debugging
- Error handling and categorization
- Performance analytics and recommendations

This serves as both documentation and reference implementation.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional

from backend_gateway.core.crewai_observability import (
    AgentType,
    RetryConfig,
    observability_manager
)
from backend_gateway.crewai.agent_monitoring import (
    monitor_nutri_check,
    create_agent_context,
    track_agent_decision,
    create_tool_tracker,
    get_agent_performance_summary
)
from backend_gateway.crewai.tools.enhanced_nutrition_calculator_tool import (
    EnhancedNutritionCalculatorTool
)
from backend_gateway.core.logging_config import get_logger

logger = get_logger("crewai.monitoring_example")


# Example 1: Enhanced Agent Function with Comprehensive Monitoring
@monitor_nutri_check("comprehensive_nutrition_analysis")
async def enhanced_nutrition_analysis(
    ingredients: List[Dict[str, Any]],
    user_id: str,
    dietary_preferences: Optional[List[str]] = None,
    analysis_depth: str = "standard"
) -> Dict[str, Any]:
    """
    Example of a comprehensive nutrition analysis function with full monitoring integration.
    
    This demonstrates:
    - Automatic retry logic with exponential backoff
    - Circuit breaker protection
    - Performance tracking
    - Decision point logging
    - Error categorization
    - PII-safe logging
    """
    
    # Simulate some processing time for demonstration
    await asyncio.sleep(0.1)
    
    try:
        # Initialize nutrition calculator tool
        nutrition_tool = EnhancedNutritionCalculatorTool()
        
        # Call the tool with monitoring
        nutrition_result = nutrition_tool._run_with_monitoring(
            ingredients=ingredients,
            user_id=user_id,
            dietary_restrictions=dietary_preferences,
            precision_level=analysis_depth
        )
        
        # Simulate additional processing
        enhanced_analysis = {
            "nutrition": nutrition_result,
            "user_id": user_id,
            "analysis_metadata": {
                "processing_time": 0.1,
                "analysis_depth": analysis_depth,
                "dietary_preferences_applied": bool(dietary_preferences)
            },
            "recommendations": _generate_nutrition_recommendations(nutrition_result),
            "status": "success"
        }
        
        return enhanced_analysis
        
    except Exception as e:
        logger.error(f"Enhanced nutrition analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id,
            "fallback_nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        }


# Example 2: Manual Context Management for Complex Workflows
async def complex_nutrition_workflow_example(
    user_id: str, 
    meal_plan: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Example of complex workflow with manual context management.
    
    This demonstrates:
    - Manual agent context creation
    - Decision point tracking
    - Tool usage monitoring
    - Performance metrics collection
    """
    
    # Create agent monitoring context
    with create_agent_context(
        AgentType.NUTRI_CHECK, 
        "meal_plan_analysis",
        metadata={"user_id": user_id, "meals_count": len(meal_plan)}
    ) as context:
        
        # Track initial decision
        track_agent_decision(
            context,
            decision="meal_plan_analysis_strategy",
            reasoning=f"Analyzing meal plan with {len(meal_plan)} meals for comprehensive nutrition assessment",
            confidence=0.9,
            context_data={
                "meal_count": len(meal_plan),
                "analysis_type": "comprehensive"
            }
        )
        
        # Create tool tracker
        tool_tracker = create_tool_tracker(context)
        
        total_nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        meal_analyses = []
        
        # Process each meal
        for i, meal in enumerate(meal_plan):
            meal_start_time = time.time()
            
            try:
                # Track decision for each meal
                track_agent_decision(
                    context,
                    decision=f"process_meal_{i+1}",
                    reasoning=f"Processing meal {i+1}: {meal.get('name', 'unnamed')}",
                    confidence=0.85,
                    context_data={
                        "meal_index": i,
                        "meal_name": meal.get('name'),
                        "ingredients_count": len(meal.get('ingredients', []))
                    }
                )
                
                # Analyze meal nutrition
                meal_nutrition = await enhanced_nutrition_analysis(
                    ingredients=meal.get('ingredients', []),
                    user_id=user_id,
                    dietary_preferences=meal.get('dietary_preferences'),
                    analysis_depth="detailed"
                )
                
                meal_duration = time.time() - meal_start_time
                
                # Track tool usage for meal analysis
                tool_tracker.track_tool_call(
                    tool_name="enhanced_nutrition_analysis",
                    duration_seconds=meal_duration,
                    success=meal_nutrition.get('status') == 'success',
                    inputs={
                        "meal_name": meal.get('name'),
                        "ingredient_count": len(meal.get('ingredients', []))
                    },
                    outputs={
                        "status": meal_nutrition.get('status'),
                        "calories": meal_nutrition.get('nutrition', {}).get('nutrition', {}).get('calories', 0)
                    }
                )
                
                # Accumulate nutrition data
                if meal_nutrition.get('status') == 'success':
                    nutrition_data = meal_nutrition.get('nutrition', {}).get('nutrition', {})
                    for nutrient in total_nutrition:
                        total_nutrition[nutrient] += nutrition_data.get(nutrient, 0)
                
                meal_analyses.append({
                    "meal_index": i,
                    "meal_name": meal.get('name'),
                    "analysis": meal_nutrition,
                    "processing_time": meal_duration
                })
                
            except Exception as e:
                # Track failed meal processing
                tool_tracker.track_tool_call(
                    tool_name="enhanced_nutrition_analysis",
                    duration_seconds=time.time() - meal_start_time,
                    success=False,
                    inputs={"meal_name": meal.get('name')},
                    outputs=None
                )
                
                meal_analyses.append({
                    "meal_index": i,
                    "meal_name": meal.get('name'),
                    "error": str(e),
                    "processing_time": time.time() - meal_start_time
                })
        
        # Final decision: Overall meal plan assessment
        successful_meals = len([m for m in meal_analyses if 'error' not in m])
        track_agent_decision(
            context,
            decision="meal_plan_completion_assessment",
            reasoning=f"Processed {successful_meals}/{len(meal_plan)} meals successfully",
            confidence=successful_meals / len(meal_plan) if meal_plan else 0,
            context_data={
                "total_meals": len(meal_plan),
                "successful_meals": successful_meals,
                "total_calories": total_nutrition.get('calories', 0)
            }
        )
        
        # Compile final result
        workflow_result = {
            "user_id": user_id,
            "meal_plan_analysis": {
                "total_nutrition": total_nutrition,
                "individual_meals": meal_analyses,
                "summary": {
                    "total_meals": len(meal_plan),
                    "successful_analyses": successful_meals,
                    "total_calories": total_nutrition.get('calories', 0),
                    "avg_calories_per_meal": total_nutrition.get('calories', 0) / len(meal_plan) if meal_plan else 0
                }
            },
            "recommendations": _generate_meal_plan_recommendations(total_nutrition, meal_analyses),
            "processing_metadata": {
                "decision_points_count": len(context.decision_points),
                "tools_used_count": len(context.tool_usage),
                "total_processing_time": context.duration if context.duration else 0
            },
            "status": "success" if successful_meals > 0 else "partial_failure"
        }
        
        return workflow_result


# Example 3: Performance Monitoring and Analysis
async def demonstrate_performance_monitoring():
    """
    Demonstrate performance monitoring capabilities and analytics.
    """
    
    logger.info("Starting performance monitoring demonstration")
    
    # Run several nutrition analyses with different parameters
    test_scenarios = [
        {
            "name": "simple_meal",
            "ingredients": [
                {"name": "chicken breast", "quantity": 200, "unit": "g"},
                {"name": "rice", "quantity": 1, "unit": "cup"}
            ],
            "user_id": "demo_user_1"
        },
        {
            "name": "complex_meal",
            "ingredients": [
                {"name": "salmon fillet", "quantity": 150, "unit": "g"},
                {"name": "quinoa", "quantity": 0.5, "unit": "cup"},
                {"name": "broccoli", "quantity": 1, "unit": "cup"},
                {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
                {"name": "almonds", "quantity": 30, "unit": "g"}
            ],
            "user_id": "demo_user_2",
            "dietary_preferences": ["gluten-free", "low-sodium"]
        },
        {
            "name": "invalid_meal",
            "ingredients": [],  # This will cause an error
            "user_id": "demo_user_3"
        }
    ]
    
    # Execute test scenarios
    results = []
    for scenario in test_scenarios:
        try:
            result = await enhanced_nutrition_analysis(
                ingredients=scenario["ingredients"],
                user_id=scenario["user_id"],
                dietary_preferences=scenario.get("dietary_preferences"),
                analysis_depth="standard"
            )
            results.append({
                "scenario": scenario["name"],
                "status": result.get("status"),
                "success": result.get("status") == "success"
            })
        except Exception as e:
            results.append({
                "scenario": scenario["name"],
                "status": "error",
                "error": str(e),
                "success": False
            })
    
    # Get performance summary
    performance_summary = get_agent_performance_summary()
    
    # Demonstrate health checking
    from backend_gateway.crewai.agent_monitoring import check_agent_health
    agent_health = check_agent_health(AgentType.NUTRI_CHECK)
    
    demonstration_result = {
        "test_scenarios_executed": len(test_scenarios),
        "scenario_results": results,
        "performance_summary": performance_summary,
        "agent_health": agent_health,
        "monitoring_capabilities": {
            "automatic_retry": True,
            "circuit_breaker": True,
            "performance_tracking": True,
            "error_categorization": True,
            "decision_tracking": True,
            "tool_monitoring": True,
            "pii_protection": True
        }
    }
    
    logger.info(
        "Performance monitoring demonstration completed",
        extra={
            "scenarios_run": len(test_scenarios),
            "successful_scenarios": sum(1 for r in results if r["success"]),
            "agent_health_status": agent_health.get("health_status", "unknown")
        }
    )
    
    return demonstration_result


# Helper functions
def _generate_nutrition_recommendations(nutrition_result: Dict[str, Any]) -> List[str]:
    """Generate nutrition recommendations based on analysis results."""
    recommendations = []
    
    nutrition_data = nutrition_result.get('nutrition', {})
    if isinstance(nutrition_data, dict):
        calories = nutrition_data.get('calories', 0)
        protein = nutrition_data.get('protein', 0)
        fat = nutrition_data.get('fat', 0)
        
        if calories > 800:
            recommendations.append("Consider portion control - high calorie content detected")
        
        if protein < 20:
            recommendations.append("Consider adding more protein sources")
        
        if fat > 30:
            recommendations.append("High fat content - consider healthier cooking methods")
    
    return recommendations


def _generate_meal_plan_recommendations(total_nutrition: Dict[str, Any], 
                                      meal_analyses: List[Dict[str, Any]]) -> List[str]:
    """Generate meal plan recommendations based on total nutrition."""
    recommendations = []
    
    total_calories = total_nutrition.get('calories', 0)
    meal_count = len(meal_analyses)
    
    if meal_count > 0:
        avg_calories = total_calories / meal_count
        
        if avg_calories > 700:
            recommendations.append("Consider reducing portion sizes - high average calories per meal")
        elif avg_calories < 300:
            recommendations.append("Consider increasing portion sizes - low average calories per meal")
    
    if total_nutrition.get('protein', 0) < meal_count * 25:
        recommendations.append("Consider adding more protein-rich foods to your meal plan")
    
    return recommendations


# Example usage and testing
async def run_monitoring_examples():
    """Run all monitoring examples to demonstrate capabilities."""
    
    logger.info("Starting comprehensive monitoring examples")
    
    # Example 1: Simple nutrition analysis with monitoring
    print("=== Example 1: Enhanced Nutrition Analysis ===")
    simple_result = await enhanced_nutrition_analysis(
        ingredients=[
            {"name": "chicken breast", "quantity": 200, "unit": "g"},
            {"name": "broccoli", "quantity": 1, "unit": "cup"}
        ],
        user_id="example_user_1"
    )
    print(f"Simple analysis result: {simple_result.get('status')}")
    
    # Example 2: Complex workflow with manual context
    print("\n=== Example 2: Complex Meal Plan Analysis ===")
    meal_plan = [
        {
            "name": "Breakfast",
            "ingredients": [
                {"name": "oats", "quantity": 0.5, "unit": "cup"},
                {"name": "banana", "quantity": 1, "unit": "medium"},
                {"name": "almond milk", "quantity": 1, "unit": "cup"}
            ]
        },
        {
            "name": "Lunch", 
            "ingredients": [
                {"name": "chicken breast", "quantity": 150, "unit": "g"},
                {"name": "quinoa", "quantity": 0.5, "unit": "cup"},
                {"name": "mixed vegetables", "quantity": 1, "unit": "cup"}
            ],
            "dietary_preferences": ["gluten-free"]
        }
    ]
    
    complex_result = await complex_nutrition_workflow_example("example_user_2", meal_plan)
    print(f"Complex workflow result: {complex_result.get('status')}")
    
    # Example 3: Performance monitoring demonstration
    print("\n=== Example 3: Performance Monitoring ===")
    performance_result = await demonstrate_performance_monitoring()
    print(f"Performance demonstration completed with {performance_result['test_scenarios_executed']} scenarios")
    
    # Summary
    print("\n=== Monitoring Summary ===")
    summary = get_agent_performance_summary()
    print(f"Total agents monitored: {len(summary.get('agents', {}))}")
    
    for agent_name, agent_data in summary.get('agents', {}).items():
        print(f"  {agent_name}: {agent_data.get('health_status', 'unknown')} "
              f"({agent_data.get('success_rate', 0):.1%} success rate)")


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_monitoring_examples())