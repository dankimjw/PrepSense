#!/usr/bin/env python3
"""Script to download and process OWID environmental impact data"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging

from backend_gateway.services.environmental_impact_service import get_environmental_impact_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Download and process OWID environmental data"""

    logger.info("Starting OWID data download and processing...")

    # Initialize service
    impact_service = get_environmental_impact_service()

    # Download data
    logger.info("Downloading OWID datasets...")
    datasets = impact_service.download_owid_data(force_update=True)

    logger.info(f"Downloaded {len(datasets)} datasets")
    for name, df in datasets.items():
        logger.info(f"  - {name}: {len(df)} rows")

    # Process data
    logger.info("\nProcessing impact data...")
    impact_data = impact_service.process_impact_data()

    logger.info(f"\nProcessed data for {len(impact_data)} food items")

    # Show some examples
    logger.info("\nExample impact data:")
    examples = ["beef", "chicken", "lentils", "rice", "milk"]

    for food in examples:
        if food in impact_data:
            data = impact_data[food]
            env = data["environmental"]
            profile = data["sustainability_profile"]

            logger.info(f"\n{food.upper()}:")
            logger.info(f"  GHG: {env.get('ghg_kg_co2e_per_kg', 'N/A')} kg CO₂e/kg")
            logger.info(f"  Land: {env.get('land_m2_per_kg', 'N/A')} m²/kg")
            logger.info(f"  Water: {env.get('water_L_per_kg', 'N/A')} L/kg")
            logger.info(f"  Impact: {profile['impact_category']} {profile['ghg_visual']}")
            logger.info(f"  Planet Score: {profile['planet_score']}/10")

    # Test swap suggestions
    logger.info("\n\nTesting swap suggestions for beef:")
    swaps = impact_service.suggest_sustainable_swaps("beef")
    for swap in swaps[:3]:
        logger.info(
            f"  → {swap['ingredient']}: -{swap['co2_savings_per_kg']} kg CO₂e/kg ({swap['percentage_reduction']}% reduction)"
        )

    logger.info("\nData download and processing complete!")
    logger.info(f"Data saved to: data/environmental_impact/")


if __name__ == "__main__":
    main()
