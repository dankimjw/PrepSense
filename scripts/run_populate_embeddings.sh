#!/bin/bash
# Script to populate embeddings for PrepSense

# Activate virtual environment
source venv/bin/activate

# Export environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run the embedding population script
echo "Starting embedding population..."
echo "This will generate embeddings for all recipes, products, and pantry items."
echo "Using OpenAI API key from .env file."
echo ""

# Run with command line argument if provided
if [ $# -eq 0 ]; then
    python backend_gateway/scripts/populate_embeddings.py
else
    python backend_gateway/scripts/populate_embeddings.py "$@"
fi