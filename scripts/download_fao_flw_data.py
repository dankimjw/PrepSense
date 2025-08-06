#!/usr/bin/env python3
"""
Script to process FAO Food Loss and Waste data after manual download
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.services.food_waste_service import get_food_waste_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS = """
FAO Food Loss and Waste Database Download Instructions:

1. Go to: https://www.fao.org/platform-food-loss-waste/flw-data/
2. Click on the "Database" tab
3. Apply filters (recommended):
   - Stage: Select "Consumer" and "Retail"
   - Time period: Last 10 years for most recent data
   - Or download all data for comprehensive coverage
4. Click "Download Data" button
5. Save the CSV file as: data/food_loss_waste/fao_flw_data.csv

The download should be approximately 4MB for the full dataset.
"""


def main():
    """Process FAO FLW data"""

    # Expected file location
    csv_path = Path("data/food_loss_waste/fao_flw_data.csv")

    if not csv_path.exists():
        print(INSTRUCTIONS)
        print(f"\n❌ File not found at: {csv_path}")
        print("\nPlease download the data manually and place it at the path above.")
        return

    print("✅ FAO FLW data file found!")

    # Process the data
    try:
        waste_service = get_food_waste_service()

        print("Processing FAO FLW data...")
        df = waste_service.download_flw_data(str(csv_path))

        if df.empty:
            print("❌ Failed to process data")
            return

        print(f"✅ Successfully processed {len(df)} commodity loss rates")

        # Show some statistics
        print("\nSample loss rates by commodity:")
        print("-" * 50)

        # Try to show some examples if data is available
        sample_commodities = ["Tomatoes", "Apples", "Rice", "Beef", "Milk"]
        for commodity in sample_commodities:
            matches = df[df["commodity_name"].str.contains(commodity, case=False, na=False)]
            if not matches.empty:
                consumer_data = matches[matches["stage"].str.lower() == "consumer"]
                if not consumer_data.empty:
                    median_loss = consumer_data.iloc[0]["median_loss_pct"]
                    print(f"{commodity}: {median_loss:.1f}% typical consumer waste")

        print("\n✅ Data processing complete!")
        print("The processed data is saved at: data/food_loss_waste/processed_flw_data.json")

    except Exception as e:
        print(f"❌ Error processing data: {str(e)}")
        logger.error(f"Processing error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
