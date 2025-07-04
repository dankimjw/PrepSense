#!/usr/bin/env python3
"""
Simple script to execute the user_recipes SQL without importing all services.
This script directly uses the BigQuery client to avoid dependency issues.
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def split_sql_statements(sql_content: str) -> list[str]:
    """Split SQL content into individual statements."""
    statements = []
    current_statement = []
    in_multiline_comment = False
    
    for line in sql_content.split('\n'):
        # Skip single-line comments and empty lines
        stripped = line.strip()
        
        # Handle multi-line comments
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
            
        if in_multiline_comment:
            continue
            
        if not stripped or stripped.startswith('--'):
            continue
            
        current_statement.append(line)
        
        # Check if this line ends a statement
        if stripped.endswith(';'):
            # Join all lines and add to statements
            full_statement = '\n'.join(current_statement).strip()
            if full_statement and not full_statement.startswith('/*'):
                statements.append(full_statement)
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        full_statement = '\n'.join(current_statement).strip()
        if full_statement and not full_statement.startswith('/*'):
            statements.append(full_statement)
    
    return statements


def main():
    """Main function to execute the SQL."""
    print("\n" + "="*60)
    print("PrepSense - User Recipes Table Setup (Direct)")
    print("="*60)
    
    # Get configuration from environment
    project_id = os.getenv('GCP_PROJECT_ID', 'adsp-34002-on02-prep-sense')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'Inventory')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # If credentials path not in env, check default location
    if not credentials_path:
        default_creds_path = Path(__file__).parent.parent.parent / "config" / "adsp-34002-on02-prep-sense-ef1111b0833b.json"
        if default_creds_path.exists():
            credentials_path = str(default_creds_path)
            logger.info(f"Using credentials from default location: {credentials_path}")
    
    if not project_id:
        logger.error("GCP_PROJECT_ID not found in environment variables")
        return 1
    
    logger.info(f"Project ID: {project_id}")
    logger.info(f"Dataset ID: {dataset_id}")
    
    # Expand ~ in credentials path if present
    if credentials_path and credentials_path.startswith('~'):
        credentials_path = os.path.expanduser(credentials_path)
    
    # Initialize BigQuery client
    try:
        if credentials_path and os.path.exists(credentials_path):
            logger.info(f"Using credentials from: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            logger.info("Using application default credentials")
            client = bigquery.Client(project=project_id)
        
        logger.info("✓ BigQuery client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize BigQuery client: {str(e)}")
        return 1
    
    # Locate SQL file
    sql_file = Path(__file__).parent.parent / "sql" / "create_or_update_user_recipes_table.sql"
    
    if not sql_file.exists():
        logger.error(f"SQL file not found: {sql_file}")
        return 1
    
    logger.info(f"\nReading SQL from: {sql_file}")
    
    try:
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements
        statements = split_sql_statements(sql_content)
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            # Get a preview of the statement for logging
            preview = statement[:100].replace('\n', ' ')
            if len(statement) > 100:
                preview += '...'
            
            logger.info(f"\nExecuting statement {i}/{len(statements)}: {preview}")
            
            try:
                # Execute the statement
                query_job = client.query(statement)
                query_job.result()  # Wait for completion
                logger.info(f"✓ Statement {i} executed successfully")
                
            except Exception as e:
                logger.error(f"✗ Error executing statement {i}: {str(e)}")
                # Continue with other statements even if one fails
                continue
        
        logger.info("\n✓ All SQL statements processed")
        
        # Verify table creation
        logger.info("\nVerifying table creation...")
        
        try:
            # Check if table exists
            query = f"""
            SELECT 
                table_name,
                TIMESTAMP_MILLIS(creation_time) as creation_time,
                row_count
            FROM `{project_id}.{dataset_id}.__TABLES__`
            WHERE table_name = 'user_recipes'
            """
            
            query_job = client.query(query)
            results = list(query_job.result())
            
            if results:
                table_info = results[0]
                logger.info(f"✓ Table 'user_recipes' exists")
                logger.info(f"  Created: {table_info.get('creation_time', 'N/A')}")
                logger.info(f"  Row count: {table_info.get('row_count', 0)}")
                
                print("\n" + "="*60)
                print("Setup completed successfully!")
                print("The user_recipes table has been created/updated in BigQuery.")
                print("="*60)
                
                return 0
            else:
                logger.error("✗ Table 'user_recipes' not found after creation")
                return 1
                
        except Exception as e:
            logger.error(f"Error verifying table: {str(e)}")
            return 1
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())