#!/usr/bin/env python3
"""
Import USDA unit mappings and analyze category-to-unit relationships.
This script:
1. Imports measure_unit.csv data
2. Analyzes food_portion.csv to determine which units are used with which categories
3. Creates category-to-unit mapping rules based on USDA data
4. Optionally imports branded food serving size data
"""

import asyncio
import asyncpg
import csv
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class USDAUnitMappingImporter:
    """Import and analyze USDA unit data for better food-to-unit matching."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self.zip_path = Path("/Users/danielkim/_Capstone/PrepSense/Food Data/FoodData_Central_AllData/FoodData_Central_csv_2025-04-24.zip")
        
    async def connect(self):
        """Connect to database."""
        self.conn = await asyncpg.connect(self.db_url)
        logger.info("Connected to database")
        
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def analyze_category_unit_relationships(self) -> Dict[int, Dict[str, any]]:
        """Analyze which units are commonly used with each food category."""
        logger.info("Analyzing category-to-unit relationships from USDA data...")
        
        category_unit_stats = defaultdict(lambda: {
            'unit_counts': defaultdict(int),
            'total_foods': 0,
            'example_foods': []
        })
        
        with zipfile.ZipFile(self.zip_path) as zip_file:
            # First, get food to category mappings
            food_categories = {}
            with zip_file.open('FoodData_Central_csv_2025-04-24/food.csv') as f:
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                for row in reader:
                    if row.get('food_category_id'):
                        food_categories[int(row['fdc_id'])] = int(row['food_category_id'])
            
            # Analyze portions to see which units are used with which categories
            with zip_file.open('FoodData_Central_csv_2025-04-24/food_portion.csv') as f:
                content = f.read().decode('utf-8')
                reader = csv.DictReader(content.splitlines())
                
                for row in reader:
                    fdc_id = int(row['fdc_id'])
                    measure_unit_id = row['measure_unit_id']
                    portion_desc = row.get('portion_description', '')
                    
                    if fdc_id in food_categories:
                        category_id = food_categories[fdc_id]
                        stats = category_unit_stats[category_id]
                        
                        # Count unit usage
                        if measure_unit_id and measure_unit_id != '9999':  # 9999 is 'undetermined'
                            stats['unit_counts'][measure_unit_id] += 1
                        
                        # Track portion descriptions for analysis
                        if portion_desc and len(stats['example_foods']) < 5:
                            stats['example_foods'].append(portion_desc)
                        
                        stats['total_foods'] += 1
        
        # Convert to regular dict for return
        return dict(category_unit_stats)
    
    async def generate_category_unit_rules(self, category_stats: Dict[int, Dict[str, any]]):
        """Generate category-to-unit rules based on analysis."""
        logger.info("Generating category-to-unit rules...")
        
        # Get unit names for better readability
        unit_names = {}
        async with self.conn.transaction():
            rows = await self.conn.fetch("SELECT id, name FROM usda_measure_units")
            unit_names = {row['id']: row['name'] for row in rows}
        
        # Get category names
        category_names = {}
        async with self.conn.transaction():
            rows = await self.conn.fetch("SELECT id, description FROM usda_food_categories")
            category_names = {row['id']: row['description'] for row in rows}
        
        # Create rules based on usage patterns
        rules = []
        for category_id, stats in category_stats.items():
            if category_id not in category_names:
                continue
                
            category_name = category_names[category_id]
            total_portions = sum(stats['unit_counts'].values())
            
            if total_portions == 0:
                continue
            
            # Find most common units (top 5)
            sorted_units = sorted(
                stats['unit_counts'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            common_units = []
            for unit_id, count in sorted_units:
                if unit_id in unit_names:
                    percentage = (count / total_portions) * 100
                    common_units.append({
                        'unit_id': int(unit_id),
                        'unit_name': unit_names[unit_id],
                        'usage_percentage': round(percentage, 2)
                    })
            
            rule = {
                'category_id': category_id,
                'category_name': category_name,
                'common_units': common_units,
                'total_foods_analyzed': stats['total_foods'],
                'example_portions': stats['example_foods'][:3]
            }
            rules.append(rule)
        
        return rules
    
    async def import_to_database(self, rules: List[Dict[str, any]]):
        """Import generated rules to database."""
        logger.info("Creating category unit mapping table...")
        
        # Create table for category-unit mappings
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS usda_category_unit_mappings (
                id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL,
                unit_id INTEGER NOT NULL,
                usage_percentage DECIMAL(5,2),
                is_preferred BOOLEAN DEFAULT FALSE,
                notes TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (category_id) REFERENCES usda_food_categories(id),
                FOREIGN KEY (unit_id) REFERENCES usda_measure_units(id),
                UNIQUE(category_id, unit_id)
            )
        """)
        
        # Insert rules
        for rule in rules:
            category_id = rule['category_id']
            
            for i, unit_info in enumerate(rule['common_units']):
                # Top 3 units are marked as preferred
                is_preferred = i < 3
                
                await self.conn.execute("""
                    INSERT INTO usda_category_unit_mappings 
                    (category_id, unit_id, usage_percentage, is_preferred, notes)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (category_id, unit_id) DO UPDATE SET
                        usage_percentage = EXCLUDED.usage_percentage,
                        is_preferred = EXCLUDED.is_preferred,
                        notes = EXCLUDED.notes
                """, 
                category_id, 
                unit_info['unit_id'], 
                unit_info['usage_percentage'],
                is_preferred,
                f"Common unit for {rule['category_name']}"
                )
        
        logger.info(f"Imported {len(rules)} category-unit mapping rules")
    
    async def create_unit_validation_functions(self):
        """Create SQL functions for unit validation using USDA data."""
        logger.info("Creating unit validation functions...")
        
        await self.conn.execute("""
            CREATE OR REPLACE FUNCTION validate_unit_for_food(
                p_food_name TEXT,
                p_unit_name TEXT,
                p_category_id INTEGER DEFAULT NULL
            ) RETURNS TABLE (
                is_valid BOOLEAN,
                confidence DECIMAL,
                suggested_units TEXT[],
                reason TEXT
            ) AS $$
            DECLARE
                v_category_id INTEGER;
                v_unit_id INTEGER;
                v_usage_percentage DECIMAL;
                v_preferred_units TEXT[];
            BEGIN
                -- Get category if not provided
                IF p_category_id IS NULL THEN
                    SELECT food_category_id INTO v_category_id
                    FROM usda_foods
                    WHERE description ILIKE '%' || p_food_name || '%'
                    LIMIT 1;
                ELSE
                    v_category_id := p_category_id;
                END IF;
                
                -- Get unit ID
                SELECT id INTO v_unit_id
                FROM usda_measure_units
                WHERE LOWER(name) = LOWER(p_unit_name)
                   OR LOWER(abbreviation) = LOWER(p_unit_name)
                LIMIT 1;
                
                -- Check if unit is valid for category
                IF v_category_id IS NOT NULL AND v_unit_id IS NOT NULL THEN
                    SELECT usage_percentage INTO v_usage_percentage
                    FROM usda_category_unit_mappings
                    WHERE category_id = v_category_id AND unit_id = v_unit_id;
                    
                    -- Get preferred units
                    SELECT ARRAY_AGG(um.name ORDER BY ucm.usage_percentage DESC)
                    INTO v_preferred_units
                    FROM usda_category_unit_mappings ucm
                    JOIN usda_measure_units um ON ucm.unit_id = um.id
                    WHERE ucm.category_id = v_category_id AND ucm.is_preferred = TRUE;
                    
                    IF v_usage_percentage IS NOT NULL THEN
                        RETURN QUERY SELECT 
                            TRUE,
                            v_usage_percentage / 100.0,
                            v_preferred_units,
                            'Unit is used in ' || v_usage_percentage || '% of similar foods';
                    ELSE
                        RETURN QUERY SELECT 
                            FALSE,
                            0.0,
                            v_preferred_units,
                            'Unit not commonly used for this food category';
                    END IF;
                ELSE
                    RETURN QUERY SELECT 
                        FALSE,
                        0.0,
                        ARRAY['each', 'lb', 'oz']::TEXT[],
                        'Could not determine food category or unit';
                END IF;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        logger.info("Created unit validation functions")
    
    async def run(self):
        """Run the complete import process."""
        try:
            await self.connect()
            
            # Analyze existing USDA data
            category_stats = await self.analyze_category_unit_relationships()
            logger.info(f"Analyzed {len(category_stats)} categories")
            
            # Generate rules
            rules = await self.generate_category_unit_rules(category_stats)
            
            # Save rules to file for review
            import json
            output_file = Path("usda_category_unit_rules.json")
            with open(output_file, 'w') as f:
                json.dump(rules, f, indent=2)
            logger.info(f"Saved rules to {output_file}")
            
            # Import to database
            await self.import_to_database(rules)
            
            # Create helper functions
            await self.create_unit_validation_functions()
            
            logger.info("✅ USDA unit mapping import completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during import: {e}")
            raise
        finally:
            await self.close()


async def main():
    """Main entry point."""
    # Build database URL from environment variables
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DATABASE')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    
    if not all([db_host, db_name, db_user, db_password]):
        logger.error("Missing required database environment variables")
        return
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    importer = USDAUnitMappingImporter(db_url)
    await importer.run()


if __name__ == "__main__":
    asyncio.run(main())