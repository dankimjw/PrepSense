#!/usr/bin/env python3
"""
Fixed USDA FoodData Central CSV import script.
Handles category name to ID mapping correctly.
"""

import csv
import json
import zipfile
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Optional, Any
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from various formats."""
    if not date_str:
        return None
    
    # Try different date formats
    formats = [
        '%Y-%m-%d',  # 2020-10-30
        '%m/%d/%Y',  # 10/30/2020
        '%d/%m/%Y',  # 30/10/2020 (just in case)
        '%Y/%m/%d',  # 2020/10/30
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If no format matches, log and return None
    logger.warning(f"Could not parse date: {date_str}")
    return None

class USDADataImporter:
    def __init__(self, db_url: str, zip_path: str):
        self.db_url = db_url
        self.zip_path = Path(zip_path)
        self.conn: Optional[asyncpg.Connection] = None
        self.category_map: Dict[str, int] = {}  # Maps category names to IDs
        
    async def connect(self):
        """Establish database connection."""
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("Connected to database")
        
    async def disconnect(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")
    
    async def build_category_map(self):
        """Build mapping of category names to IDs from database."""
        logger.info("Building category name to ID mapping...")
        
        rows = await self.conn.fetch("""
            SELECT id, description FROM usda_food_categories
        """)
        
        for row in rows:
            self.category_map[row['description']] = row['id']
        
        logger.info(f"Built mapping for {len(self.category_map)} categories")
    
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
            name_lower = name.lower()
            for unit_type, units_list in unit_types.items():
                if any(unit in name_lower for unit in units_list):
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
        
        # Build category mapping first
        await self.build_category_map()
        
        # Import generic foods
        with zip_file.open('FoodData_Central_csv_2025-04-24/food.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            chunk = []
            total_imported = 0
            skipped = 0
            
            for row in tqdm(reader, desc="Processing foods"):
                # Get category ID from name
                category_name = row.get('food_category_id', '').strip()
                category_id = None
                if category_name and category_name in self.category_map:
                    category_id = self.category_map[category_name]
                elif category_name:
                    # Skip foods with unknown categories for now
                    skipped += 1
                    continue
                
                chunk.append((
                    int(row['fdc_id']),
                    row['description'],
                    row['data_type'],
                    category_id,
                    parse_date(row.get('publication_date', ''))
                ))
                
                if len(chunk) >= chunk_size:
                    await self._insert_foods(chunk)
                    total_imported += len(chunk)
                    chunk = []
            
            # Insert remaining
            if chunk:
                await self._insert_foods(chunk)
                total_imported += len(chunk)
            
            logger.info(f"Imported {total_imported} foods (skipped {skipped} with unknown categories)")
        
        # Import branded foods for additional data
        logger.info("Importing branded food details...")
        await self._import_branded_foods(zip_file, chunk_size)
    
    async def _insert_foods(self, chunk: List[tuple]):
        """Insert a chunk of foods."""
        await self.conn.executemany(
            """
            INSERT INTO usda_foods (fdc_id, description, data_type, food_category_id, publication_date)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (fdc_id) DO UPDATE SET
                description = EXCLUDED.description,
                data_type = EXCLUDED.data_type,
                food_category_id = EXCLUDED.food_category_id,
                publication_date = EXCLUDED.publication_date
            """,
            chunk
        )
    
    async def _import_branded_foods(self, zip_file: zipfile.ZipFile, chunk_size: int = 1000):
        """Import branded food specific data."""
        try:
            with zip_file.open('FoodData_Central_csv_2025-04-24/branded_food.csv') as f:
                reader = csv.DictReader(line.decode('utf-8') for line in f)
                
                updates = []
                total_updated = 0
                
                for row in tqdm(reader, desc="Processing branded foods"):
                    updates.append((
                        row.get('brand_owner', ''),
                        row.get('brand_name', ''),
                        row.get('gtin_upc', ''),
                        row.get('ingredients', ''),
                        float(row['serving_size']) if row.get('serving_size') else None,
                        row.get('serving_size_unit', ''),
                        int(row['fdc_id'])
                    ))
                    
                    if len(updates) >= chunk_size:
                        await self._update_branded_foods(updates)
                        total_updated += len(updates)
                        updates = []
                
                if updates:
                    await self._update_branded_foods(updates)
                    total_updated += len(updates)
                
                logger.info(f"Updated {total_updated} branded foods")
        except KeyError as e:
            logger.warning(f"Branded food file not found in zip: {e}")
    
    async def _update_branded_foods(self, updates: List[tuple]):
        """Update branded food details."""
        await self.conn.executemany(
            """
            UPDATE usda_foods SET
                brand_owner = $1,
                brand_name = $2,
                gtin_upc = $3,
                ingredients = $4,
                serving_size = $5,
                serving_size_unit = $6
            WHERE fdc_id = $7
            """,
            updates
        )
    
    async def import_key_nutrients(self, zip_file: zipfile.ZipFile):
        """Import only key nutrients to save space."""
        logger.info("Importing key nutrients...")
        
        # Key nutrient IDs we care about
        key_nutrients = {
            1008: 'Energy',      # Calories
            1003: 'Protein',     # Protein
            1004: 'Total lipid', # Fat
            1005: 'Carbohydrate', # Carbs
            1079: 'Fiber',       # Fiber
            1093: 'Sodium',      # Sodium
            2000: 'Sugars'       # Sugar
        }
        
        with zip_file.open('FoodData_Central_csv_2025-04-24/food_nutrient.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            nutrients = []
            total_imported = 0
            
            for row in tqdm(reader, desc="Processing nutrients"):
                nutrient_id = int(row['nutrient_id'])
                
                # Only import key nutrients
                if nutrient_id not in key_nutrients:
                    continue
                
                nutrients.append((
                    int(row['fdc_id']),
                    nutrient_id,
                    float(row['amount']) if row.get('amount') else 0.0
                ))
                
                if len(nutrients) >= 10000:
                    await self._insert_nutrients(nutrients)
                    total_imported += len(nutrients)
                    nutrients = []
            
            if nutrients:
                await self._insert_nutrients(nutrients)
                total_imported += len(nutrients)
            
            logger.info(f"Imported {total_imported} nutrient values")
    
    async def _insert_nutrients(self, nutrients: List[tuple]):
        """Insert nutrient data."""
        await self.conn.executemany(
            """
            INSERT INTO usda_food_nutrients (fdc_id, nutrient_id, amount)
            VALUES ($1, $2, $3)
            ON CONFLICT (fdc_id, nutrient_id) DO UPDATE SET
                amount = EXCLUDED.amount
            """,
            nutrients
        )
    
    async def import_portions(self, zip_file: zipfile.ZipFile):
        """Import food portion data."""
        logger.info("Importing food portions...")
        
        with zip_file.open('FoodData_Central_csv_2025-04-24/food_portion.csv') as f:
            reader = csv.DictReader(line.decode('utf-8') for line in f)
            
            portions = []
            total_imported = 0
            
            for row in tqdm(reader, desc="Processing portions"):
                portions.append((
                    int(row['fdc_id']),
                    int(row.get('seq_num', 0)),
                    float(row['amount']) if row.get('amount') else None,
                    int(row['measure_unit_id']) if row.get('measure_unit_id') and row['measure_unit_id'] != '9999' else None,
                    row.get('portion_description', ''),
                    row.get('modifier', ''),
                    float(row['gram_weight']) if row.get('gram_weight') else None
                ))
                
                if len(portions) >= 10000:
                    await self._insert_portions(portions)
                    total_imported += len(portions)
                    portions = []
            
            if portions:
                await self._insert_portions(portions)
                total_imported += len(portions)
            
            logger.info(f"Imported {total_imported} portions")
    
    async def _insert_portions(self, portions: List[tuple]):
        """Insert portion data."""
        await self.conn.executemany(
            """
            INSERT INTO usda_food_portions 
            (fdc_id, seq_num, amount, measure_unit_id, portion_description, modifier, gram_weight)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (id) DO UPDATE SET
                seq_num = EXCLUDED.seq_num,
                amount = EXCLUDED.amount,
                measure_unit_id = EXCLUDED.measure_unit_id,
                portion_description = EXCLUDED.portion_description,
                modifier = EXCLUDED.modifier,
                gram_weight = EXCLUDED.gram_weight
            """,
            portions
        )
    
    async def run_import(self):
        """Run the complete import process."""
        try:
            await self.connect()
            
            if not self.zip_path.exists():
                raise FileNotFoundError(f"Data file not found: {self.zip_path}")
            
            logger.info("Starting USDA data import...")
            
            with zipfile.ZipFile(self.zip_path) as zip_file:
                # Import reference tables first
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
                # Skip nutrients and portions - we don't need those tables
                # await self.import_key_nutrients(zip_file)
                # await self.import_portions(zip_file)
                
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