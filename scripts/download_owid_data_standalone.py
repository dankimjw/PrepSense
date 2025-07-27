#!/usr/bin/env python3
"""Standalone script to download OWID environmental impact data"""

import os
import json
import logging
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OWID data sources
OWID_DATASETS = {
    'ghg': 'https://ourworldindata.org/grapher/ghg-per-kg-poore.csv',
    'land': 'https://ourworldindata.org/grapher/land-use-per-kg-poore.csv',
    'water': 'https://ourworldindata.org/grapher/freshwater-withdrawals-per-kg-poore.csv',
    'eutrophying': 'https://ourworldindata.org/grapher/eutrophying-emissions-per-kg-poore.csv',
    'supply_chain': 'https://ourworldindata.org/grapher/food-emissions-supply-chain.csv'
}

# Mapping between OWID product names and common food names
OWID_TO_FOOD_MAPPING = {
    'Beef (beef herd)': ['beef', 'ground_beef', 'steak', 'beef_roast'],
    'Poultry Meat': ['chicken', 'chicken_breast', 'chicken_thigh', 'turkey'],
    'Eggs': ['eggs', 'egg'],
    'Milk': ['milk', 'whole_milk', 'skim_milk'],
    'Cheese': ['cheese', 'cheddar', 'mozzarella'],
    'Tofu': ['tofu'],
    'Other Pulses': ['lentils', 'chickpeas', 'black_beans'],
    'Rice': ['rice', 'white_rice', 'brown_rice'],
    'Wheat & Rye': ['wheat', 'bread', 'pasta', 'flour'],
    'Potatoes': ['potatoes', 'potato'],
    'Tomatoes': ['tomatoes', 'tomato'],
    'Apples': ['apples', 'apple'],
    'Bananas': ['bananas', 'banana']
}


def download_datasets(data_dir: Path):
    """Download OWID datasets"""
    data_dir.mkdir(parents=True, exist_ok=True)
    
    for dataset_name, url in OWID_DATASETS.items():
        cache_file = data_dir / f'{dataset_name}_owid.csv'
        
        try:
            logger.info(f"Downloading {dataset_name} data from OWID...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to file
            with open(cache_file, 'w') as f:
                f.write(response.text)
            
            logger.info(f"Successfully downloaded {dataset_name} data")
            
        except Exception as e:
            logger.error(f"Error downloading {dataset_name}: {str(e)}")


def process_data(data_dir: Path):
    """Process downloaded data into usable format"""
    
    processed_data = {}
    
    # Load GHG data as primary dataset
    ghg_file = data_dir / 'ghg_owid.csv'
    if not ghg_file.exists():
        logger.error("GHG data not found!")
        return
    
    ghg_df = pd.read_csv(ghg_file)
    logger.info(f"Loaded GHG data with {len(ghg_df)} rows")
    
    # Process each OWID product
    for owid_product, food_items in OWID_TO_FOOD_MAPPING.items():
        logger.info(f"Processing {owid_product}...")
        
        # Find the product in the dataset
        mask = ghg_df['Entity'] == owid_product
        if not mask.any():
            logger.warning(f"Could not find {owid_product} in GHG data")
            continue
        
        # Get the most recent value
        product_data = ghg_df[mask].sort_values('Year', ascending=False).iloc[0]
        
        # Extract GHG value (last column is usually the value)
        ghg_value = float(product_data.iloc[-1]) if pd.notna(product_data.iloc[-1]) else None
        
        # Create data for each mapped food item
        for food_item in food_items:
            processed_data[food_item] = {
                'owid_product': owid_product,
                'environmental': {
                    'ghg_kg_co2e_per_kg': ghg_value
                },
                'sustainability_profile': {
                    'impact_category': categorize_impact(ghg_value),
                    'planet_score': calculate_planet_score(ghg_value),
                    'ghg_visual': get_impact_visual(ghg_value)
                }
            }
    
    # Save processed data
    output_file = data_dir / 'processed_impact_data.json'
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2)
    
    logger.info(f"Processed data for {len(processed_data)} food items")
    logger.info(f"Saved to: {output_file}")
    
    # Print examples
    print("\n--- Example Impact Data ---")
    for food in ['beef', 'chicken', 'lentils', 'rice', 'milk']:
        if food in processed_data:
            data = processed_data[food]
            ghg = data['environmental']['ghg_kg_co2e_per_kg']
            category = data['sustainability_profile']['impact_category']
            visual = data['sustainability_profile']['ghg_visual']
            print(f"{food.upper()}: {ghg} kg CO₂e/kg - {category} impact {visual}")


def categorize_impact(ghg):
    """Categorize impact level based on GHG emissions"""
    if ghg is None:
        return 'unknown'
    elif ghg < 1:
        return 'very_low'
    elif ghg < 3:
        return 'low'
    elif ghg < 7:
        return 'medium'
    elif ghg < 15:
        return 'high'
    else:
        return 'very_high'


def calculate_planet_score(ghg):
    """Calculate planet score (1-10) based on GHG emissions"""
    if ghg is None:
        return 5
    elif ghg < 1:
        return 9
    elif ghg < 3:
        return 7
    elif ghg < 7:
        return 5
    elif ghg < 15:
        return 3
    else:
        return 1


def get_impact_visual(ghg):
    """Get visual representation of impact"""
    category = categorize_impact(ghg)
    visuals = {
        'very_low': '🟢',
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'very_high': '🔴',
        'unknown': '⚪'
    }
    return visuals.get(category, '⚪')


def main():
    """Main function"""
    # Create data directory
    data_dir = Path('data/environmental_impact')
    
    logger.info("Starting OWID data download...")
    download_datasets(data_dir)
    
    logger.info("\nProcessing data...")
    process_data(data_dir)
    
    logger.info("\nDone! Data saved to data/environmental_impact/")


if __name__ == "__main__":
    main()