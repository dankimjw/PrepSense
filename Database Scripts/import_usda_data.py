#!/usr/bin/env python3
"""
Import USDA FoodData Central CSV files into PrepSense database.
This script handles the large CSV files efficiently using chunked reading.
"""

import csv
import json
import zipfile
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class USDADataImporter:
    def __init__(self, db_url: str, zip_path: str):
        self.db_url = db_url
        self.zip_path = Path(zip_path)
        self.conn: Optional[asyncpg.Connection] = None
        
    async def connect(self):
        """Establish database connection."""
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("Connected to database")
        
    async def disconnect(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")
    
    async def import_categories(self, csv_content: str):
        """Import food categories."""
        logger.info("Importing food categories...")
        
        reader = csv.DictReader(csv_content.splitlines())
        categories = []
        
        for row in reader:
            categories.append((
                int(row['id']),
                row['code'],
                row['description']
            ))
        
        await self.conn.executemany(
            """
            INSERT INTO usda_food_categories (id, code, description)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                description = EXCLUDED.description
            """,
            categories
        )
        logger.info(f"Imported {len(categories)} categories")
    
    async def import_measure_units(self, csv_content: str):
        """Import measure units."""
        logger.info("Importing measure units...")
        
        reader = csv.DictReader(csv_content.splitlines())
        units = []
        
        # Categorize units by type
        unit_types = {
            'volume': ['cup', 'tablespoon', 'teaspoon', 'liter', 'milliliter', 
                      'fl oz', 'gallon', 'pint', 'quart'],
            'weight': ['lb', 'oz', 'g', 'kg'],
            'count': ['piece', 'pieces', 'each', 'unit'],
            'portion': ['serving', 'scoop', 'slice', 'slices', 'strip', 'patty'],
            'package': ['can', 'bottle', 'box', 'container', 'package', 'bag', 'jar']
        }
        
        def get_unit_type(name: str) -> str:
            for unit_type, units_list in unit_types.items():
                if name.lower() in units_list:
                    return unit_type
            return 'other'
        
        for row in reader:
            units.append((
                int(row['id']),
                row['name'],
                row['name'][:5] if len(row['name']) > 5 else row['name'],  # abbreviation
                get_unit_type(row['name'])
            ))
        
        await self.conn.executemany(
            """
            INSERT INTO usda_measure_units (id, name, abbreviation, unit_type)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                abbreviation = EXCLUDED.abbreviation,
                unit_type = EXCLUDED.unit_type
            """,
            units
        )
        logger.info(f"Imported {len(units)} measure units")
    
    async def import_nutrients(self, csv_content: str):
        """Import nutrients reference data."""
        logger.info("Importing nutrients...")
        
        reader = csv.DictReader(csv_content.splitlines())
        nutrients = []
        
        for row in reader:
            nutrients.append((
                int(row['id']),
                row['name'],
                row['unit_name'],
                row.get('nutrient_nbr', ''),
                int(float(row.get('rank', 0))) if row.get('rank') else None
            ))
        
        await self.conn.executemany(
            """
            INSERT INTO usda_nutrients (id, name, unit_name, nutrient_nbr, rank)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                unit_name = EXCLUDED.unit_name,
                nutrient_nbr = EXCLUDED.nutrient_nbr,
                rank = EXCLUDED.rank
            """,
            nutrients
        )
        logger.info(f"Imported {len(nutrients)} nutrients")
    
    async def import_foods_chunked(self, zip_file: zipfile.ZipFile, chunk_size: int = 1000):
        """Import foods in chunks to handle large files."""
        logger.info("Importing foods (this may take a while)...")
        
        # First, import generic foods
        with zip_file.open('FoodData_Central_csv_2025-04-24/food.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            chunk = []
            total_imported = 0
            
            for row in tqdm(reader, desc="Processing foods"):
                chunk.append((
                    int(row['fdc_id']),
                    row['description'],
                    row['data_type'],
                    int(row['food_category_id']) if row.get('food_category_id') else None,
                    datetime.strptime(row['publication_date'], '%m/%d/%Y').date() 
                        if row.get('publication_date') else None
                ))
                
                if len(chunk) >= chunk_size:
                    await self._insert_foods(chunk)
                    total_imported += len(chunk)
                    chunk = []
            
            # Insert remaining
            if chunk:
                await self._insert_foods(chunk)
                total_imported += len(chunk)
                
        logger.info(f"Imported {total_imported} foods")
        
        # Import branded foods with additional fields
        await self._import_branded_foods(zip_file, chunk_size)
    
    async def _insert_foods(self, foods: List[tuple]):
        """Insert food records."""
        await self.conn.executemany(
            """
            INSERT INTO usda_foods (fdc_id, description, data_type, food_category_id, publication_date)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (fdc_id) DO UPDATE SET
                description = EXCLUDED.description,
                data_type = EXCLUDED.data_type,
                food_category_id = EXCLUDED.food_category_id,
                publication_date = EXCLUDED.publication_date,
                updated_at = CURRENT_TIMESTAMP
            """,
            foods
        )
    
    async def _import_branded_foods(self, zip_file: zipfile.ZipFile, chunk_size: int = 1000):
        """Import branded foods with barcode and brand information."""
        logger.info("Importing branded foods...")
        
        with zip_file.open('FoodData_Central_csv_2025-04-24/branded_food.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            chunk = []
            total_imported = 0
            
            for row in tqdm(reader, desc="Processing branded foods"):
                # Clean up barcode - remove any leading zeros
                barcode = row.get('gtin_upc', '').lstrip('0') if row.get('gtin_upc') else None
                
                chunk.append((
                    int(row['fdc_id']),
                    row.get('brand_owner', ''),
                    row.get('brand_name', ''),
                    barcode,
                    row.get('ingredients', ''),
                    float(row['serving_size']) if row.get('serving_size') else None,
                    row.get('serving_size_unit', '')
                ))
                
                if len(chunk) >= chunk_size:
                    await self._update_branded_foods(chunk)
                    total_imported += len(chunk)
                    chunk = []
            
            if chunk:
                await self._update_branded_foods(chunk)
                total_imported += len(chunk)
                
        logger.info(f"Updated {total_imported} branded foods")
    
    async def _update_branded_foods(self, foods: List[tuple]):
        """Update food records with branded food information."""
        await self.conn.executemany(
            """
            UPDATE usda_foods SET
                brand_owner = $2,
                brand_name = $3,
                gtin_upc = $4,
                ingredients = $5,
                serving_size = $6,
                serving_size_unit = $7,
                updated_at = CURRENT_TIMESTAMP
            WHERE fdc_id = $1
            """,
            foods
        )
    
    async def import_key_nutrients(self, zip_file: zipfile.ZipFile, chunk_size: int = 5000):
        """Import only key nutrients to save space."""
        logger.info("Importing key nutrients...")
        
        # Key nutrient IDs from USDA database
        key_nutrients = {
            1008: 'calories',
            1003: 'protein',
            1004: 'total_fat',
            1005: 'carbohydrate',
            1079: 'fiber',
            1235: 'sugar',
            1093: 'sodium',
            1087: 'calcium',
            1089: 'iron',
            1090: 'magnesium',
            1092: 'potassium',
            1104: 'vitamin_a',
            1162: 'vitamin_c',
            1114: 'vitamin_d',
            1109: 'vitamin_e'
        }
        
        with zip_file.open('FoodData_Central_csv_2025-04-24/food_nutrient.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            chunk = []
            total_imported = 0
            
            for row in tqdm(reader, desc="Processing nutrients"):
                nutrient_id = int(row['nutrient_id'])
                
                # Only import key nutrients
                if nutrient_id in key_nutrients:
                    chunk.append((
                        int(row['fdc_id']),
                        nutrient_id,
                        float(row['amount']) if row.get('amount') else 0.0
                    ))
                    
                    if len(chunk) >= chunk_size:
                        await self._insert_nutrients(chunk)
                        total_imported += len(chunk)
                        chunk = []
            
            if chunk:
                await self._insert_nutrients(chunk)
                total_imported += len(chunk)
                
        logger.info(f"Imported {total_imported} nutrient values")
    
    async def _insert_nutrients(self, nutrients: List[tuple]):
        """Insert nutrient records."""
        await self.conn.executemany(
            """
            INSERT INTO usda_food_nutrients (fdc_id, nutrient_id, amount)
            VALUES ($1, $2, $3)
            ON CONFLICT (fdc_id, nutrient_id) DO UPDATE SET
                amount = EXCLUDED.amount
            """,
            nutrients
        )
    
    async def run_import(self):
        """Run the full import process."""
        try:
            await self.connect()
            
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                # Import reference tables first
                logger.info("Starting USDA data import...")
                
                # Categories
                with zip_file.open('FoodData_Central_csv_2025-04-24/food_category.csv') as f:
                    content = f.read().decode('utf-8')
                    await self.import_categories(content)
                
                # Measure units
                with zip_file.open('FoodData_Central_csv_2025-04-24/measure_unit.csv') as f:
                    content = f.read().decode('utf-8')
                    await self.import_measure_units(content)
                
                # Nutrients
                with zip_file.open('FoodData_Central_csv_2025-04-24/nutrient.csv') as f:
                    content = f.read().decode('utf-8')
                    await self.import_nutrients(content)
                
                # Import main data
                await self.import_foods_chunked(zip_file)
                await self.import_key_nutrients(zip_file)
                
                logger.info("Import completed successfully!")
                
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')
    
    # Build database URL
    db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE')}"
    
    # Path to USDA data zip file
    zip_path = "/Users/danielkim/_Capstone/PrepSense/Food Data/FoodData_Central_AllData/FoodData_Central_csv_2025-04-24.zip"
    
    # Create importer and run
    importer = USDADataImporter(db_url, zip_path)
    await importer.run_import()


if __name__ == "__main__":
    asyncio.run(main())