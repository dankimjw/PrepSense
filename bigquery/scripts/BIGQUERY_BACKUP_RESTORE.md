# BigQuery Backup and Restore Guide

## Overview
This document explains how to backup and restore the PrepSense BigQuery database locally.

## Backup Strategy
- Backups are stored locally in `/bigquery_backups/` (gitignored)
- Each backup creates a timestamped folder with JSON exports
- Backups include a restore script for easy recovery
- Keep backups in a separate repository or cloud storage for safety

## Backup Process

### Create Local Backup
```bash
cd /path/to/PrepSense
python3 backend_gateway/scripts/backup_bigquery_local.py
```

This will:
1. Create a timestamped folder in `bigquery_backups/`
2. Export all tables as JSON files
3. Generate a restore script
4. Create backup metadata

### Backup Storage Options
1. **Local Only**: Keep in `bigquery_backups/` (gitignored)
2. **Separate Git Repo**: Create a private backup repository
3. **Cloud Storage**: Upload to Google Drive, Dropbox, etc.
4. **BigQuery Dataset**: Use `backup_bigquery_tables.py` for in-cloud backup

## Restore Process

### Restore from Local Backup
1. Navigate to the backup folder:
   ```bash
   cd bigquery_backups/backup_YYYYMMDD_HHMMSS
   ```

2. Run the restore script:
   ```bash
   python3 restore_tables.py
   ```

3. Confirm when prompted (this will REPLACE existing tables)

### Manual Restore
If you need to restore individual tables:
```bash
# Convert JSON to newline-delimited JSON
cat pantry_items.json | jq -c '.[]' > pantry_items_nd.json

# Load into BigQuery
bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  adsp-34002-on02-prep-sense:Inventory.pantry_items \
  pantry_items_nd.json
```

## Important Tables

- **pantry**: Main pantry tracking table
- **pantry_items**: Individual items in pantries
- **products**: Product information
- **recipies**: Recipe data
- **simple_interactions**: User interaction tracking
- **user**: User data (legacy)
- **users**: User data (current)
- **user_preference**: User preferences
- **user_recipes**: Saved recipes per user

## Views (Not Backed Up)
These are automatically recreated from the base tables:
- popular_recipes
- user_pantry_full
- user_recipes_with_user

## Best Practices

1. **Regular Backups**: Create backups before major changes
2. **Test Restores**: Periodically test the restore process
3. **Document Changes**: Keep track of schema changes
4. **Backup Retention**: Keep at least 3 recent backups
5. **Access Control**: Limit who can modify production data

## Troubleshooting

If restore fails:
1. Check that the backup dataset exists: `bq ls`
2. Verify table exists in backup: `bq ls Inventory_backup_2025_07_04`
3. Check permissions: `gcloud auth list`
4. Ensure project is set: `gcloud config get-value project`