#!/usr/bin/env python3
"""
Script to download USDA nutrition database and load into PostgreSQL or GCS.
"""

import os
import sys
import csv
import json
import zipfile
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import execute_batch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_database_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# USDA Download URLs (as of 2024)
USDA_URLS = {
    "foundation": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2024-10-31.zip",
    "sr_legacy": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2024-10-31.zip",
    "branded": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_branded_food_csv_2024-10-31.zip"
}

# Nutrient IDs we care about (from USDA nutrient definitions)
NUTRIENT_MAPPING = {
    1008: "calories",          # Energy (kcal)
    1003: "protein",           # Protein (g)
    1004: "total_fat",         # Total lipid (g)
    1005: "carbohydrates",     # Carbohydrate (g)
    1079: "fiber",             # Fiber, total dietary (g)
    2000: "sugar",             # Sugars, total (g)
    1258: "saturated_fat",     # Fatty acids, saturated (g)
    1257: "trans_fat",         # Fatty acids, trans (g)
    1253: "cholesterol",       # Cholesterol (mg)
    1093: "sodium",            # Sodium (mg)
    1087: "calcium",           # Calcium (mg)
    1089: "iron",              # Iron (mg)
    1090: "magnesium",         # Magnesium (mg)
    1091: "phosphorus",        # Phosphorus (mg)
    1092: "potassium",         # Potassium (mg)
    1095: "zinc",              # Zinc (mg)
    1098: "copper",            # Copper (mg)
    1103: "selenium",          # Selenium (µg)
    1162: "vitamin_c",         # Vitamin C (mg)
    1106: "vitamin_a",         # Vitamin A, RAE (µg)
    1114: "vitamin_d",         # Vitamin D (D2 + D3) (µg)
    1109: "vitamin_e",         # Vitamin E (mg)
    1183: "vitamin_k",         # Vitamin K (µg)
    1165: "thiamin",           # Thiamin (mg)
    1166: "riboflavin",        # Riboflavin (mg)
    1167: "niacin",            # Niacin (mg)
    1175: "vitamin_b6",        # Vitamin B-6 (mg)
    1177: "folate",            # Folate, total (µg)
    1178: "vitamin_b12",       # Vitamin B-12 (µg)
}

