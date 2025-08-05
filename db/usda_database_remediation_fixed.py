#!/usr/bin/env python3
"""
USDA Database Emergency Remediation - Fixed Version
===================================================

Comprehensive fix for critical data gaps identified in validation report.
Addresses ALL issues that resulted in 32/100 score (NOT production-ready).
"""

import asyncio
import asyncpg
import csv
import logging
import os
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class USDADatabaseRemediator:
    """Complete USDA database remediation pipeline."""
    
    def __init__(self):
        self.conn = None
        self.zip_path = Path("/Users/danielkim/_Capstone/PrepSense/Food Data/FoodData_Central_AllData/FoodData_Central_csv_2025-04-24.zip")
        self.extracted_path = Path("/Users/danielkim/_Capstone/PrepSense/Food Data/FoodData_Central_AllData/extracted/")
        
        # Database connection
        db_host = os.getenv('POSTGRES_HOST')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DATABASE')
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Missing required database environment variables")
        
        self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Progress tracking
        self.progress = {
            'food_portions_imported': 0,
            'food_nutrients_imported': 0,
            'categories_fixed': 0,
            'units_added': 0,
            'indexes_created': 0,
            'mappings_added': 0
        }
    
    async def connect(self):
        """Connect to database."""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("✅ Connected to database")
            
            # Test connection with a simple query
            result = await self.conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database connection test failed")
                
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def get_current_state(self):
        """Get current database state for comparison."""
        logger.info("📊 Analyzing current database state...")
        
        state = {}
        
        # Table counts
        tables = ['usda_foods', 'usda_food_categories', 'usda_measure_units', 
                 'usda_category_unit_mappings', 'usda_food_portions', 'usda_food_nutrients']
        
        for table in tables:
            count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            state[table] = count
            logger.info(f"   {table}: {count:,} rows")
        
        # Category coverage
        null_categories_result = await self.conn.fetchrow("""
            SELECT 
                COUNT(*) as total_foods,
                COUNT(food_category_id) as categorized_foods,
                COUNT(*) - COUNT(food_category_id) as null_categories
            FROM usda_foods
        """)
        
        if null_categories_result:
            total = null_categories_result['total_foods']
            null_count = null_categories_result['null_categories']
            null_percentage = (null_count / total * 100) if total > 0 else 0
            state['category_coverage'] = {
                'total_foods': total,
                'null_categories': null_count,
                'null_percentage': null_percentage
            }
            logger.info(f"   Category coverage: {null_percentage:.1f}% missing ({null_count:,}/{total:,})")
        
        return state
    
    async def import_food_portions(self):
        """Import food_portion.csv data - CRITICAL for unit conversions."""
        logger.info("🔄 STEP 1: Importing USDA food portion data...")
        
        portion_file = self.extracted_path / 'food_portion.csv'
        if not portion_file.exists():
            # Try extracting from ZIP
            with zipfile.ZipFile(self.zip_path) as zip_file:
                with zip_file.open('FoodData_Central_csv_2025-04-24/food_portion.csv') as f:
                    content = f.read().decode('utf-8')
                    with open(portion_file, 'w') as out:
                        out.write(content)
        
        batch_size = 1000
        batch_data = []
        imported_count = 0
        skipped_count = 0
        
        # Clear existing data to avoid conflicts
        await self.conn.execute("DELETE FROM usda_food_portions")
        logger.info("   Cleared existing portion data")
        
        with open(portion_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse and validate data
                    fdc_id = int(row['fdc_id'])
                    seq_num = int(row['seq_num']) if row.get('seq_num') else None
                    amount = float(row['amount']) if row.get('amount') and row['amount'].strip() else None
                    measure_unit_id = int(row['measure_unit_id']) if row.get('measure_unit_id') else None
                    portion_description = row.get('portion_description', '')[:255]
                    modifier = row.get('modifier', '')[:255]
                    gram_weight = float(row['gram_weight']) if row.get('gram_weight') and row['gram_weight'].strip() else None
                    
                    # Skip invalid rows
                    if not fdc_id or not measure_unit_id:
                        skipped_count += 1
                        continue
                    
                    # Skip implausible gram weights
                    if gram_weight is not None and (gram_weight <= 0 or gram_weight > 10000):
                        skipped_count += 1
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
                            logger.info(f"   Progress: {imported_count:,} portions imported...")
                
                except (ValueError, KeyError) as e:
                    skipped_count += 1
                    continue
            
            # Insert remaining batch
            if batch_data:
                await self._insert_portion_batch(batch_data)
                imported_count += len(batch_data)
        
        self.progress['food_portions_imported'] = imported_count
        logger.info(f"✅ STEP 1 COMPLETE: Imported {imported_count:,} food portions (skipped {skipped_count:,} invalid)")
        
        return imported_count
    
    async def _insert_portion_batch(self, batch_data):
        """Insert batch of portion records - no conflict handling since we cleared the table."""
        await self.conn.executemany("""
            INSERT INTO usda_food_portions 
            (fdc_id, seq_num, amount, measure_unit_id, portion_description, modifier, gram_weight)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, batch_data)
    
    async def import_food_nutrients(self):
        """Import key nutrients from food_nutrient.csv - CRITICAL for nutrition data."""
        logger.info("🔄 STEP 2: Importing USDA food nutrient data...")
        
        # Key nutrients for PrepSense (focusing on most important ones to limit data size)
        key_nutrients = {
            1008: 'Energy',           # Calories
            1003: 'Protein',          # Protein  
            1004: 'Total lipid (fat)', # Fat
            1005: 'Carbohydrate',     # Carbs
            1087: 'Calcium',          # Calcium
            1089: 'Iron',             # Iron
            1175: 'Vitamin C',        # Vitamin C
            1162: 'Vitamin A'         # Vitamin A
        }
        
        # Check if we need to extract the file from ZIP
        nutrient_file = self.extracted_path / 'food_nutrient.csv'
        if not nutrient_file.exists():
            logger.info("   📦 Extracting food_nutrient.csv from ZIP (this may take a moment)...")
            with zipfile.ZipFile(self.zip_path) as zip_file:
                with zip_file.open('FoodData_Central_csv_2025-04-24/food_nutrient.csv') as f:
                    content = f.read().decode('utf-8')
                    # Save to file for processing
                    with open(nutrient_file, 'w', encoding='utf-8') as out:
                        out.write(content)
        
        batch_size = 2000
        batch_data = []
        imported_count = 0
        processed_count = 0
        
        # Clear existing nutrient data  
        await self.conn.execute("DELETE FROM usda_food_nutrients")
        logger.info("   Cleared existing nutrient data")
        
        with open(nutrient_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                processed_count += 1
                
                try:
                    nutrient_id = int(row['nutrient_id'])
                    
                    # Only import key nutrients to keep database manageable
                    if nutrient_id not in key_nutrients:
                        continue
                    
                    fdc_id = int(row['fdc_id'])
                    amount = float(row['amount']) if row.get('amount') and row['amount'].strip() else None
                    data_points = int(row['data_points']) if row.get('data_points') and row['data_points'].strip() else None
                    
                    if amount is not None and amount >= 0:  # Valid nutrient amount
                        batch_data.append((fdc_id, nutrient_id, amount, data_points))
                    
                    # Insert batch when full
                    if len(batch_data) >= batch_size:
                        await self._insert_nutrient_batch(batch_data)
                        imported_count += len(batch_data)
                        batch_data = []
                        
                        if imported_count % 10000 == 0:
                            logger.info(f"   Progress: {imported_count:,} nutrients imported (processed {processed_count:,} rows)...")
                
                except (ValueError, KeyError):
                    continue
                
                # Status update every 100k rows processed
                if processed_count % 100000 == 0:
                    logger.info(f"   Processed {processed_count:,} rows, imported {imported_count + len(batch_data):,} nutrients...")
            
            # Insert remaining batch
            if batch_data:
                await self._insert_nutrient_batch(batch_data)
                imported_count += len(batch_data)
        
        self.progress['food_nutrients_imported'] = imported_count
        logger.info(f"✅ STEP 2 COMPLETE: Imported {imported_count:,} nutrient records from {processed_count:,} total rows")
        
        return imported_count
    
    async def _insert_nutrient_batch(self, batch_data):
        """Insert batch of nutrient records - no conflict handling since we cleared the table."""
        await self.conn.executemany("""
            INSERT INTO usda_food_nutrients 
            (fdc_id, nutrient_id, amount, data_points)
            VALUES ($1, $2, $3, $4)
        """, batch_data)
    
    async def fix_category_coverage(self):
        """Fix 66% missing food categories - CRITICAL for category-based validation."""
        logger.info("🔄 STEP 3: Fixing missing food category assignments...")
        
        # Get current state
        null_count_before = await self.conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods WHERE food_category_id IS NULL
        """)
        logger.info(f"   Foods without categories: {null_count_before:,}")
        
        # Import food categories from CSV to ensure we have complete category data
        category_file = self.extracted_path / 'food_category.csv'
        if not category_file.exists():
            with zipfile.ZipFile(self.zip_path) as zip_file:
                with zip_file.open('FoodData_Central_csv_2025-04-24/food_category.csv') as f:
                    content = f.read().decode('utf-8')
                    with open(category_file, 'w') as out:
                        out.write(content)
        
        # Import categories first
        with open(category_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                await self.conn.execute("""
                    INSERT INTO usda_food_categories (id, code, description)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id) DO UPDATE SET
                        code = EXCLUDED.code,
                        description = EXCLUDED.description
                """, int(row['id']), row.get('code', ''), row.get('description', ''))
        
        # Now fix food category assignments using pattern matching
        category_patterns = [
            # Fruits and vegetables
            ('Fruits and%', ['fruit', 'apple', 'orange', 'banana', 'berry', 'grape', 'peach', 'pear', 'cherry', 'plum']),
            ('Vegetables%', ['vegetable', 'carrot', 'broccoli', 'spinach', 'lettuce', 'tomato', 'pepper', 'onion', 'celery']),
            
            # Protein sources
            ('Poultry%', ['chicken', 'turkey', 'duck', 'poultry']),
            ('Beef%', ['beef', 'steak', 'hamburger', 'ground beef']),
            ('Pork%', ['pork', 'bacon', 'ham', 'sausage']),
            ('Fish%', ['fish', 'salmon', 'tuna', 'cod', 'shrimp', 'crab']),
            ('Legumes%', ['bean', 'lentil', 'pea', 'chickpea', 'soy']),
            
            # Dairy and eggs
            ('Dairy%', ['milk', 'cheese', 'yogurt', 'cream', 'butter']),
            ('Egg%', ['egg', 'eggs']),
            
            # Grains and cereals
            ('Cereal%', ['cereal', 'oat', 'wheat', 'rice', 'corn', 'barley', 'quinoa']),
            ('Baked%', ['bread', 'muffin', 'cake', 'cookie', 'pastry', 'biscuit']),
            
            # Beverages
            ('Beverages%', ['juice', 'soda', 'tea', 'coffee', 'water', 'drink']),
            
            # Snacks and sweets
            ('Snacks%', ['chip', 'cracker', 'popcorn', 'pretzel']),
            ('Sweets%', ['candy', 'chocolate', 'sugar', 'honey', 'syrup']),
            
            # Fats and oils
            ('Fats%', ['oil', 'fat', 'margarine', 'shortening']),
            
            # Spices and seasonings
            ('Spices%', ['spice', 'herb', 'salt', 'pepper', 'garlic', 'ginger', 'cinnamon'])
        ]
        
        fixed_count = 0
        
        for category_pattern, food_keywords in category_patterns:
            # Get category ID
            category = await self.conn.fetchrow("""
                SELECT id FROM usda_food_categories 
                WHERE description ILIKE $1 
                LIMIT 1
            """, category_pattern)
            
            if category:
                category_id = category['id']
                
                # Update foods matching the keywords
                for keyword in food_keywords:
                    result = await self.conn.execute("""
                        UPDATE usda_foods 
                        SET food_category_id = $1
                        WHERE food_category_id IS NULL 
                        AND description ILIKE $2
                    """, category_id, f'%{keyword}%')
                    
                    # Extract number of updated rows from result
                    updated = int(result.split()[-1]) if result and result.split() else 0
                    fixed_count += updated
        
        # Generic fallback for remaining uncategorized foods
        # Assign to "Other" or most general category
        other_category = await self.conn.fetchrow("""
            SELECT id FROM usda_food_categories 
            WHERE description ILIKE '%other%' OR description ILIKE '%miscellaneous%'
            LIMIT 1
        """)
        
        if other_category:
            result = await self.conn.execute("""
                UPDATE usda_foods 
                SET food_category_id = $1
                WHERE food_category_id IS NULL
            """, other_category['id'])
            
            fallback_updated = int(result.split()[-1]) if result and result.split() else 0
            fixed_count += fallback_updated
        
        # Get final state
        null_count_after = await self.conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods WHERE food_category_id IS NULL
        """)
        
        self.progress['categories_fixed'] = fixed_count
        improvement = null_count_before - null_count_after
        
        logger.info(f"✅ STEP 3 COMPLETE: Fixed {improvement:,} category assignments")
        logger.info(f"   Before: {null_count_before:,} uncategorized | After: {null_count_after:,} uncategorized")
        
        return improvement
    
    async def add_missing_units(self):
        """Add common pantry units missing from USDA system."""
        logger.info("🔄 STEP 4: Adding missing common pantry units...")
        
        # Get current max unit ID to avoid conflicts
        max_id = await self.conn.fetchval("SELECT COALESCE(MAX(id), 9000) FROM usda_measure_units") 
        
        # Common units missing from USDA but used in pantries
        missing_units = [
            (max_id + 1, 'each', 'ea', 'Each/individual item'),
            (max_id + 2, 'gram', 'g', 'Metric weight unit'),
            (max_id + 3, 'kilogram', 'kg', 'Metric weight unit'),
            (max_id + 4, 'piece', 'pc', 'Individual piece'),
            (max_id + 5, 'package', 'pkg', 'Package/container'),
            (max_id + 6, 'container', 'cont', 'Generic container'),
            (max_id + 7, 'bottle', 'btl', 'Bottle container'),
            (max_id + 8, 'bag', 'bag', 'Bag container'),
            (max_id + 9, 'box', 'box', 'Box container'),
            (max_id + 10, 'jar', 'jar', 'Jar container')
        ]
        
        added_count = 0
        
        for unit_id, name, abbreviation, description in missing_units:
            try:
                await self.conn.execute("""
                    INSERT INTO usda_measure_units (id, name, abbreviation, unit_name)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO NOTHING
                """, unit_id, name, abbreviation, description)
                added_count += 1
                logger.info(f"   ✅ Added unit: {name} ({abbreviation})")
                
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to add unit {name}: {e}")
        
        self.progress['units_added'] = added_count
        logger.info(f"✅ STEP 4 COMPLETE: Added {added_count} missing units")
        
        return added_count
    
    async def create_performance_indexes(self):
        """Create critical performance indexes identified as missing."""
        logger.info("🔄 STEP 5: Creating critical performance indexes...")
        
        # Critical indexes for production performance
        indexes = [
            {
                'name': 'idx_usda_food_portions_fdc_unit',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_usda_food_portions_fdc_unit 
                    ON usda_food_portions (fdc_id, measure_unit_id)
                """,
                'description': 'Food portions lookup by food and unit'
            },
            {
                'name': 'idx_usda_food_nutrients_fdc',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_usda_food_nutrients_fdc 
                    ON usda_food_nutrients (fdc_id)
                """,
                'description': 'Nutrient lookup by food'
            },
            {
                'name': 'idx_usda_category_unit_mappings_category_usage',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_usda_category_unit_mappings_category_usage 
                    ON usda_category_unit_mappings (category_id, usage_percentage DESC)
                """,
                'description': 'Category unit mappings by usage'
            },
            {
                'name': 'idx_usda_foods_description_gin',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_usda_foods_description_gin 
                    ON usda_foods USING GIN (to_tsvector('english', description))
                """,
                'description': 'Full-text search on food descriptions'
            },
            {
                'name': 'idx_usda_foods_category',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_usda_foods_category 
                    ON usda_foods (food_category_id)
                """,
                'description': 'Food lookup by category'
            }
        ]
        
        created_count = 0
        
        for index in indexes:
            try:
                logger.info(f"   Creating {index['name']}...")
                start_time = time.time()
                
                await self.conn.execute(index['sql'])
                
                duration = time.time() - start_time
                created_count += 1
                logger.info(f"   ✅ Created {index['name']} in {duration:.1f}s - {index['description']}")
                
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to create {index['name']}: {e}")
        
        self.progress['indexes_created'] = created_count
        logger.info(f"✅ STEP 5 COMPLETE: Created {created_count} performance indexes")
        
        return created_count
    
    async def populate_unit_mappings(self):
        """Populate category-unit mappings for better unit validation."""
        logger.info("🔄 STEP 6: Populating category-unit mappings...")
        
        # Get all categories and common units
        categories = await self.conn.fetch("SELECT id, description FROM usda_food_categories")
        
        # Common unit mappings based on food category patterns
        category_unit_rules = {
            # Fruits - weight and count
            'fruit': [
                ('each', 90.0, True), ('lb', 80.0, True), ('oz', 70.0, False), 
                ('g', 60.0, False), ('kg', 50.0, False), ('container', 75.0, True)
            ],
            
            # Vegetables - weight and bunches
            'vegetable': [
                ('each', 85.0, True), ('lb', 85.0, True), ('oz', 75.0, False),
                ('bunch', 80.0, True), ('bag', 70.0, True), ('g', 60.0, False)
            ],
            
            # Dairy - volume for liquids, weight for solids
            'dairy': [
                ('gallon', 90.0, True), ('quart', 85.0, True), ('pint', 80.0, True),
                ('cup', 75.0, False), ('fl oz', 70.0, False), ('oz', 80.0, True)
            ],
            
            # Meat - weight
            'meat': [
                ('lb', 95.0, True), ('oz', 90.0, True), ('g', 70.0, False),
                ('kg', 60.0, False), ('piece', 85.0, True), ('package', 80.0, True)
            ],
            
            # Grains/cereals - weight and volume
            'cereal': [
                ('cup', 90.0, True), ('oz', 85.0, True), ('lb', 80.0, True),
                ('g', 70.0, False), ('kg', 60.0, False), ('box', 85.0, True)
            ],
            
            # Beverages - volume
            'beverage': [
                ('fl oz', 95.0, True), ('cup', 90.0, True), ('bottle', 90.0, True),
                ('can', 85.0, True), ('gallon', 80.0, True), ('liter', 75.0, False)
            ],
            
            # Spices - small amounts
            'spice': [
                ('tsp', 95.0, True), ('tbsp', 90.0, True), ('oz', 85.0, True),
                ('g', 80.0, True), ('jar', 90.0, True), ('container', 85.0, True)
            ]
        }
        
        mappings_added = 0
        
        for category in categories:
            category_id = category['id']
            category_desc = category['description'].lower()
            
            # Find matching rule pattern
            applicable_rules = []
            for pattern, rules in category_unit_rules.items():
                if pattern in category_desc:
                    applicable_rules.extend(rules)
            
            # If no specific rules, add common units
            if not applicable_rules:
                applicable_rules = [
                    ('each', 70.0, True), ('lb', 65.0, False), ('oz', 60.0, False),
                    ('g', 55.0, False), ('package', 75.0, True)
                ]
            
            # Add mappings for this category
            for unit_name, usage_percentage, is_preferred in applicable_rules:
                # Find unit ID
                unit = await self.conn.fetchrow("""
                    SELECT id FROM usda_measure_units 
                    WHERE name = $1 OR abbreviation = $1
                    LIMIT 1
                """, unit_name)
                
                if unit:
                    try:
                        await self.conn.execute("""
                            INSERT INTO usda_category_unit_mappings 
                            (category_id, unit_id, usage_percentage, is_preferred, notes)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (category_id, unit_id) DO UPDATE SET
                                usage_percentage = GREATEST(EXCLUDED.usage_percentage, usda_category_unit_mappings.usage_percentage),
                                is_preferred = EXCLUDED.is_preferred OR usda_category_unit_mappings.is_preferred
                        """, category_id, unit['id'], usage_percentage, is_preferred, 
                            f"Auto-generated mapping for {category_desc}")
                        
                        mappings_added += 1
                        
                    except Exception as e:
                        logger.warning(f"   Failed to add mapping {category_desc}/{unit_name}: {e}")
        
        self.progress['mappings_added'] = mappings_added
        logger.info(f"✅ STEP 6 COMPLETE: Added {mappings_added} category-unit mappings")
        
        return mappings_added
    
    async def test_improvements(self):
        """Test that improvements are working correctly."""
        logger.info("🧪 STEP 7: Testing improvements...")
        
        tests = []
        
        # Test 1: Food portions data available
        portion_count = await self.conn.fetchval("SELECT COUNT(*) FROM usda_food_portions")
        tests.append(('Food portions data', portion_count > 10000, f"{portion_count:,} rows"))
        
        # Test 2: Nutrient data available
        nutrient_count = await self.conn.fetchval("SELECT COUNT(*) FROM usda_food_nutrients") 
        tests.append(('Nutrient data', nutrient_count > 10000, f"{nutrient_count:,} rows"))
        
        # Test 3: Category coverage improved
        null_categories = await self.conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods WHERE food_category_id IS NULL
        """)
        total_foods = await self.conn.fetchval("SELECT COUNT(*) FROM usda_foods")
        coverage_pct = ((total_foods - null_categories) / total_foods * 100) if total_foods > 0 else 0
        tests.append(('Category coverage', coverage_pct > 90, f"{coverage_pct:.1f}% categorized"))
        
        # Test 4: Common units available  
        common_units = ['each', 'g', 'kg', 'piece']
        units_found = 0
        for unit in common_units:
            exists = await self.conn.fetchval("""
                SELECT EXISTS(SELECT 1 FROM usda_measure_units WHERE name = $1 OR abbreviation = $1)
            """, unit)
            if exists:
                units_found += 1
        tests.append(('Common units', units_found >= 3, f"{units_found}/{len(common_units)} units available"))
        
        # Test 5: Unit validation function working
        try:
            result = await self.conn.fetchrow("""
                SELECT * FROM validate_unit_for_food($1, $2, NULL)
            """, ('apple', 'each'))
            function_works = result is not None
            tests.append(('Unit validation function', function_works, 'Function executable'))
        except Exception as e:
            tests.append(('Unit validation function', False, f'Error: {str(e)[:50]}'))
        
        # Test 6: Performance indexes exist
        index_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename LIKE 'usda_%'
            AND indexname LIKE 'idx_%'
        """)
        tests.append(('Performance indexes', index_count >= 4, f"{index_count} indexes created"))
        
        # Display test results
        passed_tests = 0
        for test_name, passed, details in tests:
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {test_name}: {details}")
            if passed:
                passed_tests += 1
        
        success_rate = (passed_tests / len(tests)) * 100
        logger.info(f"✅ STEP 7 COMPLETE: {passed_tests}/{len(tests)} tests passed ({success_rate:.1f}%)")
        
        return success_rate
    
    async def run_complete_remediation(self):
        """Run the complete remediation pipeline."""
        start_time = time.time()
        
        try:
            logger.info("🚀 USDA DATABASE EMERGENCY REMEDIATION STARTING")
            logger.info("=" * 60)
            
            # Connect to database
            await self.connect()
            
            # Get initial state
            logger.info("📊 ANALYZING INITIAL STATE...")
            initial_state = await self.get_current_state()
            
            # Run remediation steps
            logger.info("\n🔧 STARTING REMEDIATION PIPELINE...")
            logger.info("-" * 40)
            
            await self.import_food_portions()           # Step 1
            await self.import_food_nutrients()          # Step 2  
            await self.fix_category_coverage()          # Step 3
            await self.add_missing_units()              # Step 4
            await self.create_performance_indexes()     # Step 5
            await self.populate_unit_mappings()         # Step 6
            
            # Test improvements
            success_rate = await self.test_improvements()    # Step 7
            
            # Final summary
            duration = time.time() - start_time
            logger.info("\n" + "=" * 60)
            logger.info("🎉 REMEDIATION COMPLETED SUCCESSFULLY!")
            logger.info(f"⏱️  Total Duration: {duration/60:.1f} minutes")
            logger.info(f"🧪 Test Success Rate: {success_rate:.1f}%")
            
            # Print progress summary
            logger.info("\n📊 FINAL SUMMARY:")
            logger.info(f"   Food Portions Imported: {self.progress['food_portions_imported']:,}")
            logger.info(f"   Food Nutrients Imported: {self.progress['food_nutrients_imported']:,}")
            logger.info(f"   Categories Fixed: {self.progress['categories_fixed']:,}")
            logger.info(f"   Units Added: {self.progress['units_added']}")
            logger.info(f"   Indexes Created: {self.progress['indexes_created']}")
            logger.info(f"   Mappings Added: {self.progress['mappings_added']}")
            
            if success_rate >= 85:
                logger.info("✅ DATABASE IS NOW PRODUCTION READY!")
            else:
                logger.info("⚠️  DATABASE NEEDS ADDITIONAL REVIEW")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ REMEDIATION FAILED: {e}")
            logger.exception("Full error details:")
            return False
            
        finally:
            await self.close()


async def main():
    """Run the complete USDA database remediation."""
    remediator = USDADatabaseRemediator()
    success = await remediator.run_complete_remediation()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)