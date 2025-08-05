#!/usr/bin/env python3
"""
Import USDA food portion data to complete the database setup.
This addresses the critical missing data identified in the DBA analysis.
"""

import asyncio
import asyncpg
import csv
import logging
import os
import zipfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class USDAPortionImporter:
    """Import USDA food portion data for unit conversions."""
    
    def __init__(self):
        self.conn = None
        self.zip_path = Path("/Users/danielkim/_Capstone/PrepSense/Food Data/FoodData_Central_AllData/FoodData_Central_csv_2025-04-24.zip")
        
        # Connect to database
        db_host = os.getenv('POSTGRES_HOST')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DATABASE')
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        
        self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    async def connect(self):
        """Connect to database."""
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("Connected to database")
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def import_food_portions(self):
        """Import food portion data from USDA CSV."""
        logger.info("🔄 Importing USDA food portion data...")
        
        if not self.zip_path.exists():
            raise FileNotFoundError(f"USDA data file not found: {self.zip_path}")
        
        imported_count = 0
        batch_size = 1000
        batch_data = []
        
        # Check current row count
        current_count = await self.conn.fetchval("SELECT COUNT(*) FROM usda_food_portions")
        logger.info(f"Current food portions in database: {current_count}")
        
        with zipfile.ZipFile(self.zip_path) as zip_file:
            with zip_file.open('FoodData_Central_csv_2025-04-24/food_portion.csv') as f:
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                
                for row in reader:
                    try:
                        # Parse row data
                        fdc_id = int(row['fdc_id'])
                        seq_num = int(row['seq_num']) if row.get('seq_num') else None
                        amount = float(row['amount']) if row.get('amount') else None
                        measure_unit_id = int(row['measure_unit_id']) if row.get('measure_unit_id') else None
                        portion_description = row.get('portion_description', '')[:255]  # Limit length
                        modifier = row.get('modifier', '')[:255]
                        gram_weight = float(row['gram_weight']) if row.get('gram_weight') else None
                        
                        # Skip rows with invalid gram weights
                        if gram_weight is not None and (gram_weight <= 0 or gram_weight > 5000):
                            continue
                        
                        batch_data.append((
                            fdc_id, seq_num, amount, measure_unit_id,
                            portion_description, modifier, gram_weight
                        ))
                        
                        # Insert batch when full
                        if len(batch_data) >= batch_size:
                            await self._insert_portion_batch(batch_data)
                            imported_count += len(batch_data)
                            batch_data = []
                            
                            if imported_count % 5000 == 0:
                                logger.info(f"Imported {imported_count} food portions...")
                    
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid row: {e}")
                        continue
                
                # Insert remaining batch
                if batch_data:
                    await self._insert_portion_batch(batch_data)
                    imported_count += len(batch_data)
        
        logger.info(f"✅ Imported {imported_count} food portion records")
        return imported_count
    
    async def _insert_portion_batch(self, batch_data):
        """Insert a batch of portion records."""
        await self.conn.executemany("""
            INSERT INTO usda_food_portions 
            (fdc_id, seq_num, amount, measure_unit_id, portion_description, modifier, gram_weight)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
        """, batch_data)
    
    async def import_food_nutrients(self):
        """Import basic nutrient data (calories, protein, fat, carbs)."""
        logger.info("🔄 Importing key USDA food nutrient data...")
        
        # Key nutrients we care about
        key_nutrients = {
            1008: 'Energy (calories)',
            1003: 'Protein',  
            1004: 'Total lipid (fat)',
            1005: 'Carbohydrate, by difference'
        }
        
        imported_count = 0
        batch_size = 1000
        batch_data = []
        
        current_count = await self.conn.fetchval("SELECT COUNT(*) FROM usda_food_nutrients")
        logger.info(f"Current food nutrients in database: {current_count}")
        
        with zipfile.ZipFile(self.zip_path) as zip_file:
            with zip_file.open('FoodData_Central_csv_2025-04-24/food_nutrient.csv') as f:
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                
                for row in reader:
                    try:
                        nutrient_id = int(row['nutrient_id'])
                        
                        # Only import key nutrients to keep database size manageable
                        if nutrient_id not in key_nutrients:
                            continue
                        
                        fdc_id = int(row['fdc_id'])
                        amount = float(row['amount']) if row.get('amount') else None
                        data_points = int(row['data_points']) if row.get('data_points') else None
                        
                        batch_data.append((fdc_id, nutrient_id, amount, data_points))
                        
                        if len(batch_data) >= batch_size:
                            await self._insert_nutrient_batch(batch_data)
                            imported_count += len(batch_data)
                            batch_data = []
                            
                            if imported_count % 10000 == 0:
                                logger.info(f"Imported {imported_count} nutrient records...")
                    
                    except (ValueError, KeyError) as e:
                        continue
                
                # Insert remaining batch
                if batch_data:
                    await self._insert_nutrient_batch(batch_data)
                    imported_count += len(batch_data)
        
        logger.info(f"✅ Imported {imported_count} nutrient records for key nutrients")
        return imported_count
    
    async def _insert_nutrient_batch(self, batch_data):
        """Insert a batch of nutrient records."""
        await self.conn.executemany("""
            INSERT INTO usda_food_nutrients 
            (fdc_id, nutrient_id, amount, data_points)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (fdc_id, nutrient_id) DO UPDATE SET
                amount = EXCLUDED.amount,
                data_points = EXCLUDED.data_points
        """, batch_data)
    
    async def add_common_unit_mappings(self):
        """Add common units missing from USDA data."""
        logger.info("🔄 Adding common unit mappings...")
        
        # Add missing units
        missing_units = [
            (9999, 'each', 'ea', 'count'),
            (9998, 'gram', 'g', 'weight'),
            (9997, 'kilogram', 'kg', 'weight'),
            (9996, 'pound', 'pound', 'weight')
        ]
        
        for unit_id, name, abbrev, unit_type in missing_units:
            await self.conn.execute("""
                INSERT INTO usda_measure_units (id, name, abbreviation, unit_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
            """, unit_id, name, abbrev, unit_type)
        
        # Add category mappings for common units
        categories = await self.conn.fetch("SELECT id FROM usda_food_categories WHERE id <= 15")
        
        mappings_added = 0
        for cat in categories:
            category_id = cat['id']
            
            # Add 'each' as a common unit for most categories
            await self.conn.execute("""
                INSERT INTO usda_category_unit_mappings 
                (category_id, unit_id, usage_percentage, is_preferred, notes)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (category_id, unit_id) DO NOTHING
            """, category_id, 9999, 80.0, True, 'Common count unit')
            
            # Add gram/kg for weight-based categories
            if category_id in [1, 4, 5, 7, 10, 11]:  # Food categories that use weight
                await self.conn.execute("""
                    INSERT INTO usda_category_unit_mappings 
                    (category_id, unit_id, usage_percentage, is_preferred, notes)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (category_id, unit_id) DO NOTHING
                """, category_id, 9998, 70.0, True, 'Common weight unit')
            
            mappings_added += 2
        
        logger.info(f"✅ Added {mappings_added} unit mappings")
    
    async def add_common_product_aliases(self):
        """Add aliases for common pantry items."""
        logger.info("🔄 Adding common product aliases...")
        
        # Common product mappings based on analysis
        aliases_to_add = [
            ('yellow bell pepper', '%bell pepper%', 0.90, 'fuzzy'),
            ('corn on the cob', '%corn%', 0.85, 'fuzzy'),
            ('roma tomatoes', '%tomato%', 0.90, 'fuzzy'),
            ('anchovies', '%anchov%', 0.95, 'fuzzy'),
            ('red apple', '%apple%', 0.95, 'fuzzy'),
            ('ground beef', '%ground beef%', 0.98, 'exact'),
            ('all-purpose flour', '%flour%', 0.90, 'fuzzy'),
            ('milk', '%milk%', 0.80, 'fuzzy'),
            ('broccoli', '%broccoli%', 0.95, 'exact')
        ]
        
        added_count = 0
        for pantry_name, search_pattern, confidence, match_type in aliases_to_add:
            # Find matching USDA food
            fdc_id = await self.conn.fetchval("""
                SELECT fdc_id FROM usda_foods 
                WHERE description ILIKE $1
                LIMIT 1
            """, search_pattern)
            
            if fdc_id:
                await self.conn.execute("""
                    INSERT INTO product_aliases 
                    (pantry_name, usda_fdc_id, confidence_score, match_type)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (pantry_name) DO NOTHING
                """, pantry_name, fdc_id, confidence, match_type)
                added_count += 1
                logger.info(f"   ✅ Added alias: {pantry_name} -> FDC {fdc_id}")
        
        logger.info(f"✅ Added {added_count} product aliases")
    
    async def run_import(self):
        """Run the complete import process."""
        try:
            await self.connect()
            
            print("🚀 USDA Data Import Process")
            print("=" * 40)
            
            # Import food portions (critical for unit conversions)
            portion_count = await self.import_food_portions()
            
            # Import key nutrients  
            nutrient_count = await self.import_food_nutrients()
            
            # Add missing unit mappings
            await self.add_common_unit_mappings()
            
            # Add product aliases
            await self.add_common_product_aliases()
            
            print("\n✅ IMPORT COMPLETED SUCCESSFULLY!")
            print(f"   Food portions imported: {portion_count:,}")
            print(f"   Nutrient records imported: {nutrient_count:,}")
            
            # Test the improvements
            print("\n🧪 Testing improvements...")
            
            # Test unit validation
            result = await self.conn.fetchrow("""
                SELECT * FROM validate_unit_for_food_enhanced('apple', 'each')
            """)
            if result:
                print(f"   ✅ Unit validation: apple/each -> valid={result['is_valid']}, confidence={result['confidence']}")
            
            # Test portion conversion
            conversion = await self.conn.fetchrow("""
                SELECT gram_weight FROM usda_food_portions 
                WHERE measure_unit_id = (SELECT id FROM usda_measure_units WHERE name = 'cup')
                LIMIT 1
            """)
            if conversion:
                print(f"   ✅ Unit conversion: 1 cup = {conversion['gram_weight']}g available")
            
            # Check coverage improvement
            alias_count = await self.conn.fetchval("SELECT COUNT(*) FROM product_aliases")
            print(f"   ✅ Product aliases: {alias_count} common items mapped")
            
            print("\n🎯 Next Steps:")
            print("   1. Test unit validation API endpoints")
            print("   2. Run performance benchmarks")
            print("   3. Monitor query times in production")
            print("   4. Add more product aliases based on usage")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise
        finally:
            await self.close()


if __name__ == "__main__":
    asyncio.run(USDAPortionImporter().run_import())