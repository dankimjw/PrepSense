#!/usr/bin/env python3
"""
Script to create or update the user_recipes table in BigQuery
Run this script to set up the enhanced user_recipes table with all new fields
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()

def execute_bigquery_script():
    """Execute the SQL script to create/update user_recipes table"""
    
    # Get configuration from environment
    project_id = os.getenv('GCP_PROJECT_ID', 'adsp-34002-on02-prep-sense')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'Inventory')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"Project ID: {project_id}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Credentials Path: {credentials_path}")
    
    # Initialize BigQuery client
    if credentials_path and os.path.exists(os.path.expanduser(credentials_path)):
        credentials = service_account.Credentials.from_service_account_file(
            os.path.expanduser(credentials_path)
        )
        client = bigquery.Client(credentials=credentials, project=project_id)
    else:
        # Use application default credentials
        client = bigquery.Client(project=project_id)
    
    print("\nConnected to BigQuery successfully!")
    
    # Read the SQL script
    sql_file_path = Path(__file__).parent.parent / 'sql' / 'create_or_update_user_recipes_table.sql'
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Split the SQL content by semicolons to handle multiple statements
    # BigQuery doesn't support multiple statements in one query
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip comment lines
        if line.strip().startswith('--') or line.strip().startswith('/*'):
            continue
        # Skip lines that are part of multi-line comments
        if '*/' in line:
            continue
            
        current_statement.append(line)
        
        # If line ends with semicolon, we have a complete statement
        if line.strip().endswith(';'):
            full_statement = '\n'.join(current_statement).strip()
            if full_statement and not full_statement.startswith('--'):
                # Remove the trailing semicolon
                full_statement = full_statement.rstrip(';')
                statements.append(full_statement)
            current_statement = []
    
    # Filter out any remaining comment blocks or empty statements
    statements = [stmt for stmt in statements if stmt and not stmt.strip().startswith('/*')]
    
    print(f"\nFound {len(statements)} SQL statements to execute")
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        try:
            print(f"\n{'='*60}")
            print(f"Executing statement {i}/{len(statements)}:")
            print(f"{statement[:100]}..." if len(statement) > 100 else statement)
            
            # Skip pure comment blocks
            if statement.strip().startswith('/*') and statement.strip().endswith('*/'):
                print("Skipping comment block")
                continue
                
            # Configure and run query
            job_config = bigquery.QueryJobConfig(use_legacy_sql=False)
            query_job = client.query(statement, job_config=job_config)
            
            # Wait for query to complete
            results = query_job.result()
            
            # Check if it was a DML statement (INSERT, UPDATE, DELETE)
            if hasattr(query_job, 'num_dml_affected_rows') and query_job.num_dml_affected_rows is not None:
                print(f"✓ Success! Affected {query_job.num_dml_affected_rows} rows")
            else:
                print("✓ Success!")
                
        except Exception as e:
            print(f"✗ Error executing statement: {str(e)}")
            # Continue with next statement instead of failing completely
            continue
    
    print(f"\n{'='*60}")
    print("Table setup completed!")
    
    # Verify the table exists
    print("\nVerifying table creation...")
    table_id = f"{project_id}.{dataset_id}.user_recipes"
    
    try:
        table = client.get_table(table_id)
        print(f"✓ Table '{table_id}' exists")
        print(f"  - Total rows: {table.num_rows}")
        print(f"  - Created: {table.created}")
        print(f"  - Schema fields: {len(table.schema)}")
        
        # List all fields
        print("\n  Table schema:")
        for field in table.schema:
            print(f"    - {field.name} ({field.field_type})")
            
    except Exception as e:
        print(f"✗ Could not verify table: {str(e)}")
    
    # Test with a sample query
    print("\nTesting table with sample query...")
    test_query = f"""
    SELECT COUNT(*) as count 
    FROM `{project_id}.{dataset_id}.user_recipes`
    """
    
    try:
        query_job = client.query(test_query)
        results = query_job.result()
        for row in results:
            print(f"✓ Table has {row.count} existing records")
    except Exception as e:
        print(f"✗ Error testing table: {str(e)}")

if __name__ == "__main__":
    print("User Recipes Table Setup Script")
    print("==============================")
    
    try:
        execute_bigquery_script()
        print("\n✓ Setup completed successfully!")
    except Exception as e:
        print(f"\n✗ Setup failed: {str(e)}")
        sys.exit(1)