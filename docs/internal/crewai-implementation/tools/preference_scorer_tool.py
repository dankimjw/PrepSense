"""Preference Scorer Tool for CrewAI

Wraps the existing PreferenceAnalyzerService to score recipes based on user preferences.
"""

from crewai.tools import BaseTool
from backend_gateway.services.preference_analyzer_service import PreferenceAnalyzerService
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PreferenceScorerTool(BaseTool):
    name: str = "preference_scorer" 
    description: str = "Score recipes using existing preference analyzer"
    
    def _run(self, recipe: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Use existing preference scoring service"""
        try:
            scorer = PreferenceAnalyzerService()
            result = scorer.score_recipe(recipe, user_preferences)
            
            if isinstance(result, dict):
                return {
                    "status": "success",
                    "score": result.get("score", 0),
                    "breakdown": result.get("breakdown", {}),
                    "reasoning": result.get("reasoning", ""),
                    "recipe_id": recipe.get("id"),
                    "recipe_title": recipe.get("title")
                }
            else:
                # If result is just a score
                return {
                    "status": "success",
                    "score": float(result) if result is not None else 0,
                    "breakdown": {},
                    "reasoning": "Preference score calculated",
                    "recipe_id": recipe.get("id"),
                    "recipe_title": recipe.get("title")
                }
                
        except Exception as e:
            logger.error(f"Preference scoring failed for recipe {recipe.get('id', 'unknown')}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "score": 0,
                "breakdown": {},
                "reasoning": "Failed to calculate preference score",
                "recipe_id": recipe.get("id"),
                "recipe_title": recipe.get("title")
            }