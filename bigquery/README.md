# BigQuery Archive

This folder contains all BigQuery-related code that was removed from the main PrepSense application when migrating to PostgreSQL.

## Contents

### Services
- `bigquery_service.py` - Core BigQuery service implementation
- `user_recipes_service_old.py` - Old user recipes service using BigQuery

### Routers
- `bigquery_router.py` - API routes for BigQuery operations
- `user_recipes_router_old.py` - Old user recipes router

### Scripts
- Various migration and maintenance scripts that were used with BigQuery

### Frontend
- `bigquery-tester.tsx` - Frontend component for testing BigQuery queries

## Note
These files are kept for reference only. The main application now uses PostgreSQL exclusively.