class USDANutritionLoader:
    def __init__(self, data_dir: str = "./usda_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def download_dataset(self, dataset: str = "foundation"):
        """Download USDA dataset."""
        url = USDA_URLS.get(dataset)
        if not url:
            raise ValueError(f"Unknown dataset: {dataset}")
            
        filename = url.split("/")[-1]
        filepath = self.data_dir / filename
        
        if filepath.exists():
            logger.info(f"Dataset already downloaded: {filepath}")
            return filepath
            
        logger.info(f"Downloading {dataset} dataset from {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"Downloaded: {filepath}")
        return filepath
        
    def extract_dataset(self, zip_path: Path):
        """Extract USDA dataset."""
        extract_dir = self.data_dir / zip_path.stem
        
        if extract_dir.exists():
            logger.info(f"Dataset already extracted: {extract_dir}")
            return extract_dir
            
        logger.info(f"Extracting {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        logger.info(f"Extracted to: {extract_dir}")
        return extract_dir
        
    def load_to_postgresql(self, extract_dir: Path):
        """Load USDA data into PostgreSQL."""
        logger.info("Loading data into PostgreSQL")
        
        # Get database connection
        db_url = get_database_url()
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        try:
            # Create tables
            logger.info("Creating USDA nutrition tables")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usda_foods (
                    fdc_id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    food_category TEXT,
                    data_type TEXT,
                    publication_date DATE,
                    brand_name TEXT,
                    brand_owner TEXT,
                    ingredients TEXT,
                    serving_size DECIMAL(10,2),
                    serving_size_unit TEXT,
                    household_serving_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS usda_nutrients (
                    id SERIAL PRIMARY KEY,
                    fdc_id INTEGER REFERENCES usda_foods(fdc_id),
                    nutrient_id INTEGER NOT NULL,
                    nutrient_name TEXT NOT NULL,
                    nutrient_number TEXT,
                    unit TEXT NOT NULL,
                    amount DECIMAL(15,3),
                    data_points INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS usda_nutrient_definitions (
                    nutrient_id INTEGER PRIMARY KEY,
                    nutrient_name TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    nutrient_number TEXT,
                    rank INTEGER
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_food_description ON usda_foods(description);
                CREATE INDEX IF NOT EXISTS idx_food_category ON usda_foods(food_category);
                CREATE INDEX IF NOT EXISTS idx_nutrients_fdc ON usda_nutrients(fdc_id);
                CREATE INDEX IF NOT EXISTS idx_nutrients_id ON usda_nutrients(nutrient_id);
                
                -- Create text search index for food descriptions
                CREATE INDEX IF NOT EXISTS idx_food_description_trgm 
                ON usda_foods USING gin(description gin_trgm_ops);
            """)
            
            # Load food data
            food_file = extract_dir / "food.csv"
            if food_file.exists():
                logger.info(f"Loading foods from {food_file}")
                with open(food_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    foods = []
                    for row in reader:
                        foods.append((
                            int(row['fdc_id']),
                            row.get('description', ''),
                            row.get('food_category', ''),
                            row.get('data_type', ''),
                            row.get('publication_date'),
                            row.get('brand_name'),
                            row.get('brand_owner'),
                            row.get('ingredients'),
                            float(row['serving_size']) if row.get('serving_size') else None,
                            row.get('serving_size_unit'),
                            row.get('household_serving_fulltext')
                        ))
                        
                        if len(foods) >= 1000:
                            execute_batch(cur, """
                                INSERT INTO usda_foods (
                                    fdc_id, description, food_category, data_type,
                                    publication_date, brand_name, brand_owner, ingredients,
                                    serving_size, serving_size_unit, household_serving_text
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (fdc_id) DO NOTHING
                            """, foods)
                            foods = []
                            
                    # Insert remaining foods
                    if foods:
                        execute_batch(cur, """
                            INSERT INTO usda_foods (
                                fdc_id, description, food_category, data_type,
                                publication_date, brand_name, brand_owner, ingredients,
                                serving_size, serving_size_unit, household_serving_text
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (fdc_id) DO NOTHING
                        """, foods)
                        
                logger.info("Foods loaded successfully")
            
            # Load nutrient data
            nutrient_file = extract_dir / "food_nutrient.csv"
            if nutrient_file.exists():
                logger.info(f"Loading nutrients from {nutrient_file}")
                with open(nutrient_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    nutrients = []
                    for row in reader:
                        nutrient_id = int(row.get('nutrient_id', 0))
                        
                        # Only load nutrients we care about
                        if nutrient_id in NUTRIENT_MAPPING:
                            nutrients.append((
                                int(row['fdc_id']),
                                nutrient_id,
                                row.get('nutrient_name', ''),
                                row.get('nutrient_number', ''),
                                row.get('unit', ''),
                                float(row.get('amount', 0)),
                                int(row.get('data_points', 0)) if row.get('data_points') else None
                            ))
                            
                            if len(nutrients) >= 1000:
                                execute_batch(cur, """
                                    INSERT INTO usda_nutrients (
                                        fdc_id, nutrient_id, nutrient_name, nutrient_number,
                                        unit, amount, data_points
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT DO NOTHING
                                """, nutrients)
                                nutrients = []
                                
                    # Insert remaining nutrients
                    if nutrients:
                        execute_batch(cur, """
                            INSERT INTO usda_nutrients (
                                fdc_id, nutrient_id, nutrient_name, nutrient_number,
                                unit, amount, data_points
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, nutrients)
                        
                logger.info("Nutrients loaded successfully")
            
            # Create materialized view for fast lookups
            logger.info("Creating materialized view for fast nutrition lookups")
            cur.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS usda_food_nutrition AS
                SELECT 
                    f.fdc_id,
                    f.description,
                    f.food_category,
                    f.brand_name,
                    f.serving_size,
                    f.serving_size_unit,
                    jsonb_object_agg(
                        COALESCE(
                            CASE n.nutrient_id
                                WHEN 1008 THEN 'calories'
                                WHEN 1003 THEN 'protein'
                                WHEN 1004 THEN 'total_fat'
                                WHEN 1005 THEN 'carbohydrates'
                                WHEN 1079 THEN 'fiber'
                                WHEN 2000 THEN 'sugar'
                                WHEN 1093 THEN 'sodium'
                                WHEN 1087 THEN 'calcium'
                                WHEN 1089 THEN 'iron'
                                WHEN 1162 THEN 'vitamin_c'
                                ELSE n.nutrient_name
                            END,
                            n.nutrient_name
                        ),
                        n.amount
                    ) AS nutrients
                FROM usda_foods f
                LEFT JOIN usda_nutrients n ON f.fdc_id = n.fdc_id
                WHERE n.nutrient_id IN (1008, 1003, 1004, 1005, 1079, 2000, 1093, 1087, 1089, 1162)
                GROUP BY f.fdc_id, f.description, f.food_category, f.brand_name, 
                         f.serving_size, f.serving_size_unit;
                
                CREATE INDEX IF NOT EXISTS idx_food_nutrition_description 
                ON usda_food_nutrition(description);
            """)
            
            conn.commit()
            logger.info("USDA nutrition database loaded successfully!")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error loading data: {e}")
            raise
        finally:
            cur.close()
            conn.close()
            
    def generate_gcs_upload_script(self, extract_dir: Path):
        """Generate script to upload to Google Cloud Storage."""
        script_path = self.data_dir / "upload_to_gcs.sh"
        
        with open(script_path, 'w') as f:
            f.write(f"""#!/bin/bash
# Upload USDA nutrition data to Google Cloud Storage

BUCKET="gs://prepsense-data/usda-nutrition"

echo "Creating GCS bucket if not exists..."
gsutil mb -p prepsense-436806 $BUCKET 2>/dev/null || true

echo "Uploading CSV files..."
gsutil -m cp -r {extract_dir}/*.csv $BUCKET/

echo "Setting public read access..."
gsutil iam ch allUsers:objectViewer $BUCKET

echo "Upload complete!"
echo "Files available at: $BUCKET"
""")
        
        script_path.chmod(0o755)
        logger.info(f"GCS upload script created: {script_path}")
        
def main():
    """Main function to download and load USDA data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and load USDA nutrition database")
    parser.add_argument("--dataset", default="foundation", 
                        choices=["foundation", "sr_legacy", "branded"],
                        help="Which USDA dataset to download")
    parser.add_argument("--load-postgres", action="store_true",
                        help="Load data into PostgreSQL")
    parser.add_argument("--generate-gcs-script", action="store_true",
                        help="Generate GCS upload script")
    parser.add_argument("--data-dir", default="./usda_data",
                        help="Directory to store downloaded data")
    
    args = parser.parse_args()
    
    loader = USDANutritionLoader(args.data_dir)
    
    # Download and extract
    zip_path = loader.download_dataset(args.dataset)
    extract_dir = loader.extract_dataset(zip_path)
    
    # Load into PostgreSQL
    if args.load_postgres:
        loader.load_to_postgresql(extract_dir)
        
    # Generate GCS upload script
    if args.generate_gcs_script:
        loader.generate_gcs_upload_script(extract_dir)
        
    logger.info("Done!")

if __name__ == "__main__":
    main()