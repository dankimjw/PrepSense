# User Recipes Table Setup Guide

This guide explains how to create the enhanced `user_recipes` table in BigQuery for the My Recipes feature.

## Prerequisites

1. Access to the BigQuery console or `bq` command-line tool
2. Permissions to create tables in the `adsp-34002-on02-prep-sense.Inventory` dataset
3. Google Cloud credentials configured

## Table Overview

The `user_recipes` table stores:
- User's saved recipes from various sources (Spoonacular, AI-generated, custom)
- User ratings (thumbs up/down)
- Recipe metadata (prep time, cuisine, dietary info)
- Tracking data (times cooked, last cooked date)
- Personal notes and tags

## Setup Instructions

### Option 1: Using BigQuery Console (Recommended)

1. Go to the [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Select your project: `adsp-34002-on02-prep-sense`
3. Navigate to the `Inventory` dataset
4. Click "CREATE TABLE" or if updating existing table, click on the three dots menu and select "Query table"
5. Copy and paste the SQL from `create_or_update_user_recipes_table.sql`
6. Click "RUN" to execute

### Option 2: Using bq Command-Line Tool

```bash
# First, authenticate if needed
gcloud auth login

# Set your project
gcloud config set project adsp-34002-on02-prep-sense

# Execute the SQL file
bq query --use_legacy_sql=false < create_or_update_user_recipes_table.sql
```

### Option 3: Using Python Script

```python
from google.cloud import bigquery
from google.oauth2 import service_account

# Load credentials
credentials = service_account.Credentials.from_service_account_file(
    'path/to/your/credentials.json'
)

# Initialize client
client = bigquery.Client(
    credentials=credentials,
    project='adsp-34002-on02-prep-sense'
)

# Read SQL file
with open('create_or_update_user_recipes_table.sql', 'r') as f:
    sql = f.read()

# Execute each statement separately (BigQuery doesn't support multiple statements)
statements = sql.split(';')
for statement in statements:
    if statement.strip():
        query_job = client.query(statement)
        query_job.result()
        print(f"Executed: {statement[:50]}...")
```

## Table Schema Details

### Core Fields
- `id` (STRING): Unique identifier for each saved recipe
- `user_id` (INTEGER): References the `user` table
- `recipe_id` (INTEGER): External recipe ID (e.g., from Spoonacular)
- `recipe_title` (STRING): Recipe name
- `recipe_data` (JSON): Complete recipe information

### User Interaction Fields
- `rating` (STRING): 'thumbs_up', 'thumbs_down', or 'neutral'
- `is_favorite` (BOOL): Quick favorite flag
- `notes` (STRING): User's personal notes
- `times_cooked` (INTEGER): How many times the user has made this recipe
- `last_cooked_at` (TIMESTAMP): When the recipe was last cooked

### Recipe Metadata
- `prep_time`, `cook_time`, `total_time` (INTEGER): Time in minutes
- `servings` (INTEGER): Number of servings
- `difficulty` (STRING): Recipe difficulty level
- `cuisine` (ARRAY<STRING>): Cuisine types
- `dish_type` (ARRAY<STRING>): Dish categories
- `diet_labels` (ARRAY<STRING>): Dietary restrictions
- `tags` (ARRAY<STRING>): User-defined tags

## Key Relationships

```
user (user_id) ─────┬──> user_recipes (user_id)
                    │
                    ├──> pantry (user_id)
                    │
                    └──> user_preference (user_id)
```

## Testing the Table

After creating the table, test it with:

```sql
-- Check if table was created
SELECT table_name 
FROM `adsp-34002-on02-prep-sense.Inventory.INFORMATION_SCHEMA.TABLES`
WHERE table_name = 'user_recipes';

-- Insert a test record
INSERT INTO `adsp-34002-on02-prep-sense.Inventory.user_recipes` 
(id, user_id, recipe_id, recipe_title, recipe_data, source, created_at, updated_at)
VALUES
(GENERATE_UUID(), 111, 123456, 'Test Recipe', 
 JSON '{"test": true}', 'spoonacular', 
 CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

-- Query the test record
SELECT * FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE user_id = 111;
```

## API Endpoints

Once the table is created, the following endpoints will be available:

- `POST /api/v1/user-recipes` - Save a recipe
- `GET /api/v1/user-recipes` - Get saved recipes
- `PUT /api/v1/user-recipes/{id}/rating` - Update rating
- `DELETE /api/v1/user-recipes/{id}` - Delete recipe
- `POST /api/v1/user-recipes/{id}/cooked` - Mark as cooked
- `GET /api/v1/user-recipes/stats` - Get user statistics

## Troubleshooting

### Permission Errors
If you get permission errors, ensure your account has:
- `bigquery.tables.create` permission
- `bigquery.tables.update` permission
- Access to the `Inventory` dataset

### Table Already Exists
If the table already exists and you want to modify it:
1. Back up existing data first
2. Use ALTER TABLE statements for simple changes
3. Or drop and recreate for major schema changes

### Data Type Issues
- Arrays in BigQuery use `ARRAY<TYPE>` syntax
- JSON fields require `PARSE_JSON()` when inserting string data
- Timestamps should use `CURRENT_TIMESTAMP()` or ISO format strings