#!/usr/bin/env python3
"""
Migration script from BigQuery to PostgreSQL for PrepSense
Handles data migration with proper type conversions and relationship mapping
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_batch
from google.cloud import bigquery
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigQueryToPostgresMigrator:
    def __init__(self, project_id: str, postgres_config: Dict[str, str]):
        """Initialize migrator with BigQuery and PostgreSQL connections"""
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.pg_config = postgres_config
        self.pg_conn = None
        self.pg_cursor = None
        
    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config.get('port', 5432),
                database=self.pg_config['database'],
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            self.pg_cursor = self.pg_conn.cursor()
            logger.info("Connected to PostgreSQL successfully")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
            
    def close_connections(self):
        """Close database connections"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        logger.info("Closed database connections")
        
    def migrate_users(self):
        """Migrate users table from BigQuery to PostgreSQL"""
        logger.info("Migrating users...")
        
        query = """
        SELECT user_id, username, email, first_name, last_name, 
               password_hash, role, created_at, updated_at
        FROM `adsp-34002-on02-prep-sense.Inventory.users`
        ORDER BY user_id
        """
        
        try:
            # Fetch from BigQuery
            results = list(self.bq_client.query(query))
            logger.info(f"Found {len(results)} users to migrate")
            
            if not results:
                return
                
            # Prepare insert statement
            insert_sql = """
            INSERT INTO users (user_id, username, email, first_name, last_name, 
                             password_hash, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                email = EXCLUDED.email,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                updated_at = CURRENT_TIMESTAMP
            """
            
            # Convert BigQuery rows to tuples
            data = []
            for row in results:
                data.append((
                    row.user_id,
                    row.username,
                    row.email,
                    row.first_name,
                    row.last_name,
                    row.password_hash,
                    row.role,
                    row.created_at,
                    row.updated_at or row.created_at
                ))
            
            # Batch insert
            execute_batch(self.pg_cursor, insert_sql, data)
            self.pg_conn.commit()
            
            # Reset sequence
            self.pg_cursor.execute("SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users))")
            self.pg_conn.commit()
            
            logger.info(f"Successfully migrated {len(data)} users")
            
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            self.pg_conn.rollback()
            raise
            
    def migrate_pantries(self):
        """Migrate pantries table"""
        logger.info("Migrating pantries...")
        
        query = """
        SELECT pantry_id, user_id, pantry_name, created_at
        FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
        ORDER BY pantry_id
        """
        
        try:
            results = list(self.bq_client.query(query))
            logger.info(f"Found {len(results)} pantries to migrate")
            
            if not results:
                return
                
            insert_sql = """
            INSERT INTO pantries (pantry_id, user_id, pantry_name, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (pantry_id) DO UPDATE SET
                pantry_name = EXCLUDED.pantry_name
            """
            
            data = [(row.pantry_id, row.user_id, row.pantry_name, row.created_at) 
                    for row in results]
            
            execute_batch(self.pg_cursor, insert_sql, data)
            self.pg_conn.commit()
            
            # Reset sequence
            self.pg_cursor.execute("SELECT setval('pantries_pantry_id_seq', (SELECT MAX(pantry_id) FROM pantries))")
            self.pg_conn.commit()
            
            logger.info(f"Successfully migrated {len(data)} pantries")
            
        except Exception as e:
            logger.error(f"Error migrating pantries: {e}")
            self.pg_conn.rollback()
            raise
            
    def migrate_pantry_items(self, batch_size: int = 1000):
        """Migrate pantry items with batching for large datasets"""
        logger.info("Migrating pantry items...")
        
        # First get total count
        count_query = """
        SELECT COUNT(*) as total
        FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
        """
        
        total_count = list(self.bq_client.query(count_query))[0].total
        logger.info(f"Total pantry items to migrate: {total_count}")
        
        # Migrate in batches
        offset = 0
        migrated = 0
        
        while offset < total_count:
            query = f"""
            SELECT pantry_item_id, pantry_id, quantity, unit_of_measurement,
                   expiration_date, unit_price, total_price, source, status,
                   created_at, updated_at, consumed_at, used_quantity,
                   category, brand_name
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items` pi
            LEFT JOIN `adsp-34002-on02-prep-sense.Inventory.products` p
                ON pi.pantry_item_id = p.pantry_item_id
            ORDER BY pi.pantry_item_id
            LIMIT {batch_size} OFFSET {offset}
            """
            
            try:
                results = list(self.bq_client.query(query))
                
                if not results:
                    break
                    
                # Also get product names for these items
                item_ids = [row.pantry_item_id for row in results]
                product_query = f"""
                SELECT pantry_item_id, product_name
                FROM `adsp-34002-on02-prep-sense.Inventory.products`
                WHERE pantry_item_id IN UNNEST(@item_ids)
                """
                
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ArrayQueryParameter("item_ids", "INT64", item_ids)
                    ]
                )
                
                product_results = {row.pantry_item_id: row.product_name 
                                 for row in self.bq_client.query(product_query, job_config=job_config)}
                
                insert_sql = """
                INSERT INTO pantry_items (
                    pantry_item_id, pantry_id, product_name, brand_name, category,
                    quantity, unit_of_measurement, expiration_date, unit_price, 
                    total_price, source, status, created_at, updated_at, 
                    consumed_at, used_quantity, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pantry_item_id) DO UPDATE SET
                    quantity = EXCLUDED.quantity,
                    expiration_date = EXCLUDED.expiration_date,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                data = []
                for row in results:
                    product_name = product_results.get(row.pantry_item_id, "Unknown Product")
                    
                    # Create metadata JSON
                    metadata = {}
                    if row.consumed_at:
                        metadata['consumed_at'] = row.consumed_at.isoformat()
                    
                    data.append((
                        row.pantry_item_id,
                        row.pantry_id,
                        product_name,
                        row.brand_name,
                        row.category or 'Uncategorized',
                        float(row.quantity) if row.quantity else 0.0,
                        row.unit_of_measurement,
                        row.expiration_date,
                        float(row.unit_price) if row.unit_price else None,
                        float(row.total_price) if row.total_price else None,
                        row.source or 'manual',
                        row.status or 'available',
                        row.created_at,
                        row.updated_at or row.created_at,
                        row.consumed_at,
                        float(row.used_quantity) if row.used_quantity else 0.0,
                        json.dumps(metadata) if metadata else None
                    ))
                
                execute_batch(self.pg_cursor, insert_sql, data)
                self.pg_conn.commit()
                
                migrated += len(data)
                logger.info(f"Migrated {migrated}/{total_count} pantry items...")
                
                offset += batch_size
                
            except Exception as e:
                logger.error(f"Error migrating pantry items batch at offset {offset}: {e}")
                self.pg_conn.rollback()
                raise
                
        # Reset sequence
        self.pg_cursor.execute("SELECT setval('pantry_items_pantry_item_id_seq', (SELECT MAX(pantry_item_id) FROM pantry_items))")
        self.pg_conn.commit()
        
        logger.info(f"Successfully migrated {migrated} pantry items")
        
    def migrate_user_preferences(self):
        """Migrate user preferences and related tables"""
        logger.info("Migrating user preferences...")
        
        # Migrate main preferences
        query = """
        SELECT user_id, household_size, created_at, updated_at
        FROM `adsp-34002-on02-prep-sense.Inventory.user_preferences`
        """
        
        try:
            results = list(self.bq_client.query(query))
            
            if results:
                insert_sql = """
                INSERT INTO user_preferences (user_id, household_size, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    household_size = EXCLUDED.household_size,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                data = [(row.user_id, row.household_size, row.created_at, 
                        row.updated_at or row.created_at) for row in results]
                
                execute_batch(self.pg_cursor, insert_sql, data)
                self.pg_conn.commit()
                
                logger.info(f"Migrated {len(data)} user preferences")
                
            # Migrate dietary preferences
            self._migrate_preference_table(
                'dietary_preferences', 
                'user_dietary_preferences',
                'dietary_preference'
            )
            
            # Migrate allergens
            self._migrate_preference_table(
                'allergens',
                'user_allergens',
                'allergen'
            )
            
            # Migrate cuisine preferences
            self._migrate_preference_table(
                'cuisine_preferences',
                'user_cuisine_preferences',
                'cuisine_preference'
            )
            
        except Exception as e:
            logger.error(f"Error migrating user preferences: {e}")
            self.pg_conn.rollback()
            raise
            
    def _migrate_preference_table(self, bq_table: str, pg_table: str, column_name: str):
        """Helper to migrate preference tables"""
        query = f"""
        SELECT user_id, {column_name}
        FROM `adsp-34002-on02-prep-sense.Inventory.{bq_table}`
        """
        
        results = list(self.bq_client.query(query))
        
        if results:
            # Clear existing data first
            self.pg_cursor.execute(f"DELETE FROM {pg_table}")
            
            insert_sql = f"""
            INSERT INTO {pg_table} (user_id, {column_name.replace('_preference', '')})
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """
            
            data = [(row.user_id, getattr(row, column_name)) for row in results]
            
            execute_batch(self.pg_cursor, insert_sql, data)
            self.pg_conn.commit()
            
            logger.info(f"Migrated {len(data)} {bq_table}")
            
    def migrate_recipes(self):
        """Migrate recipes and user recipes"""
        logger.info("Migrating recipes...")
        
        # Note: This is a placeholder as the BigQuery schema doesn't show recipe tables
        # You may need to adjust based on your actual schema
        
        # Check if user_recipes exists in BigQuery
        try:
            query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
            LIMIT 10
            """
            results = list(self.bq_client.query(query))
            
            if results:
                # Implement migration logic based on actual schema
                logger.info("User recipes table found but migration not implemented")
            else:
                logger.info("No user recipes to migrate")
                
        except Exception as e:
            logger.info(f"User recipes table not found in BigQuery: {e}")
            
    def verify_migration(self):
        """Verify migration by comparing counts"""
        logger.info("\nVerifying migration...")
        
        tables = [
            ('users', 'users'),
            ('pantry', 'pantries'),
            ('pantry_items', 'pantry_items'),
            ('user_preferences', 'user_preferences')
        ]
        
        for bq_table, pg_table in tables:
            try:
                # BigQuery count
                bq_query = f"SELECT COUNT(*) as count FROM `adsp-34002-on02-prep-sense.Inventory.{bq_table}`"
                bq_count = list(self.bq_client.query(bq_query))[0].count
                
                # PostgreSQL count
                self.pg_cursor.execute(f"SELECT COUNT(*) FROM {pg_table}")
                pg_count = self.pg_cursor.fetchone()[0]
                
                status = "✓" if bq_count == pg_count else "✗"
                logger.info(f"{status} {bq_table}: BigQuery={bq_count}, PostgreSQL={pg_count}")
                
            except Exception as e:
                logger.error(f"Error verifying {bq_table}: {e}")
                
    def run_migration(self):
        """Run the complete migration"""
        try:
            self.connect_postgres()
            
            # Migration order matters due to foreign key constraints
            self.migrate_users()
            self.migrate_pantries()
            self.migrate_pantry_items()
            self.migrate_user_preferences()
            self.migrate_recipes()
            
            # Verify
            self.verify_migration()
            
            logger.info("\nMigration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close_connections()

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate PrepSense data from BigQuery to PostgreSQL')
    parser.add_argument('--project-id', default='adsp-34002-on02-prep-sense',
                       help='Google Cloud project ID')
    parser.add_argument('--pg-host', required=True, help='PostgreSQL host')
    parser.add_argument('--pg-port', default=5432, type=int, help='PostgreSQL port')
    parser.add_argument('--pg-database', default='prepsense', help='PostgreSQL database')
    parser.add_argument('--pg-user', default='postgres', help='PostgreSQL user')
    parser.add_argument('--pg-password', required=True, help='PostgreSQL password')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Test connection without migrating')
    
    args = parser.parse_args()
    
    postgres_config = {
        'host': args.pg_host,
        'port': args.pg_port,
        'database': args.pg_database,
        'user': args.pg_user,
        'password': args.pg_password
    }
    
    migrator = BigQueryToPostgresMigrator(args.project_id, postgres_config)
    
    if args.dry_run:
        logger.info("Dry run - testing connections only")
        migrator.connect_postgres()
        logger.info("PostgreSQL connection successful")
        
        # Test BigQuery
        test_query = "SELECT COUNT(*) FROM `adsp-34002-on02-prep-sense.Inventory.users`"
        count = list(migrator.bq_client.query(test_query))[0][0]
        logger.info(f"BigQuery connection successful - found {count} users")
        
        migrator.close_connections()
    else:
        migrator.run_migration()

if __name__ == "__main__":
    main()