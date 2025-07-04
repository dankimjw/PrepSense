# Database Migration Guide

## Overview

PrepSense has migrated from using Google BigQuery as the primary database to a hybrid approach:
- **PostgreSQL (Cloud SQL)** - Primary transactional database for real-time operations
- **Google BigQuery** - Data warehouse for analytics and historical data

## Why the Migration?

### Performance Issues with BigQuery
- Update operations taking 15-30 seconds
- Not designed for transactional workloads
- High latency for real-time operations

### Solution: PostgreSQL for Transactional Data
- Update operations now complete in ~0.5 seconds
- ACID compliance for data integrity
- Better suited for real-time CRUD operations

## Database Architecture

### PostgreSQL Tables (Transactional)
- `users` - User accounts
- `pantries` - User pantries
- `pantry_items` - Current pantry inventory
- `user_recipes` - Saved recipes
- `shopping_list_items` - Shopping list items
- `pantry_history` - Change tracking
- `user_preferences` - Dietary preferences
- `user_dietary_preferences` - Dietary restrictions
- `user_allergens` - Allergen information
- `user_cuisine_preferences` - Cuisine preferences

### BigQuery Tables (Analytics)
- Historical data snapshots
- Aggregated analytics
- Long-term storage
- Reporting queries

## Configuration

### Environment Variables
```bash
# Database type selection
DB_TYPE=postgres  # or 'bigquery' for analytics

# PostgreSQL Configuration
POSTGRES_HOST=35.184.61.42
POSTGRES_PORT=5432
POSTGRES_DATABASE=prepsense
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_USE_IAM=false  # Set to true for production

# BigQuery Configuration (still used for analytics)
GCP_PROJECT=adsp-34002-on02-prep-sense
BIGQUERY_DATASET=Inventory
```

### Connection Details
- **Host**: 35.184.61.42 (Cloud SQL public IP)
- **Port**: 5432
- **Database**: prepsense
- **SSL**: Required for production

## Key Changes

### 1. Service Layer Updates
- `PostgresService` handles all transactional operations
- Automatic query translation from BigQuery syntax
- Connection pooling for better performance

### 2. Query Syntax Changes
| BigQuery | PostgreSQL |
|----------|------------|
| `CURRENT_DATETIME()` | `CURRENT_TIMESTAMP` |
| Backticks `` ` `` | Double quotes `"` |
| `STRING` type | `VARCHAR` or `TEXT` |
| `ARRAY<STRING>` | `TEXT[]` |
| `GENERATE_UUID()` | `gen_random_uuid()` |

### 3. Router Updates
- All pantry operations use PostgreSQL
- Shopping list now persists in database
- User recipes migrated to PostgreSQL

## Migration Status

### ✅ Completed
- Pantry tables and operations
- Shopping list persistence
- User recipes management
- Performance optimization
- Automatic query translation

### 🚧 In Progress
- Complete removal of BigQuery dependencies
- IAM authentication setup
- Data synchronization between systems

### 📋 TODO
- Migrate remaining analytics queries
- Set up data pipeline for BigQuery analytics
- Implement backup and recovery procedures

## Performance Improvements

### Before (BigQuery)
- Item update: 15-30 seconds
- Bulk operations: Often timeout
- Real-time sync: Not feasible

### After (PostgreSQL)
- Item update: ~0.5 seconds
- Bulk operations: 2-3 seconds
- Real-time sync: Instant

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check if Cloud SQL instance is running
   - Verify IP whitelist settings
   - Ensure correct credentials

2. **Query Errors**
   - PostgreSQL uses different syntax
   - Check for BigQuery-specific functions
   - Verify table names (no project prefixes)

3. **Data Type Mismatches**
   - JSON fields use JSONB in PostgreSQL
   - Arrays have different syntax
   - Date/time functions differ

## Backup and Recovery

### PostgreSQL Backups
```bash
# Create backup
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE > backup.sql

# Restore backup
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE < backup.sql
```

### BigQuery Snapshots
- Automated daily snapshots
- Point-in-time recovery available
- Export to Cloud Storage for long-term retention

## Future Improvements

1. **Read Replicas** - For scaling read operations
2. **Connection Pooling** - PgBouncer for better connection management
3. **Caching Layer** - Redis for frequently accessed data
4. **Data Pipeline** - Real-time sync to BigQuery for analytics