"""Service for managing environmental impact data from Our World in Data"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class EnvironmentalImpactService:
    """Service for handling environmental impact data from OWID"""

    # OWID data sources
    OWID_DATASETS = {
        "ghg": "https://ourworldindata.org/grapher/ghg-per-kg-poore.csv",
        "land": "https://ourworldindata.org/grapher/land-use-per-kg-poore.csv",
        "water": "https://ourworldindata.org/grapher/freshwater-withdrawals-per-kg-poore.csv",
        "eutrophying": "https://ourworldindata.org/grapher/eutrophying-emissions-per-kg-poore.csv",
        "supply_chain": "https://ourworldindata.org/grapher/food-emissions-supply-chain.csv",
    }

    # Mapping between OWID product names and our food categories
    OWID_TO_FOOD_MAPPING = {
        "Beef (beef herd)": ["beef", "ground_beef", "steak", "beef_roast", "beef_stew"],
        "Beef (dairy herd)": ["beef_dairy", "veal"],
        "Lamb & Mutton": ["lamb", "mutton", "lamb_chops"],
        "Pig Meat": ["pork", "bacon", "ham", "pork_chops", "ground_pork"],
        "Poultry Meat": ["chicken", "chicken_breast", "chicken_thigh", "turkey", "duck"],
        "Eggs": ["eggs", "egg"],
        "Fish (farmed)": ["salmon", "tilapia", "catfish", "farmed_fish"],
        "Shrimps (farmed)": ["shrimp", "prawns"],
        "Milk": ["milk", "whole_milk", "skim_milk", "2_percent_milk"],
        "Cheese": ["cheese", "cheddar", "mozzarella", "parmesan", "swiss_cheese"],
        "Tofu": ["tofu", "firm_tofu", "soft_tofu", "silken_tofu"],
        "Groundnuts": ["peanuts", "peanut_butter"],
        "Other Pulses": ["lentils", "chickpeas", "black_beans", "kidney_beans", "pinto_beans"],
        "Peas": ["peas", "green_peas", "split_peas"],
        "Nuts": ["almonds", "walnuts", "cashews", "pecans", "pistachios"],
        "Wheat & Rye": ["wheat", "bread", "pasta", "flour", "rye_bread"],
        "Rice": ["rice", "white_rice", "brown_rice", "wild_rice"],
        "Potatoes": ["potatoes", "potato", "sweet_potatoes", "yams"],
        "Tomatoes": ["tomatoes", "tomato", "cherry_tomatoes", "roma_tomatoes"],
        "Root Vegetables": ["carrots", "turnips", "radishes", "beets"],
        "Brassicas": ["broccoli", "cauliflower", "cabbage", "brussels_sprouts"],
        "Other Vegetables": ["lettuce", "spinach", "cucumbers", "peppers", "zucchini"],
        "Citrus Fruit": ["oranges", "lemons", "limes", "grapefruit"],
        "Bananas": ["bananas", "banana", "plantains"],
        "Apples": ["apples", "apple"],
        "Berries & Grapes": ["strawberries", "blueberries", "raspberries", "grapes"],
        "Coffee": ["coffee", "coffee_beans"],
        "Dark Chocolate": ["dark_chocolate", "cocoa"],
        "Cane Sugar": ["sugar", "white_sugar", "brown_sugar"],
        "Olive Oil": ["olive_oil", "extra_virgin_olive_oil"],
        "Palm Oil": ["palm_oil"],
        "Soybean Oil": ["soybean_oil", "vegetable_oil"],
        "Rapeseed Oil": ["canola_oil", "rapeseed_oil"],
        "Wine": ["wine", "red_wine", "white_wine"],
    }

    def __init__(self):
        self.data_dir = Path("data/environmental_impact")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._impact_data = {}
        self._load_cached_data()

    def download_owid_data(self, force_update: bool = False) -> Dict[str, pd.DataFrame]:
        """Download or update OWID environmental impact data"""

        for dataset_name, url in self.OWID_DATASETS.items():
            cache_file = self.data_dir / f"{dataset_name}_owid.csv"

            # Check if we need to download
            if not force_update and cache_file.exists():
                # Check if data is less than 7 days old
                file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_age.days < 7:
                    logger.info(f"Using cached {dataset_name} data")
                    continue

            try:
                logger.info(f"Downloading {dataset_name} data from OWID...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Save to cache
                with open(cache_file, "w") as f:
                    f.write(response.text)

                logger.info(f"Successfully downloaded {dataset_name} data")

            except Exception as e:
                logger.error(f"Error downloading {dataset_name} data: {str(e)}")
                if not cache_file.exists():
                    raise

        return self._load_all_datasets()

    def _load_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """Load all cached datasets"""
        datasets = {}

        for dataset_name in self.OWID_DATASETS.keys():
            cache_file = self.data_dir / f"{dataset_name}_owid.csv"
            if cache_file.exists():
                try:
                    df = pd.read_csv(cache_file)
                    datasets[dataset_name] = df
                    logger.info(f"Loaded {dataset_name} dataset with {len(df)} entries")
                except Exception as e:
                    logger.error(f"Error loading {dataset_name} dataset: {str(e)}")

        return datasets

    def _load_cached_data(self):
        """Load processed impact data from cache"""
        cache_file = self.data_dir / "processed_impact_data.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self._impact_data = json.load(f)
                logger.info(f"Loaded impact data for {len(self._impact_data)} food items")
            except Exception as e:
                logger.error(f"Error loading cached impact data: {str(e)}")

    def process_impact_data(self) -> Dict[str, Dict]:
        """Process OWID data into our food database format"""
        datasets = self._load_all_datasets()

        if not datasets:
            logger.warning("No datasets loaded, downloading now...")
            datasets = self.download_owid_data()

        impact_data = {}

        # Process each OWID product
        for owid_product, food_items in self.OWID_TO_FOOD_MAPPING.items():

            # Get environmental metrics for this product
            metrics = {
                "ghg_kg_co2e_per_kg": self._get_metric(
                    datasets.get("ghg"), owid_product, "per kilogram"
                ),
                "land_m2_per_kg": self._get_metric(
                    datasets.get("land"), owid_product, "per kilogram"
                ),
                "water_L_per_kg": self._get_metric(
                    datasets.get("water"), owid_product, "per kilogram"
                ),
                "eutrophying_g_per_kg": self._get_metric(
                    datasets.get("eutrophying"), owid_product, "per kilogram"
                ),
                "supply_chain_breakdown": self._get_supply_chain_breakdown(
                    datasets.get("supply_chain"), owid_product
                ),
            }

            # Apply to all mapped food items
            for food_item in food_items:
                impact_data[food_item] = {
                    "owid_product": owid_product,
                    "environmental": metrics,
                    "sustainability_profile": self._calculate_sustainability_profile(metrics),
                }

        # Save processed data
        cache_file = self.data_dir / "processed_impact_data.json"
        with open(cache_file, "w") as f:
            json.dump(impact_data, f, indent=2)

        self._impact_data = impact_data
        logger.info(f"Processed impact data for {len(impact_data)} food items")

        return impact_data

    def _get_metric(self, df: Optional[pd.DataFrame], product: str, unit: str) -> Optional[float]:
        """Extract a metric value from a dataframe"""
        if df is None or df.empty:
            return None

        try:
            # Try exact match first
            mask = (df["Entity"] == product) & (df["Unit"] == unit)
            if mask.any():
                # Get the most recent year's data
                row = df[mask].sort_values("Year", ascending=False).iloc[0]
                return float(row.iloc[-1])  # Last column is usually the value

            # Try fuzzy match
            for col in ["Entity", "Food product"]:
                if col in df.columns:
                    mask = df[col].str.contains(product.split("(")[0].strip(), case=False, na=False)
                    if mask.any():
                        row = df[mask].sort_values("Year", ascending=False).iloc[0]
                        return float(row.iloc[-1])

        except Exception as e:
            logger.debug(f"Could not find metric for {product}: {str(e)}")

        return None

    def _get_supply_chain_breakdown(
        self, df: Optional[pd.DataFrame], product: str
    ) -> Dict[str, float]:
        """Extract supply chain breakdown from data"""
        breakdown = {
            "land_use_change": 0.0,
            "feed": 0.0,
            "farm": 0.0,
            "processing": 0.0,
            "transport": 0.0,
            "packaging": 0.0,
            "retail": 0.0,
        }

        if df is None:
            return breakdown

        try:
            # Find the product row
            mask = df["Entity"] == product
            if mask.any():
                row = df[mask].iloc[0]

                # Map column names to our structure
                column_mapping = {
                    "Land use change": "land_use_change",
                    "Animal Feed": "feed",
                    "Farm": "farm",
                    "Processing": "processing",
                    "Transport": "transport",
                    "Packaging": "packaging",
                    "Retail": "retail",
                }

                total = 0
                for col, key in column_mapping.items():
                    if col in df.columns:
                        value = float(row[col]) if pd.notna(row[col]) else 0.0
                        breakdown[key] = value
                        total += value

                # Normalize to percentages
                if total > 0:
                    for key in breakdown:
                        breakdown[key] = round(breakdown[key] / total, 3)

        except Exception as e:
            logger.debug(f"Could not get supply chain breakdown for {product}: {str(e)}")

        return breakdown

    def _calculate_sustainability_profile(self, metrics: Dict) -> Dict:
        """Calculate sustainability scores and categories"""
        ghg = metrics.get("ghg_kg_co2e_per_kg", 0)

        # Categorize impact level
        if ghg < 1:
            impact_category = "very_low"
            planet_score = 9
        elif ghg < 3:
            impact_category = "low"
            planet_score = 7
        elif ghg < 7:
            impact_category = "medium"
            planet_score = 5
        elif ghg < 15:
            impact_category = "high"
            planet_score = 3
        else:
            impact_category = "very_high"
            planet_score = 1

        return {
            "impact_category": impact_category,
            "planet_score": planet_score,
            "ghg_visual": self._get_impact_visual(impact_category),
        }

    def _get_impact_visual(self, category: str) -> str:
        """Get visual representation of impact"""
        visuals = {"very_low": "🟢", "low": "🟢", "medium": "🟡", "high": "🟠", "very_high": "🔴"}
        return visuals.get(category, "⚪")

    def get_food_impact(self, food_name: str) -> Optional[Dict]:
        """Get environmental impact data for a specific food"""
        # Try direct match
        if food_name.lower() in self._impact_data:
            return self._impact_data[food_name.lower()]

        # Try partial match
        for key in self._impact_data:
            if food_name.lower() in key or key in food_name.lower():
                return self._impact_data[key]

        return None

    def calculate_recipe_impact(self, ingredients: List[Dict]) -> Dict:
        """Calculate total environmental impact for a recipe"""
        total_ghg = 0
        total_land = 0
        total_water = 0
        missing_data = []

        for ingredient in ingredients:
            food_name = ingredient.get("name", "")
            quantity_kg = ingredient.get("quantity_kg", 0)

            impact = self.get_food_impact(food_name)
            if impact and impact.get("environmental"):
                env = impact["environmental"]
                total_ghg += (env.get("ghg_kg_co2e_per_kg", 0) or 0) * quantity_kg
                total_land += (env.get("land_m2_per_kg", 0) or 0) * quantity_kg
                total_water += (env.get("water_L_per_kg", 0) or 0) * quantity_kg
            else:
                missing_data.append(food_name)

        return {
            "total_ghg_kg_co2e": round(total_ghg, 2),
            "total_land_m2": round(total_land, 2),
            "total_water_L": round(total_water, 2),
            "missing_data": missing_data,
            "impact_category": self._categorize_recipe_impact(total_ghg),
            "driving_equivalent_miles": round(total_ghg * 2.5, 1),  # Rough conversion
        }

    def _categorize_recipe_impact(self, ghg: float) -> str:
        """Categorize recipe impact level"""
        if ghg < 2:
            return "very_low"
        elif ghg < 5:
            return "low"
        elif ghg < 10:
            return "medium"
        elif ghg < 20:
            return "high"
        else:
            return "very_high"

    def suggest_sustainable_swaps(self, ingredient: str, max_suggestions: int = 3) -> List[Dict]:
        """Suggest lower-impact alternatives for an ingredient"""
        current_impact = self.get_food_impact(ingredient)
        if not current_impact:
            return []

        current_ghg = current_impact["environmental"].get("ghg_kg_co2e_per_kg", float("inf"))
        suggestions = []

        # Find lower-impact alternatives
        for food_name, data in self._impact_data.items():
            if food_name == ingredient:
                continue

            food_ghg = data["environmental"].get("ghg_kg_co2e_per_kg", float("inf"))

            # Only suggest if significantly lower impact (at least 30% reduction)
            if food_ghg < current_ghg * 0.7:
                co2_savings = current_ghg - food_ghg
                percentage_reduction = (co2_savings / current_ghg) * 100

                suggestions.append(
                    {
                        "ingredient": food_name,
                        "co2_savings_per_kg": round(co2_savings, 2),
                        "percentage_reduction": round(percentage_reduction, 1),
                        "impact_category": data["sustainability_profile"]["impact_category"],
                        "planet_score": data["sustainability_profile"]["planet_score"],
                    }
                )

        # Sort by CO2 savings and return top suggestions
        suggestions.sort(key=lambda x: x["co2_savings_per_kg"], reverse=True)
        return suggestions[:max_suggestions]


# Initialize service as singleton
_instance = None


def get_environmental_impact_service() -> EnvironmentalImpactService:
    global _instance
    if _instance is None:
        _instance = EnvironmentalImpactService()
    return _instance
