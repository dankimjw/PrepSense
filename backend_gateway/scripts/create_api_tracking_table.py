#!/usr/bin/env python3
"""
Script to create the spoonacular_api_calls tracking table.
This follows the CLAUDE.md guidelines for database changes against GCP Cloud SQL.
"""
import os
import sys

# Add the parent directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)
sys.path.insert(0, backend_dir)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from backend_gateway.config.database import get_database_service

    logger.info("Successfully imported database service")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Available paths:")
    for path in sys.path:
        logger.info(f"  - {path}")
    sys.exit(1)


def create_api_tracking_table():
    """Create the spoonacular_api_calls table and related objects."""

    # SQL to create the table (adapted for PostgreSQL syntax)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS spoonacular_api_calls (
        id SERIAL PRIMARY KEY,
        
        -- API Call Metadata
        endpoint VARCHAR(100) NOT NULL,
        method VARCHAR(10) NOT NULL DEFAULT 'GET',
        call_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        -- Request Details
        user_id INTEGER,
        request_params JSONB,
        request_size_bytes INTEGER DEFAULT 0,
        
        -- Response Details
        response_status INTEGER,
        response_size_bytes INTEGER DEFAULT 0,
        response_time_ms INTEGER,
        
        -- API Usage Tracking  
        recipe_count INTEGER DEFAULT 0,
        cache_hit BOOLEAN DEFAULT FALSE,
        duplicate_detected BOOLEAN DEFAULT FALSE,
        cost_points INTEGER DEFAULT 1,
        
        -- Error Handling
        error_code VARCHAR(50),
        error_message TEXT,
        retry_attempt INTEGER DEFAULT 0,
        
        -- Recipe Fingerprinting
        recipe_fingerprints TEXT[],
        duplicate_recipe_ids INTEGER[],
        
        -- Additional Metadata
        api_version VARCHAR(10) DEFAULT 'v1',
        client_version VARCHAR(20) DEFAULT 'prepsense-1.0',
        environment VARCHAR(20) DEFAULT 'production'
    );
    """

    # SQL to create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_spoonacular_calls_timestamp ON spoonacular_api_calls (call_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_spoonacular_calls_user_id ON spoonacular_api_calls (user_id);",
        "CREATE INDEX IF NOT EXISTS idx_spoonacular_calls_endpoint ON spoonacular_api_calls (endpoint);",
        "CREATE INDEX IF NOT EXISTS idx_spoonacular_calls_status ON spoonacular_api_calls (response_status);",
        "CREATE INDEX IF NOT EXISTS idx_spoonacular_calls_cache_hit ON spoonacular_api_calls (cache_hit);",
    ]

    # SQL to add comments
    comment_sql = [
        "COMMENT ON TABLE spoonacular_api_calls IS 'Tracks all Spoonacular API calls for usage analytics and cost monitoring';",
        "COMMENT ON COLUMN spoonacular_api_calls.endpoint IS 'Spoonacular API endpoint called (findByIngredients, complexSearch, etc.)';",
        "COMMENT ON COLUMN spoonacular_api_calls.request_params IS 'JSON storage of request parameters for debugging and analytics';",
        "COMMENT ON COLUMN spoonacular_api_calls.cost_points IS 'API cost in points based on endpoint pricing';",
        "COMMENT ON COLUMN spoonacular_api_calls.recipe_fingerprints IS 'Array of recipe fingerprints for deduplication tracking';",
        "COMMENT ON COLUMN spoonacular_api_calls.duplicate_recipe_ids IS 'Array of recipe IDs that were detected as duplicates';",
    ]

    try:
        logger.info("Getting database service...")
        db_service = get_database_service()

        logger.info("Creating spoonacular_api_calls table...")
        result = db_service.execute_query(create_table_sql)

        logger.info("Creating indexes...")
        for index_sql in create_indexes_sql:
            db_service.execute_query(index_sql)

        logger.info("Adding table comments...")
        for comment in comment_sql:
            db_service.execute_query(comment)

        logger.info("✅ Successfully created spoonacular_api_calls table with indexes and comments")

        # Verify table was created
        logger.info("Verifying table creation...")
        columns_result = db_service.execute_query(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'spoonacular_api_calls'
            ORDER BY ordinal_position;
        """
        )

        logger.info(f"Table created with {len(columns_result)} columns:")
        for row in columns_result:
            logger.info(f"  - {row['column_name']}: {row['data_type']}")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating API tracking table: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = create_api_tracking_table()
    sys.exit(0 if success else 1)
