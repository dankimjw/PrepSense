#!/bin/bash

# Set the project and dataset
PROJECT_ID="adsp-34002-on02-prep-sense"
DATASET="Inventory"

echo "Testing connection to BigQuery project: $PROJECT_ID"
echo "============================================"

# List all tables in the dataset
echo "\nListing tables in dataset $DATASET:"
echo "--------------------------------"
bq ls --project_id=$PROJECT_ID $DATASET

# Function to count records in a table
count_records() {
    local table=$1
    local query="SELECT COUNT(*) as record_count FROM \`$PROJECT_ID.$DATASET.$table\`"
    echo "\nCounting records in $table:"
    echo "--------------------------------"
    bq query --use_legacy_sql=false --project_id=$PROJECT_ID "$query"
}

# Count records in each table
for table in pantry pantry_items products recipies user user_preference; do
    count_records $table
done

echo "\nSample data from tables:"
echo "========================"

# Function to get sample data from a table
sample_data() {
    local table=$1
    local limit=3
    echo "\nSample data from $table (first $limit records):"
    echo "--------------------------------"
    bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
        "SELECT * FROM \`$PROJECT_ID.$DATASET.$table\` LIMIT $limit"
    echo ""
}

# Get sample data from each table
for table in pantry pantry_items products recipies user user_preference; do
    sample_data $table
done
