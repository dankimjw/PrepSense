"""Pantry analysis tool for CrewAI agents."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from backend_gateway.tools.database_tool import create_database_tool

# from crewai_tools import BaseTool  # Not available in CrewAI 0.5.0


logger = logging.getLogger(__name__)


class PantryTool:
    """Tool for pantry analysis and management."""

    name: str = "pantry_tool"
    description: str = (
        "A tool for analyzing pantry items, identifying expiring ingredients, "
        "categorizing items, and providing insights for recipe recommendations."
    )

    def __init__(self):
        self.db_tool = create_database_tool()

    def _run(self, action: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Execute a pantry analysis action.

        Args:
            action: The action to perform (analyze, expiring, categories, etc.)
            user_id: The user ID
            **kwargs: Additional parameters

        Returns:
            Dict containing the analysis results
        """
        try:
            if action == "analyze":
                return self._analyze_pantry(user_id)
            elif action == "expiring":
                days = kwargs.get("days", 7)
                return self._get_expiring_items(user_id, days)
            elif action == "categories":
                return self._categorize_items(user_id)
            elif action == "proteins":
                return self._get_protein_sources(user_id)
            elif action == "staples":
                return self._get_staple_items(user_id)
            elif action == "available_ingredients":
                return self._get_available_ingredients(user_id)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Pantry tool error: {str(e)}")
            return {"error": f"Pantry analysis failed: {str(e)}"}

    def _analyze_pantry(self, user_id: int) -> Dict[str, Any]:
        """Comprehensive pantry analysis."""
        # Get pantry items
        pantry_data = self.db_tool._run("pantry_items", user_id)

        if "error" in pantry_data:
            return pantry_data

        pantry_items = pantry_data["items"]
        today = date.today()

        analysis = {
            "user_id": user_id,
            "total_items": len(pantry_items),
            "expiring_soon": [],
            "expired": [],
            "categories": {},
            "protein_sources": [],
            "staples": [],
            "available_ingredients": [],
        }

        # Analyze each item
        for item in pantry_items:
            product_name = item.get("product_name", "").lower()
            category = item.get("category", "other")

            # Check expiration
            if item.get("expiration_date"):
                try:
                    if isinstance(item["expiration_date"], str):
                        exp_date = datetime.strptime(item["expiration_date"], "%Y-%m-%d").date()
                    else:
                        exp_date = item["expiration_date"]

                    days_until = (exp_date - today).days

                    if days_until < 0:
                        analysis["expired"].append(
                            {
                                "name": item["product_name"],
                                "days_expired": abs(days_until),
                                "date": exp_date.strftime("%Y-%m-%d"),
                            }
                        )
                    elif days_until <= 7:
                        analysis["expiring_soon"].append(
                            {
                                "name": item["product_name"],
                                "days": days_until,
                                "date": exp_date.strftime("%Y-%m-%d"),
                            }
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid expiration date for {product_name}: {e}")

            # Categorize items
            if category not in analysis["categories"]:
                analysis["categories"][category] = []
            analysis["categories"][category].append(product_name)

            # Identify proteins
            protein_keywords = [
                "chicken",
                "beef",
                "pork",
                "fish",
                "salmon",
                "tuna",
                "tofu",
                "beans",
                "eggs",
                "turkey",
                "lamb",
            ]
            if any(protein in product_name for protein in protein_keywords):
                analysis["protein_sources"].append(product_name)

            # Identify staples
            staple_keywords = [
                "rice",
                "pasta",
                "bread",
                "potato",
                "flour",
                "oats",
                "quinoa",
                "noodles",
            ]
            if any(staple in product_name for staple in staple_keywords):
                analysis["staples"].append(product_name)

            # Add to available ingredients (non-expired)
            if not item.get("expiration_date") or (item.get("expiration_date") and days_until >= 0):
                analysis["available_ingredients"].append(
                    {
                        "name": item["product_name"],
                        "category": category,
                        "quantity": item.get("quantity", 1),
                        "unit": item.get("unit_of_measurement", "unit"),
                    }
                )

        # Add summary statistics
        analysis["summary"] = {
            "categories_count": len(analysis["categories"]),
            "proteins_count": len(analysis["protein_sources"]),
            "staples_count": len(analysis["staples"]),
            "expiring_count": len(analysis["expiring_soon"]),
            "expired_count": len(analysis["expired"]),
            "available_count": len(analysis["available_ingredients"]),
        }

        return analysis

    def _get_expiring_items(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Get items expiring within specified days."""
        analysis = self._analyze_pantry(user_id)

        if "error" in analysis:
            return analysis

        # Filter items expiring within the specified days
        expiring_items = []
        for item in analysis["expiring_soon"]:
            if item["days"] <= days:
                expiring_items.append(item)

        return {
            "user_id": user_id,
            "days_threshold": days,
            "expiring_items": expiring_items,
            "count": len(expiring_items),
        }

    def _categorize_items(self, user_id: int) -> Dict[str, Any]:
        """Get pantry items organized by category."""
        analysis = self._analyze_pantry(user_id)

        if "error" in analysis:
            return analysis

        return {
            "user_id": user_id,
            "categories": analysis["categories"],
            "category_counts": {cat: len(items) for cat, items in analysis["categories"].items()},
        }

    def _get_protein_sources(self, user_id: int) -> Dict[str, Any]:
        """Get available protein sources."""
        analysis = self._analyze_pantry(user_id)

        if "error" in analysis:
            return analysis

        return {
            "user_id": user_id,
            "protein_sources": analysis["protein_sources"],
            "count": len(analysis["protein_sources"]),
        }

    def _get_staple_items(self, user_id: int) -> Dict[str, Any]:
        """Get available staple items."""
        analysis = self._analyze_pantry(user_id)

        if "error" in analysis:
            return analysis

        return {
            "user_id": user_id,
            "staple_items": analysis["staples"],
            "count": len(analysis["staples"]),
        }

    def _get_available_ingredients(self, user_id: int) -> Dict[str, Any]:
        """Get all available (non-expired) ingredients."""
        analysis = self._analyze_pantry(user_id)

        if "error" in analysis:
            return analysis

        return {
            "user_id": user_id,
            "available_ingredients": analysis["available_ingredients"],
            "count": len(analysis["available_ingredients"]),
            "ingredient_names": [item["name"] for item in analysis["available_ingredients"]],
        }


# Helper function to create the tool
def create_pantry_tool() -> PantryTool:
    """Create and return a PantryTool instance."""
    return PantryTool()
