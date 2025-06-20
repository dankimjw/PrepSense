#!/bin/bash

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="/Users/danielkim/_Capstone/PrepSense/adsp-34002-on02-prep-sense-ef1111b0833b.json"
export BIGQUERY_PROJECT="adsp-34002-on02-prep-sense"
export BIGQUERY_DATASET="Inventory"

# Print environment information
echo "Environment Information:"
echo "GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
echo "BIGQUERY_PROJECT: $BIGQUERY_PROJECT"
echo "BIGQUERY_DATASET: $BIGQUERY_DATASET"
echo ""

# Run the server
python run_server.py
