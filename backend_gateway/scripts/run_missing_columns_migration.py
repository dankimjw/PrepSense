#!/usr/bin/env python3
"""
Run migration to add missing columns for BigQuery compatibility
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the missing columns migration"""
    
    # Get database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT', 5432),
        'database': os.getenv('POSTGRES_DATABASE'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }
    
    # Check if using IAM
    if os.getenv('POSTGRES_USE_IAM', '').lower() == 'true':
        logger.info("Using IAM authentication")
        # Import IAM service to get token
        from backend_gateway.services.postgres_iam_service import PostgresIAMService
        iam_service = PostgresIAMService(db_params)
        db_params['password'] = iam_service._get_access_token()
        db_params['user'] = os.getenv('POSTGRES_IAM_USER', db_params['user'])
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL at {db_params['host']}:{db_params['port']}")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Run migration
        logger.info("Running migration to add missing columns...")
        
        # Add product_id column if it doesn't exist
        cursor.execute("""
            ALTER TABLE pantry_items 
            ADD COLUMN IF NOT EXISTS product_id INTEGER;
        """)
        logger.info("Added product_id column (if not exists)")
        
        # Add index for product_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pantry_items_product_id ON pantry_items(product_id);
        """)
        logger.info("Created index on product_id")
        
        # Add comment about upc_code in metadata
        cursor.execute("""
            COMMENT ON COLUMN pantry_items.metadata IS 'JSONB field for flexible attributes including upc_code';
        """)
        logger.info("Added comment about upc_code storage")
        
        # Verify the columns exist
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pantry_items' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        logger.info("\nCurrent pantry_items columns:")
        for col_name, data_type in columns:
            logger.info(f"  - {col_name}: {data_type}")
        
        logger.info("\nMigration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()