#!/usr/bin/env python3
"""
Script to backup BigQuery tables to local JSON files
This creates local backups that can be version controlled separately or stored locally
"""

import subprocess
import os
import sys
from datetime import datetime
import json

# Configuration
PROJECT_ID = "adsp-34002-on02-prep-sense"
SOURCE_DATASET = "Inventory"
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bigquery_backups")

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

def export_table_to_json(table_name, backup_folder):
    """Export a single table to JSON file"""
    output_file = os.path.join(backup_folder, f"{table_name}.json")
    
    print(f"Exporting {table_name}...")
    
    # Use bq extract to export table to local JSON file
    cmd = [
        "bq", "extract", 
        "--destination_format=NEWLINE_DELIMITED_JSON",
        f"{PROJECT_ID}:{SOURCE_DATASET}.{table_name}",
        f"gs://temp-prepsense-backup/{table_name}.json"
    ]
    
    # First, query the table and save to local file
    query_cmd = [
        "bq", "query",
        "--format=json",
        "--max_rows=100000",
        "--use_legacy_sql=false",
        f"SELECT * FROM `{PROJECT_ID}.{SOURCE_DATASET}.{table_name}`"
    ]
    
    try:
        result = subprocess.run(query_cmd, capture_output=True, text=True, check=True)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        
        # Get row count
        data = json.loads(result.stdout)
        row_count = len(data) if isinstance(data, list) else 0
        
        print(f"✓ Exported {table_name}: {row_count} rows")
        return True, row_count
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to export {table_name}: {e.stderr}")
        return False, 0
    except Exception as e:
        print(f"✗ Failed to export {table_name}: {str(e)}")
        return False, 0

def create_restore_script(backup_folder, tables_info):
    """Create a script to restore from the backup"""
    restore_script = os.path.join(backup_folder, "restore_tables.py")
    
    script_content = '''#!/usr/bin/env python3
"""
Script to restore BigQuery tables from JSON backup
Generated on: {timestamp}
"""

import subprocess
import json
import os
import sys

PROJECT_ID = "{project_id}"
DATASET = "{dataset}"
BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))

TABLES_INFO = {tables_info}

def restore_table(table_name):
    """Restore a single table from JSON"""
    json_file = os.path.join(BACKUP_DIR, f"{{table_name}}.json")
    
    if not os.path.exists(json_file):
        print(f"✗ Backup file not found: {{json_file}}")
        return False
    
    print(f"Restoring {{table_name}}...")
    
    # Create a temporary file for bq load
    temp_file = f"/tmp/{{table_name}}_restore.json"
    
    # Convert JSON array to newline-delimited JSON
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    with open(temp_file, 'w') as f:
        for record in data:
            f.write(json.dumps(record) + '\\n')
    
    # Load data into BigQuery
    cmd = [
        "bq", "load",
        "--replace",
        "--source_format=NEWLINE_DELIMITED_JSON",
        f"{{PROJECT_ID}}:{{DATASET}}.{{table_name}}",
        temp_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        os.remove(temp_file)
        print(f"✓ Restored {{table_name}}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to restore {{table_name}}: {{e.stderr}}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def main():
    print("BigQuery Table Restore")
    print("=" * 50)
    print(f"Target dataset: {{PROJECT_ID}}:{{DATASET}}")
    print(f"Backup location: {{BACKUP_DIR}}")
    print()
    
    if input("Are you sure you want to restore? This will REPLACE existing tables! (yes/no): ").lower() != 'yes':
        print("Restore cancelled.")
        sys.exit(0)
    
    print()
    success_count = 0
    
    for table_name, info in TABLES_INFO.items():
        if restore_table(table_name):
            success_count += 1
    
    print()
    print(f"Restore completed: {{success_count}}/{{len(TABLES_INFO)}} tables restored successfully")

if __name__ == "__main__":
    main()
'''.format(
        timestamp=datetime.now().isoformat(),
        project_id=PROJECT_ID,
        dataset=SOURCE_DATASET,
        tables_info=repr(tables_info)
    )
    
    with open(restore_script, 'w') as f:
        f.write(script_content)
    
    os.chmod(restore_script, 0o755)
    print(f"Created restore script: {restore_script}")

def main():
    # Create backup folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    
    os.makedirs(backup_folder, exist_ok=True)
    
    print(f"BigQuery Local Backup")
    print("=" * 50)
    print(f"Source: {PROJECT_ID}:{SOURCE_DATASET}")
    print(f"Destination: {backup_folder}")
    print()
    
    success_count = 0
    failed_tables = []
    tables_info = {}
    
    for table in TABLES:
        success, row_count = export_table_to_json(table, backup_folder)
        if success:
            success_count += 1
            tables_info[table] = {"rows": row_count}
        else:
            failed_tables.append(table)
    
    # Create metadata file
    metadata = {
        "backup_timestamp": datetime.now().isoformat(),
        "project_id": PROJECT_ID,
        "dataset": SOURCE_DATASET,
        "tables": tables_info,
        "success_count": success_count,
        "failed_tables": failed_tables
    }
    
    with open(os.path.join(backup_folder, "backup_metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create restore script
    create_restore_script(backup_folder, tables_info)
    
    print()
    print("=" * 50)
    print(f"Backup completed: {success_count}/{len(TABLES)} tables exported successfully")
    
    if failed_tables:
        print(f"Failed tables: {', '.join(failed_tables)}")
        sys.exit(1)
    else:
        print(f"✓ All tables backed up successfully to: {backup_folder}")
        print()
        print("To restore from this backup:")
        print(f"  cd {backup_folder}")
        print(f"  python restore_tables.py")

if __name__ == "__main__":
    main()