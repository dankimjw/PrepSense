#!/usr/bin/env python3
"""
Script to backup all BigQuery tables from Inventory dataset
"""

import subprocess
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "adsp-34002-on02-prep-sense"
SOURCE_DATASET = "Inventory"
BACKUP_DATASET = "Inventory_backup_2025_07_04"

# Tables to backup (excluding views)
TABLES = [
    "pantry",
    "pantry_items",
    "products",
    "recipies",
    "simple_interactions",
    "user",
    "user_preference",
    "user_recipes",
    "users"
]

def copy_table(table_name):
    """Copy a single table to the backup dataset"""
    source_table = f"{PROJECT_ID}:{SOURCE_DATASET}.{table_name}"
    dest_table = f"{PROJECT_ID}:{BACKUP_DATASET}.{table_name}"
    
    print(f"Copying {table_name}...")
    
    cmd = ["bq", "cp", "-f", source_table, dest_table]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Successfully copied {table_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to copy {table_name}: {e.stderr}")
        return False

def main():
    print(f"Starting backup of BigQuery tables")
    print(f"Source: {SOURCE_DATASET}")
    print(f"Destination: {BACKUP_DATASET}")
    print("-" * 50)
    
    success_count = 0
    failed_tables = []
    
    for table in TABLES:
        if copy_table(table):
            success_count += 1
        else:
            failed_tables.append(table)
    
    print("-" * 50)
    print(f"Backup completed: {success_count}/{len(TABLES)} tables copied successfully")
    
    if failed_tables:
        print(f"Failed tables: {', '.join(failed_tables)}")
        sys.exit(1)
    else:
        print("All tables backed up successfully!")
        print(f"\nTo restore from this backup, you can use:")
        print(f"bq cp {PROJECT_ID}:{BACKUP_DATASET}.<table_name> {PROJECT_ID}:{SOURCE_DATASET}.<table_name>")

if __name__ == "__main__":
    main()