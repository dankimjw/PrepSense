#!/usr/bin/env python3
"""
Script to recategorize existing uncategorized pantry items.
This will apply proper food categorization to items that are currently marked as "Uncategorized".
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.practical_food_categorization import PracticalFoodCategorizationService

# Load environment variables
load_dotenv()

async def recategorize_items():
    """Recategorize all uncategorized items in the database."""
    
    # Initialize services with connection params
    connection_params = {
        'host': os.getenv('POSTGRES_HOST', '35.184.61.42'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DATABASE', 'prepsense'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'PrepSense2025Secure')
    }
    
    db_service = PostgresService(connection_params)
    categorizer = PracticalFoodCategorizationService(db_service)
    
    # Get all uncategorized items
    query = """
        SELECT pantry_item_id, product_name, category
        FROM pantry_items
        WHERE category = 'Uncategorized' OR category IS NULL
        ORDER BY created_at DESC
    """
    
    try:
        items = db_service.execute_query(query)
        print(f"Found {len(items)} uncategorized items")
        
        if not items:
            print("No uncategorized items found!")
            return
        
        # Process each item
        updated_count = 0
        for item in items:
            item_id = item['pantry_item_id']
            item_name = item['product_name']
            
            try:
                # Get proper categorization
                categorization = await categorizer.categorize_food_item(item_name)
                
                # Map category to simpler names used in the database
                category_mapping = {
                    'produce_countable': 'Produce',
                    'produce_measurable': 'Produce',
                    'liquids': 'Beverages',
                    'dairy': 'Dairy',
                    'meat_seafood': 'Proteins',
                    'dry_goods': 'Pantry Staples',
                    'canned_goods': 'Canned Goods',
                    'spices': 'Spices',
                    'snacks_bars': 'Snacks',
                    'packaged_snacks': 'Snacks',
                    'frozen_foods': 'Frozen',
                    'condiments': 'Condiments',
                    'baking': 'Baking',
                    'grains': 'Grains',
                    'pasta_rice': 'Pantry Staples',
                    'herbs': 'Fresh Herbs',
                    'other': 'Other'
                }
                
                new_category = category_mapping.get(categorization.category, 'Other')
                
                # Update the item's category
                update_query = """
                    UPDATE pantry_items
                    SET category = %(category)s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE pantry_item_id = %(item_id)s
                """
                
                params = {
                    'category': new_category,
                    'item_id': item_id
                }
                
                db_service.execute_query(update_query, params)
                updated_count += 1
                print(f"  ✓ {item_name}: {item.get('category', 'NULL')} → {new_category}")
                
            except Exception as e:
                print(f"  ✗ Error categorizing {item_name}: {e}")
                continue
        
        print(f"\n✅ Successfully recategorized {updated_count}/{len(items)} items")
        
        # Show updated category distribution
        dist_query = """
            SELECT category, COUNT(*) as count
            FROM pantry_items
            WHERE pantry_id IN (SELECT pantry_id FROM pantries WHERE user_id = 111)
            GROUP BY category
            ORDER BY count DESC
        """
        
        distribution = db_service.execute_query(dist_query)
        
        print("\n📊 Updated category distribution:")
        total = sum(row['count'] for row in distribution)
        for row in distribution:
            pct = 100 * row['count'] / total
            print(f"  {row['category']}: {row['count']} items ({pct:.1f}%)")
            
    except Exception as e:
        print(f"Error: {e}")
        return
    finally:
        # Close database connection
        if hasattr(db_service, 'close'):
            db_service.close()


if __name__ == "__main__":
    print("🔄 Starting pantry item recategorization...")
    asyncio.run(recategorize_items())
    print("\n✨ Recategorization complete!")