"""
Service for managing FAO Food Loss and Waste data
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class FoodWasteService:
    """Service for handling food loss and waste data from FAO"""

    # FAO FLW Database URL (placeholder - needs manual download)
    FAO_FLW_URL = "https://www.fao.org/platform-food-loss-waste/flw-data/"

    # Default loss rates by commodity group (fallback values)
    DEFAULT_LOSS_RATES = {
        "Fruits & Vegetables": 0.25,  # 25% average loss
        "Cereals": 0.06,  # 6% average loss
        "Roots & Tubers": 0.20,  # 20% average loss
        "Oilseeds & Pulses": 0.08,  # 8% average loss
        "Meat": 0.11,  # 11% average loss
        "Fish & Seafood": 0.15,  # 15% average loss
        "Milk": 0.07,  # 7% average loss
        "Eggs": 0.08,  # 8% average loss
    }

    # CPC to common food mapping (sample mappings)
    CPC_TO_FOOD_SAMPLES = {
        "01211": ["apples", "apple"],
        "01212": ["pears", "pear"],
        "01213": ["peaches", "peach", "nectarines"],
        "01221": ["grapes"],
        "01231": ["berries", "strawberries", "blueberries", "raspberries"],
        "01241": ["oranges", "orange"],
        "01242": ["lemons", "lemon", "limes", "lime"],
        "01251": ["bananas", "banana"],
        "01311": ["tomatoes", "tomato"],
        "01312": ["onions", "onion"],
        "01313": ["garlic"],
        "01314": ["leeks"],
        "01321": ["cabbage"],
        "01322": ["cauliflower"],
        "01323": ["broccoli"],
        "01324": ["brussels_sprouts"],
        "01331": ["lettuce"],
        "01332": ["spinach"],
        "01341": ["carrots", "carrot"],
        "01342": ["turnips", "turnip"],
        "01351": ["potatoes", "potato"],
        "01352": ["sweet_potatoes", "yams"],
        "01411": ["wheat", "flour", "bread", "pasta"],
        "01412": ["rice", "white_rice", "brown_rice"],
        "01413": ["corn", "maize"],
        "01421": ["barley"],
        "01422": ["oats", "oatmeal"],
        "01511": ["soybeans", "soy"],
        "01512": ["peanuts", "peanut_butter"],
        "01521": ["lentils"],
        "01522": ["chickpeas"],
        "01523": ["beans", "black_beans", "kidney_beans"],
        "02111": ["beef", "ground_beef", "steak"],
        "02112": ["veal"],
        "02121": ["pork", "bacon", "ham"],
        "02131": ["lamb", "mutton"],
        "02141": ["chicken", "poultry", "turkey"],
        "02211": ["milk", "whole_milk", "skim_milk"],
        "02212": ["cream"],
        "02221": ["butter"],
        "02222": ["cheese", "cheddar", "mozzarella"],
        "02231": ["eggs", "egg"],
        "02311": ["fish", "salmon", "tuna", "cod"],
        "02321": ["shrimp", "prawns"],
        "02322": ["crab", "lobster"],
    }

    def __init__(self):
        self.data_dir = Path("data/food_loss_waste")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._loss_data = {}
        self._cpc_mapping = {}
        self._load_cached_data()

    def download_flw_data(self, csv_path: Optional[str] = None) -> pd.DataFrame:
        """
        Process FAO FLW data from CSV file
        Note: FAO data must be manually downloaded from their platform
        """
        if not csv_path:
            csv_path = self.data_dir / "fao_flw_data.csv"

        if not Path(csv_path).exists():
            logger.warning(
                f"FAO FLW data not found at {csv_path}. "
                "Please download from https://www.fao.org/platform-food-loss-waste/flw-data/"
            )
            return pd.DataFrame()

        try:
            # Read FAO CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows of FLW data")

            # Expected columns: year, country, commodity_group, cpc_code, stage, loss_percentage, etc.
            # Filter for consumer and retail stages
            consumer_data = df[df["stage"].isin(["Consumer", "Retail", "consumer", "retail"])]

            # Group by commodity and calculate statistics
            grouped = consumer_data.groupby(["cpc_code", "commodity_name", "stage"])

            loss_stats = (
                grouped["loss_percentage"]
                .agg(["median", "mean", "min", "max", "count"])
                .reset_index()
            )

            loss_stats.columns = [
                "cpc_code",
                "commodity_name",
                "stage",
                "median_loss_pct",
                "mean_loss_pct",
                "min_loss_pct",
                "max_loss_pct",
                "observations",
            ]

            # Save processed data
            output_file = self.data_dir / "processed_flw_data.json"
            loss_stats.to_json(output_file, orient="records")

            logger.info(f"Processed FLW data saved to {output_file}")
            return loss_stats

        except Exception as e:
            logger.error(f"Error processing FLW data: {str(e)}")
            return pd.DataFrame()

    def _load_cached_data(self):
        """Load processed FLW data from cache"""
        cache_file = self.data_dir / "processed_flw_data.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    for item in data:
                        cpc = item["cpc_code"]
                        self._loss_data[cpc] = item
                logger.info(f"Loaded waste data for {len(self._loss_data)} CPC codes")
            except Exception as e:
                logger.error(f"Error loading cached FLW data: {str(e)}")

        # Load CPC mappings
        self._cpc_mapping = self.CPC_TO_FOOD_SAMPLES.copy()

    def get_loss_rate(self, food_name: str, stage: str = "consumer") -> Optional[float]:
        """Get loss rate for a specific food item"""
        # Find CPC code for this food
        cpc_code = None
        food_lower = food_name.lower()

        for cpc, foods in self._cpc_mapping.items():
            if food_lower in foods or any(food in food_lower for food in foods):
                cpc_code = cpc
                break

        if not cpc_code:
            # Try to match by commodity group
            return self._get_default_loss_rate(food_name)

        # Get loss data for this CPC code
        if cpc_code in self._loss_data:
            data = self._loss_data[cpc_code]
            return data.get("median_loss_pct", 0) / 100  # Convert percentage to decimal

        return self._get_default_loss_rate(food_name)

    def _get_default_loss_rate(self, food_name: str) -> float:
        """Get default loss rate based on food category"""
        food_lower = food_name.lower()

        # Simple categorization
        if any(
            item in food_lower
            for item in [
                "apple",
                "banana",
                "berry",
                "fruit",
                "vegetable",
                "tomato",
                "lettuce",
                "spinach",
                "carrot",
            ]
        ):
            return self.DEFAULT_LOSS_RATES["Fruits & Vegetables"]
        elif any(item in food_lower for item in ["rice", "wheat", "bread", "pasta", "cereal"]):
            return self.DEFAULT_LOSS_RATES["Cereals"]
        elif any(item in food_lower for item in ["potato", "sweet potato", "yam"]):
            return self.DEFAULT_LOSS_RATES["Roots & Tubers"]
        elif any(item in food_lower for item in ["beef", "pork", "chicken", "meat", "poultry"]):
            return self.DEFAULT_LOSS_RATES["Meat"]
        elif any(item in food_lower for item in ["fish", "salmon", "tuna", "shrimp", "seafood"]):
            return self.DEFAULT_LOSS_RATES["Fish & Seafood"]
        elif any(item in food_lower for item in ["milk", "cheese", "yogurt", "dairy"]):
            return self.DEFAULT_LOSS_RATES["Milk"]
        elif "egg" in food_lower:
            return self.DEFAULT_LOSS_RATES["Eggs"]
        else:
            return 0.10  # Default 10% loss rate

    def calculate_waste_risk_score(
        self,
        food_name: str,
        days_until_expiry: int,
        quantity: float = 1.0,
        storage_quality: str = "good",  # 'excellent', 'good', 'fair', 'poor'
    ) -> dict[str, any]:
        """
        Calculate waste risk score for a pantry item

        Returns dict with:
        - risk_score: 0-100 (higher = more likely to be wasted)
        - risk_category: 'very_high', 'high', 'medium', 'low'
        - recommended_action: What to do with this item
        """
        # Get base loss rate
        base_loss_rate = self.get_loss_rate(food_name)

        # Adjust for storage quality
        storage_multipliers = {
            "excellent": 0.7,  # 30% reduction in waste
            "good": 1.0,  # No change
            "fair": 1.3,  # 30% increase
            "poor": 1.8,  # 80% increase
        }
        storage_mult = storage_multipliers.get(storage_quality, 1.0)

        # Calculate time-based risk
        if days_until_expiry <= 0:
            time_risk = 1.0  # Maximum risk
        elif days_until_expiry <= 2:
            time_risk = 0.8
        elif days_until_expiry <= 5:
            time_risk = 0.5
        elif days_until_expiry <= 7:
            time_risk = 0.3
        else:
            time_risk = 0.1

        # Combine factors
        risk_score = min(100, (base_loss_rate * storage_mult * 100) + (time_risk * 50))

        # Categorize risk
        if risk_score >= 75:
            category = "very_high"
            action = "Use today or freeze immediately"
        elif risk_score >= 50:
            category = "high"
            action = "Use within 1-2 days"
        elif risk_score >= 25:
            category = "medium"
            action = "Plan to use this week"
        else:
            category = "low"
            action = "Monitor normally"

        return {
            "food_name": food_name,
            "base_loss_rate": base_loss_rate,
            "adjusted_loss_rate": base_loss_rate * storage_mult,
            "days_until_expiry": days_until_expiry,
            "risk_score": round(risk_score, 1),
            "risk_category": category,
            "recommended_action": action,
            "quantity_at_risk": quantity,
        }

    def prioritize_pantry_by_waste_risk(self, pantry_items: list[dict]) -> list[dict]:
        """
        Sort pantry items by waste risk priority

        Args:
            pantry_items: List of dicts with 'product_name', 'expiry_date', 'quantity'

        Returns:
            Sorted list with waste risk scores added
        """
        today = datetime.now().date()
        items_with_risk = []

        for item in pantry_items:
            # Calculate days until expiry
            if isinstance(item.get("expiry_date"), str):
                expiry = datetime.fromisoformat(item["expiry_date"]).date()
            else:
                expiry = item.get("expiry_date", today + timedelta(days=7))

            days_left = (expiry - today).days

            # Calculate waste risk
            risk_data = self.calculate_waste_risk_score(
                food_name=item.get("product_name", ""),
                days_until_expiry=days_left,
                quantity=item.get("quantity", 1.0),
            )

            # Add risk data to item
            item_with_risk = item.copy()
            item_with_risk.update(risk_data)
            items_with_risk.append(item_with_risk)

        # Sort by risk score (highest first)
        items_with_risk.sort(key=lambda x: x["risk_score"], reverse=True)

        return items_with_risk

    def suggest_waste_reduction_recipes(
        self, high_risk_items: list[str], available_recipes: list[dict]
    ) -> list[tuple[dict, float]]:
        """
        Prioritize recipes that use high-waste-risk ingredients

        Returns:
            List of (recipe, waste_reduction_score) tuples
        """
        recipe_scores = []

        for recipe in available_recipes:
            waste_score = 0
            ingredients_used = 0

            # Check recipe ingredients
            for ingredient in recipe.get("ingredients", []):
                ing_name = ingredient.get("name", "").lower()

                # Check if this ingredient is high risk
                for risk_item in high_risk_items:
                    if risk_item.lower() in ing_name or ing_name in risk_item.lower():
                        # Get the waste rate for this ingredient
                        loss_rate = self.get_loss_rate(risk_item)
                        waste_score += loss_rate * 100
                        ingredients_used += 1

            if ingredients_used > 0:
                # Normalize score by number of high-risk ingredients used
                normalized_score = waste_score / ingredients_used
                recipe_scores.append((recipe, normalized_score))

        # Sort by waste reduction potential
        recipe_scores.sort(key=lambda x: x[1], reverse=True)

        return recipe_scores

    def calculate_waste_impact(
        self,
        food_name: str,
        quantity_kg: float,
        price_per_kg: Optional[float] = None,
        include_supply_chain: bool = True,
    ) -> dict[str, float]:
        """
        Calculate economic and environmental impact of potential waste

        Args:
            food_name: Name of the food item
            quantity_kg: Quantity in kilograms
            price_per_kg: Price per kilogram
            include_supply_chain: Include upstream supply chain losses

        Returns:
            Dict with 'economic_loss', 'ghg_impact', 'supply_chain_multiplier'
        """
        loss_rate = self.get_loss_rate(food_name)
        potential_waste_kg = quantity_kg * loss_rate

        impact = {
            "potential_waste_kg": round(potential_waste_kg, 2),
            "waste_percentage": round(loss_rate * 100, 1),
        }

        # Economic impact
        if price_per_kg:
            impact["economic_loss"] = round(potential_waste_kg * price_per_kg, 2)

        # Supply chain multiplier (simplified - would use actual data in production)
        if include_supply_chain:
            # Estimate based on food category
            food_lower = food_name.lower()
            if any(item in food_lower for item in ["lettuce", "spinach", "tomato", "berry"]):
                multiplier = 2.5  # High supply chain loss
            elif any(item in food_lower for item in ["banana", "apple", "orange"]):
                multiplier = 2.0  # Medium supply chain loss
            elif any(item in food_lower for item in ["rice", "pasta", "bread"]):
                multiplier = 1.5  # Low supply chain loss
            else:
                multiplier = 1.8  # Default

            impact["supply_chain_multiplier"] = multiplier
            impact["total_production_kg"] = round(potential_waste_kg * multiplier, 2)
            impact["upstream_waste_kg"] = round(potential_waste_kg * (multiplier - 1), 2)

            # Amplified economic impact
            if price_per_kg:
                # Supply chain costs are typically 40-60% of retail price
                supply_chain_cost_factor = 0.5
                impact["total_economic_impact"] = round(
                    impact["economic_loss"]
                    + (impact["upstream_waste_kg"] * price_per_kg * supply_chain_cost_factor),
                    2,
                )

        return impact


# Singleton instance
_instance = None


def get_food_waste_service() -> FoodWasteService:
    global _instance
    if _instance is None:
        _instance = FoodWasteService()
    return _instance
