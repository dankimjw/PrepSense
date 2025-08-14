#!/usr/bin/env python3
"""
Script to add demo_ingredients tags to specific burger ingredients for demo prioritization.

This script adds a 'demo_ingredients' tag to the metadata JSONB field for:
- Lean Ground Beef
- Turkey Bacon  
- Wheat Hamburger Buns

These ingredients will be prioritized at the top when using category sort on the home screen.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo ingredients that should be prioritized (these are the burger ingredients)
DEMO_INGREDIENTS = [
    "Lean Ground Beef",
    "Turkey Bacon", 
    "Wheat Hamburger Buns"
]

async def add_demo_tags():
    """Add demo_ingredients tags to specific pantry items."""
    db_service = get_database_service()
    
    try:
        # First, check which items exist for user 111
        check_query = """
            SELECT pantry_item_id, product_name, metadata
            FROM pantry_items 
            WHERE pantry_id = (SELECT pantry_id FROM pantries WHERE user_id = 111)
        """
        
        existing_items = await db_service.execute_query(check_query)
        logger.info(f"Found {len(existing_items)} pantry items for user 111")
        
        # Show current items
        for item in existing_items:
            logger.info(f"  - {item['product_name']} (ID: {item['pantry_item_id']})")
        
        # Find matching demo ingredients
        updated_count = 0
        for item in existing_items:
            product_name = item['product_name']
            
            # Check if this item matches any of our demo ingredients (case-insensitive partial match)
            is_demo_ingredient = False
            for demo_ingredient in DEMO_INGREDIENTS:
                if demo_ingredient.lower() in product_name.lower() or product_name.lower() in demo_ingredient.lower():
                    is_demo_ingredient = True
                    break
            
            if is_demo_ingredient:
                # Get existing metadata
                current_metadata = item['metadata'] or {}
                
                # Add demo_ingredients tag
                current_metadata['demo_ingredients'] = True
                
                # Update the item
                update_query = """
                    UPDATE pantry_items 
                    SET metadata = %s
                    WHERE pantry_item_id = %s
                """
                
                await db_service.execute_query(
                    update_query, 
                    [current_metadata, item['pantry_item_id']]
                )
                
                logger.info(f"✅ Added demo_ingredients tag to: {product_name}")
                updated_count += 1
            else:
                logger.info(f"⏭️  Skipping non-demo ingredient: {product_name}")
        
        logger.info(f"\n🎯 Successfully tagged {updated_count} demo ingredients!")
        
        # Verify the changes
        verify_query = """
            SELECT pantry_item_id, product_name, metadata
            FROM pantry_items 
            WHERE pantry_id = (SELECT pantry_id FROM pantries WHERE user_id = 111)
            AND metadata->>'demo_ingredients' = 'true'
        """
        
        demo_items = await db_service.execute_query(verify_query)
        logger.info(f"\n📋 Verification: {len(demo_items)} items now have demo_ingredients tag:")
        for item in demo_items:
            logger.info(f"  ✅ {item['product_name']}")
            
    except Exception as e:
        logger.error(f"Error adding demo tags: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_demo_tags())