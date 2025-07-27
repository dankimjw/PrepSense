# Database Scripts

This folder contains all database-related scripts for the PrepSense project.

## Organization

### Core Scripts
- **Query Utilities**
  - `query_usda.py` - USDA database query utility
  - `test_pantry_query.py` - Test pantry queries
  
- **Migration Scripts**
  - `apply_semantic_search_migration.py` - Apply semantic search
  - `run_user_recipes_migration.py` - User recipes migration
  - `run_external_recipe_migration.py` - External recipe support
  - `run_missing_columns_migration.py` - Add missing columns
  
- **Data Import Scripts**
  - `import_usda_data_fixed.py` - Import USDA food data
  - `import_usda_unit_mappings.py` - Import USDA unit mappings
  - `populate_embeddings.py` - Populate vector embeddings
  - `populate_environmental_data.py` - Import environmental impact data
  
- **Setup Scripts**
  - `setup_cloud_sql_postgres.py` - Setup Cloud SQL
  - `configure_database.py` - Configure database connection
  - `setup_usda_tables.py` - Setup USDA tables
  
- **Test Scripts**
  - `test_usda_api.py` - Test USDA API
  - `test_usda_queries.py` - Test USDA queries
  - `test_usda_simple.py` - Simple USDA tests
  - `check_database_schema.py` - Check schema
  - `check_embedding_status.py` - Check embeddings
  
### SQL Files
- **Migrations** - SQL migration files
- **Schema** - Database schema definitions
- **Tables** - Individual table creation scripts

## Usage

Most Python scripts can be run directly:
```bash
python query_usda.py --help
python import_usda_data_fixed.py
```

SQL files should be run via psql or through a migration script:
```bash
psql $DATABASE_URL < migrations/create_usda_food_tables.sql
```