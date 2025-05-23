#!/usr/bin/env python3
"""
Integration test script for BigQueryService.

This script tests the BigQueryService with a real BigQuery connection.
Make sure to set the GOOGLE_APPLICATION_CREDENTIALS environment variable
before running this script.

Example:
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
    python scripts/test_bigquery_integration.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.services.bigquery_service import BigQueryService

def test_bigquery_integration():
    """Test BigQueryService with a real BigQuery connection."""
    # Configuration
    project_id = "adsp-34002-on02-prep-sense"
    dataset_id = "Inventory"
    test_table = "pantry_items"
    
    # Initialize the service
    print(f"Initializing BigQueryService with project_id={project_id}, dataset_id={dataset_id}")
    service = BigQueryService(project_id=project_id, dataset_id=dataset_id)
    
    try:
        # Test 1: Get schema
        print("\n=== Testing get_schema ===")
        schema = service.get_schema(test_table)
        print(f"Schema for {test_table}:")
        for field in schema:
            print(f"  - {field['name']}: {field['type']} ({field.get('mode', 'NULLABLE')})")
        
        # Test 2: Execute a simple query
        print("\n=== Testing execute_query ===")
        query = f"""
            SELECT pantry_item_id, pantry_id, quantity, unit_of_measurement
            FROM `{project_id}.{dataset_id}.{test_table}`
            ORDER BY created_at DESC
            LIMIT 5
        """
        rows = service.execute_query(query)
        print(f"Found {len(rows)} rows:")
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row}")
            
        # Test 3: Insert a test record (if you have write permissions)
        print("\n=== Testing insert_rows ===")
        test_data = [
            {
                "pantry_id": 1,  # Replace with a valid pantry_id
                "quantity": 5.0,
                "unit_of_measurement": "pcs",
                "expiration_date": (datetime.now() + timedelta(days=30)).date().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
        ]
        
        try:
            inserted = service.insert_rows(test_table, test_data)
            print(f"Inserted {inserted} row(s)")
            
            # If we successfully inserted, try to query it back
            if inserted > 0:
                print("\n=== Verifying inserted data ===")
                last_insert = service.execute_query(
                    f"""
                    SELECT * FROM `{project_id}.{dataset_id}.{test_table}`
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
                if last_insert:
                    print("Last inserted row:", last_insert[0])
        except Exception as e:
            print(f"Warning: Could not insert test data - {str(e)}")
            print("This is expected if you don't have write permissions.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Check for credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Please set it to the path of your service account key file.")
        print("Example: export GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/your/credentials.json\"")
        sys.exit(1)
    
    # Run the tests
    print("=== Starting BigQuery Integration Tests ===")
    success = test_bigquery_integration()
    
    if success:
        print("\n=== All tests completed successfully! ===")
    else:
        print("\n=== Some tests failed. See above for details. ===")
        sys.exit(1)
