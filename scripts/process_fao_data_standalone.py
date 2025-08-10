#!/usr/bin/env python3
"""
Standalone script to process FAO FLW data without backend dependencies
"""

import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def process_fao_data():
    """Process FAO FLW data and create mapping"""

    # Paths
    input_file = Path("data/food_loss_waste/fao_flw_data.csv")
    output_dir = Path("data/food_loss_waste")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        logger.error(f"FAO data file not found at {input_file}")
        return

    logger.info("Reading FAO FLW data...")

    # Read CSV with various encodings
    for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            logger.info(f"Successfully read file with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    else:
        logger.error("Could not read file with any encoding")
        return

    logger.info(f"Loaded {len(df)} rows")
    logger.info(f"Columns: {list(df.columns)}")

    # Print first few rows to understand structure
    print("\nFirst 5 rows of data:")
    print(df.head())

    # Identify column names (they might vary)
    # Common patterns: 'loss_percentage', 'loss_%', 'percentage', 'value'
    loss_col = None
    for col in df.columns:
        if any(term in col.lower() for term in ["loss", "waste", "percentage", "value"]):
            logger.info(f"Found potential loss column: {col}")
            if loss_col is None:
                loss_col = col

    # Identify stage column
    stage_col = None
    for col in df.columns:
        if "stage" in col.lower() or "fsc_location" in col.lower():
            stage_col = col
            logger.info(f"Found stage column: {col}")
            break

    # Identify commodity column
    commodity_col = None
    for col in df.columns:
        if any(term in col.lower() for term in ["commodity", "food", "product"]):
            commodity_col = col
            logger.info(f"Found commodity column: {col}")
            break

    if not all([loss_col, stage_col, commodity_col]):
        logger.error(
            f"Could not identify required columns. Found: loss={loss_col}, stage={stage_col}, commodity={commodity_col}"
        )
        return

    # Filter for consumer and retail stages
    logger.info("Filtering for consumer and retail stages...")
    consumer_retail = df[
        df[stage_col].str.lower().isin(["consumer", "retail", "consumption", "household"])
    ]
    logger.info(f"Found {len(consumer_retail)} consumer/retail entries")

    # Group by commodity and calculate statistics
    logger.info("Calculating loss statistics by commodity...")

    # Convert loss values to numeric
    consumer_retail[loss_col] = pd.to_numeric(consumer_retail[loss_col], errors="coerce")

    # Group and calculate stats
    grouped = (
        consumer_retail.groupby(commodity_col)[loss_col]
        .agg(["mean", "median", "min", "max", "count"])
        .round(2)
    )

    # Sort by median loss rate
    grouped = grouped.sort_values("median", ascending=False)

    print("\nTop 20 commodities by median loss rate:")
    print(grouped.head(20))

    # Create processed data for our system
    processed_data = []
    for commodity, stats in grouped.iterrows():
        if pd.notna(stats["median"]):
            processed_data.append(
                {
                    "commodity_name": commodity,
                    "median_loss_pct": float(stats["median"]),
                    "mean_loss_pct": float(stats["mean"]) if pd.notna(stats["mean"]) else None,
                    "min_loss_pct": float(stats["min"]) if pd.notna(stats["min"]) else None,
                    "max_loss_pct": float(stats["max"]) if pd.notna(stats["max"]) else None,
                    "observations": int(stats["count"]),
                    "stage": "consumer",
                }
            )

    # Save processed data
    output_file = output_dir / "processed_flw_data.json"
    with open(output_file, "w") as f:
        json.dump(processed_data, f, indent=2)

    logger.info(f"Saved processed data to {output_file}")

    # Create simple mapping for common foods
    food_mappings = {
        # Vegetables
        "tomatoes": ["tomato", "tomatoes", "cherry tomatoes", "roma tomatoes"],
        "lettuce": ["lettuce", "romaine", "iceberg", "mixed greens"],
        "spinach": ["spinach", "baby spinach"],
        "carrots": ["carrots", "carrot", "baby carrots"],
        "potatoes": ["potatoes", "potato", "sweet potatoes"],
        "onions": ["onions", "onion", "red onion", "white onion"],
        # Fruits
        "apples": ["apples", "apple", "granny smith", "red delicious"],
        "bananas": ["bananas", "banana"],
        "berries": ["strawberries", "blueberries", "raspberries", "blackberries"],
        "citrus fruit": ["oranges", "lemons", "limes", "grapefruit"],
        # Proteins
        "beef": ["beef", "ground beef", "steak", "roast"],
        "poultry meat": ["chicken", "turkey", "chicken breast", "chicken thighs"],
        "pork": ["pork", "bacon", "ham", "pork chops"],
        "fish": ["fish", "salmon", "tuna", "cod", "tilapia"],
        # Dairy
        "milk": ["milk", "whole milk", "skim milk", "2% milk"],
        "cheese": ["cheese", "cheddar", "mozzarella", "swiss"],
        "yogurt": ["yogurt", "greek yogurt"],
        # Grains
        "bread": ["bread", "whole wheat bread", "white bread"],
        "rice": ["rice", "white rice", "brown rice"],
        "pasta": ["pasta", "spaghetti", "penne", "macaroni"],
    }

    # Create reverse mapping with loss rates
    item_loss_rates = {}
    for _, row in grouped.iterrows():
        commodity_lower = str(row.name).lower()

        # Direct mapping
        for category, items in food_mappings.items():
            if category in commodity_lower or commodity_lower in category:
                for item in items:
                    item_loss_rates[item] = {
                        "loss_rate": float(row["median"]) / 100,  # Convert to decimal
                        "source_commodity": row.name,
                        "observations": int(row["count"]),
                    }

    # Save mapping
    mapping_file = output_dir / "food_loss_mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(item_loss_rates, f, indent=2)

    logger.info(f"Saved food mapping to {mapping_file}")
    logger.info(f"Processed {len(processed_data)} commodities")
    logger.info(f"Created mappings for {len(item_loss_rates)} food items")

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total commodities processed: {len(processed_data)}")
    print(f"Average loss rate: {grouped['median'].mean():.1f}%")
    print(f"Highest loss rate: {grouped['median'].max():.1f}% ({grouped['median'].idxmax()})")
    print(f"Lowest loss rate: {grouped['median'].min():.1f}% ({grouped['median'].idxmin()})")


if __name__ == "__main__":
    process_fao_data()
