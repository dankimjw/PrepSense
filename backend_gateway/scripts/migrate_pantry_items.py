#!/usr/bin/env python3
"""
Simple migration script to move pantry items from BigQuery to PostgreSQL
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend_gateway.services.bigquery_service import BigQueryService
from backend_gateway.services.postgres_service import PostgresService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_pantry_items():
    """Migrate pantry items from BigQuery to PostgreSQL"""
    
    # Initialize services
    logger.info("Initializing services...")
    bq_service = BigQueryService()
    
    pg_config = {
        'host': '35.184.61.42',
        'port': 5432,
        'database': 'prepsense',
        'user': 'postgres',
        'password': 'changeme123!'
    }
    pg_service = PostgresService(pg_config)
    
    # Get all pantry items from BigQuery
    logger.info("Fetching pantry items from BigQuery...")
    query = """
    SELECT 
        pantry_item_id,
        pantry_id,
        quantity,
        unit_of_measurement,
        expiration_date,
        unit_price,
        total_price,
        pantry_item_created_at as created_at,
        pantry_item_created_at as updated_at,
        NULL as consumed_at,
        used_quantity,
        status,
        product_id,
        product_name,
        brand_name,
        food_category as category,
        'manual' as source
    FROM `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
    WHERE user_id = 111
    """
    
    items = bq_service.execute_query(query)
    logger.info(f"Found {len(items)} items to migrate")
    
    if not items:
        logger.info("No items to migrate")
        return
    
    # Insert items into PostgreSQL
    logger.info("Inserting items into PostgreSQL...")
    success_count = 0
    error_count = 0
    
    for item in items:
        try:
            # Insert into pantry_items
            insert_query = """
            INSERT INTO pantry_items (
                pantry_item_id, pantry_id, product_name, brand_name, category,
                quantity, unit_of_measurement, expiration_date, unit_price, total_price,
                source, status, created_at, updated_at, consumed_at, used_quantity
            ) VALUES (
                %(pantry_item_id)s, %(pantry_id)s, %(product_name)s, %(brand_name)s, %(category)s,
                %(quantity)s, %(unit_of_measurement)s, %(expiration_date)s, %(unit_price)s, %(total_price)s,
                %(source)s, %(status)s, %(created_at)s, %(updated_at)s, %(consumed_at)s, %(used_quantity)s
            )
            ON CONFLICT (pantry_item_id) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
            """
            
            pg_service.execute_query(insert_query, item)
            success_count += 1
            
            if success_count % 50 == 0:
                logger.info(f"Progress: {success_count}/{len(items)} items migrated...")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error migrating item {item.get('pantry_item_id')}: {e}")
            if error_count > 10:
                logger.error("Too many errors, stopping migration")
                break
    
    # Update sequence
    logger.info("Updating sequence...")
    pg_service.execute_query("""
        SELECT setval('pantry_items_pantry_item_id_seq', 
               (SELECT MAX(pantry_item_id) FROM pantry_items))
    """)
    
    logger.info(f"\nMigration complete!")
    logger.info(f"  Successfully migrated: {success_count} items")
    logger.info(f"  Errors: {error_count} items")
    
    # Verify
    verify_query = "SELECT COUNT(*) as count FROM pantry_items WHERE pantry_id = 1"
    result = pg_service.execute_query(verify_query)
    logger.info(f"  Total items in PostgreSQL: {result[0]['count']}")
    
    pg_service.close()

if __name__ == "__main__":
    migrate_pantry_items()