#!/usr/bin/env python3
"""
Script to normalize all pantry item units in the database
Converts units like 'ea' -> 'each', 'floz' -> 'fluid ounce', etc.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.config.database import get_database_service
from backend_gateway.services.unit_validation_service import UnitValidationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Unit mappings for normalization
UNIT_MAPPINGS = {
    # Weight
    'g': 'gram',
    'gr': 'gram',
    'grams': 'gram',
    'kg': 'kilogram',
    'kilo': 'kilogram',
    'kilos': 'kilogram',
    'kilograms': 'kilogram',
    'mg': 'milligram',
    'milligrams': 'milligram',
    'oz': 'ounce',
    'ounces': 'ounce',
    'lb': 'pound',
    'lbs': 'pound',
    'pounds': 'pound',
    
    # Volume
    'ml': 'milliliter',
    'milliliters': 'milliliter',
    'millilitres': 'milliliter',
    'l': 'liter',
    'liters': 'liter',
    'litres': 'liter',
    'tsp': 'teaspoon',
    'teaspoons': 'teaspoon',
    'tbsp': 'tablespoon',
    'tablespoons': 'tablespoon',
    'tbs': 'tablespoon',
    'fl oz': 'fluid ounce',
    'floz': 'fluid ounce',
    'fluid oz': 'fluid ounce',
    'fluid ounces': 'fluid ounce',
    'c': 'cup',
    'cups': 'cup',
    'pt': 'pint',
    'pints': 'pint',
    'qt': 'quart',
    'quarts': 'quart',
    'gal': 'gallon',
    'gallons': 'gallon',
    
    # Countable
    'ea': 'each',
    'pc': 'piece',
    'pcs': 'piece',
    'pieces': 'piece',
    'doz': 'dozen',
    'dozens': 'dozen',
    
    # Containers
    'pkg': 'package',
    'packages': 'package',
    'pack': 'package',
    'bags': 'bag',
    'boxes': 'box',
    'cans': 'can',
    'jars': 'jar',
    'bottles': 'bottle',
    'cartons': 'carton'
}


async def normalize_pantry_units():
    """Normalize all pantry item units in the database."""
    db_service = None
    
    try:
        # Initialize database service
        db_service = get_database_service()
        
        # Get all pantry items
        query = """
            SELECT pantry_item_id, product_name, unit_of_measurement
            FROM pantry_items
            WHERE user_id = 111
            ORDER BY pantry_item_id
        """
        
        results = await db_service.execute_query(query)
        
        if not results:
            logger.info("No pantry items found")
            return
        
        logger.info(f"Found {len(results)} pantry items to check")
        
        # Track updates
        updates_needed = []
        
        for row in results:
            pantry_item_id = row['pantry_item_id']
            product_name = row['product_name']
            current_unit = row['unit_of_measurement']
            
            if not current_unit:
                continue
            
            # Normalize the unit
            unit_lower = current_unit.lower().strip()
            normalized_unit = UNIT_MAPPINGS.get(unit_lower, current_unit)
            
            # Check if normalization is needed
            if normalized_unit != current_unit:
                updates_needed.append({
                    'pantry_item_id': pantry_item_id,
                    'product_name': product_name,
                    'old_unit': current_unit,
                    'new_unit': normalized_unit
                })
        
        if not updates_needed:
            logger.info("All units are already normalized!")
            return
        
        logger.info(f"\nFound {len(updates_needed)} units that need normalization:")
        
        # Display changes to be made
        print("\nUnits to be normalized:")
        print("-" * 80)
        for update in updates_needed[:20]:  # Show first 20
            print(f"{update['product_name']:<30} {update['old_unit']:<15} → {update['new_unit']}")
        
        if len(updates_needed) > 20:
            print(f"... and {len(updates_needed) - 20} more items")
        
        # Ask for confirmation
        confirm = input("\nDo you want to apply these normalizations? (yes/no): ")
        
        if confirm.lower() != 'yes':
            logger.info("Update cancelled")
            return
        
        # Apply updates
        logger.info("\nApplying unit normalizations...")
        
        for update in updates_needed:
            update_query = """
                UPDATE pantry_items
                SET unit_of_measurement = %s,
                    updated_at = %s
                WHERE pantry_item_id = %s
            """
            
            await db_service.execute_query(
                update_query,
                (update['new_unit'], datetime.now(), update['pantry_item_id'])
            )
        
        logger.info(f"\nSuccessfully normalized {len(updates_needed)} units!")
        
        # Show summary of changes
        print("\nSummary of normalizations:")
        print("-" * 50)
        
        # Count changes by unit type
        changes_by_type = {}
        for update in updates_needed:
            key = f"{update['old_unit']} → {update['new_unit']}"
            changes_by_type[key] = changes_by_type.get(key, 0) + 1
        
        for change_type, count in sorted(changes_by_type.items(), key=lambda x: -x[1]):
            print(f"{change_type:<30} {count} items")
        
    except Exception as e:
        logger.error(f"Error normalizing units: {str(e)}")
        raise
    finally:
        if db_service:
            await db_service.close()


async def main():
    """Main function."""
    print("PrepSense Pantry Unit Normalization")
    print("=" * 50)
    
    await normalize_pantry_units()


if __name__ == "__main__":
    asyncio.run(main())