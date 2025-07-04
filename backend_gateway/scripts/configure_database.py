#!/usr/bin/env python3
"""
Configure database settings for PrepSense
Switch between BigQuery and PostgreSQL
"""

import os
import sys
from pathlib import Path

def update_env_file(use_postgres: bool):
    """Update .env file with database configuration"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        return False
        
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
        
    # Update or add database configuration
    db_config_found = False
    new_lines = []
    
    for line in lines:
        # Skip existing DB_TYPE lines
        if line.strip().startswith('DB_TYPE='):
            db_config_found = True
            continue
        # Skip PostgreSQL config lines if switching to BigQuery
        if not use_postgres and any(line.strip().startswith(prefix) for prefix in 
                                   ['POSTGRES_', 'CLOUD_SQL_']):
            continue
        new_lines.append(line)
        
    # Add database configuration
    if use_postgres:
        new_lines.append('\n# Database Configuration\n')
        new_lines.append('DB_TYPE=postgres\n')
        
        # Check if PostgreSQL config exists
        has_pg_config = any('POSTGRES_HOST' in line for line in new_lines)
        if not has_pg_config:
            new_lines.append('\n# PostgreSQL Configuration\n')
            new_lines.append('POSTGRES_HOST=***REMOVED***  # Update with your Cloud SQL IP\n')
            new_lines.append('POSTGRES_PORT=5432\n')
            new_lines.append('POSTGRES_DATABASE=prepsense\n')
            new_lines.append('POSTGRES_USER=postgres\n')
            new_lines.append('POSTGRES_PASSWORD=***REMOVED***  # Update with your password\n')
            new_lines.append('CLOUD_SQL_CONNECTION_NAME=adsp-34002-on02-prep-sense:us-central1:prepsense-postgres\n')
    else:
        new_lines.append('\n# Database Configuration\n')
        new_lines.append('DB_TYPE=bigquery\n')
        
    # Write updated .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        
    return True

def main():
    print("=== PrepSense Database Configuration ===\n")
    print("Select database backend:")
    print("1. PostgreSQL (Cloud SQL) - Better for transactional operations")
    print("2. BigQuery - Current setup, better for analytics")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        print("\nConfiguring for PostgreSQL...")
        if update_env_file(True):
            print("✓ Updated .env file for PostgreSQL")
            print("\nNext steps:")
            print("1. Ensure Cloud SQL instance is running:")
            print("   gcloud sql instances describe prepsense-postgres --project=adsp-34002-on02-prep-sense")
            print("\n2. Run migration if needed:")
            print("   python backend_gateway/scripts/migrate_bigquery_to_postgres.py --pg-host [IP] --pg-password [PASSWORD]")
            print("\n3. Restart the backend:")
            print("   uvicorn backend_gateway.app:app --reload")
    elif choice == '2':
        print("\nConfiguring for BigQuery...")
        if update_env_file(False):
            print("✓ Updated .env file for BigQuery")
            print("\nRestart the backend:")
            print("   uvicorn backend_gateway.app:app --reload")
    else:
        print("Invalid choice!")
        sys.exit(1)

if __name__ == "__main__":
    main()