"""Unit tests for the :mod:`BigQueryService` class."""

import pytest
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
from google.cloud import bigquery
from google.oauth2 import service_account

# Import the service to test
from backend_gateway.services.bigquery_service import BigQueryService

# Test configuration
TEST_PROJECT_ID = "test-project"
TEST_DATASET_ID = "test_dataset"
TEST_CREDENTIALS_PATH = "/path/to/test/credentials.json"

# Test data
TEST_TABLE_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("quantity", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("is_active", "BOOLEAN", mode="NULLABLE"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
]

@pytest.fixture
def mock_bigquery_client(monkeypatch):
    """Mock the BigQuery client."""
    # Create a mock client
    mock_client = MagicMock()
    
    # Mock the query method
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = []
    mock_client.query.return_value = mock_query_job
    
    # Mock the insert_rows_json method
    mock_client.insert_rows_json.return_value = []
    
    # Mock the get_table method
    mock_table = MagicMock()
    mock_table.schema = TEST_TABLE_SCHEMA
    mock_client.get_table.return_value = mock_table
    
    # Patch the BigQuery client to return our mock
    with patch('google.cloud.bigquery.Client', return_value=mock_client):
        yield mock_client

def test_bigquery_service_init(mock_bigquery_client):
    """Test BigQueryService initialization."""
    # Initialize the service without credentials (should use default credentials)
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Verify client was initialized
    assert service.client is not None

def test_execute_query(mock_bigquery_client):
    """Test executing a query."""
    # Setup mock query result
    mock_rows = [
        {"id": 1, "name": "Test Item 1", "quantity": 10.5, "is_active": True},
        {"id": 2, "name": "Test Item 2", "quantity": 20.0, "is_active": False},
    ]
    
    # Configure the mock client
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = mock_rows
    mock_bigquery_client.query.return_value = mock_query_job
    
    # Initialize the service
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Execute a test query
    query = "SELECT * FROM test_table"
    result = service.execute_query(query)
    
    # Verify the query was executed
    mock_bigquery_client.query.assert_called_once()
    assert result == mock_rows

def test_insert_rows(mock_bigquery_client):
    """Test inserting rows."""
    # Configure the mock insert job
    mock_bigquery_client.insert_rows_json.return_value = []
    
    # Initialize the service
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Test data
    rows = [
        {"id": 1, "name": "Test Item 1", "quantity": 10.5},
        {"id": 2, "name": "Test Item 2", "quantity": 20.0},
    ]
    
    # Insert rows
    result = service.insert_rows("test_table", rows)
    
    # Verify the rows were inserted
    mock_bigquery_client.insert_rows_json.assert_called_once()
    assert result == len(rows)

def test_update_rows(mock_bigquery_client):
    """Test updating rows in a table."""
    # Configure the mock query job
    mock_query_job = MagicMock()
    mock_query_job.num_dml_affected_rows = 1
    mock_bigquery_client.query.return_value = mock_query_job
    
    # Initialize the service
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Update data
    updates = {"quantity": 15.0, "is_active": False}
    where_conditions = {"id": 1}
    
    # Update rows
    result = service.update_rows("test_table", updates, where_conditions)
    
    # Verify the query was executed
    mock_bigquery_client.query.assert_called_once()
    
    # Verify the number of affected rows
    assert result == 1
    
    # Verify the query contains the expected table reference
    actual_query = mock_bigquery_client.query.call_args[0][0]
    assert f'`{TEST_PROJECT_ID}.{TEST_DATASET_ID}.test_table`' in actual_query

def test_delete_rows(mock_bigquery_client):
    """Test deleting rows."""
    # Configure the mock query job
    mock_query_job = MagicMock()
    mock_query_job.num_dml_affected_rows = 1
    mock_bigquery_client.query.return_value = mock_query_job
    
    # Initialize the service
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Delete condition
    where_conditions = {"id": 1}
    
    # Delete rows
    result = service.delete_rows("test_table", where_conditions)
    
    # Get the actual query that was executed
    actual_call = mock_bigquery_client.query.call_args[0][0]
    
    # Verify the query contains the expected components
    assert f'`{TEST_PROJECT_ID}.{TEST_DATASET_ID}.test_table`' in actual_call
    assert 'WHERE id = @id' in actual_call
    
    # Verify the parameters
    query_config = mock_bigquery_client.query.call_args[1]["job_config"]
    params = {p.name: p.value for p in query_config.query_parameters}
    assert params == {"id": 1}
    
    assert result == 1  # One row affected

def test_get_schema(mock_bigquery_client):
    """Test getting table schema."""
    # Create a mock table with schema
    mock_table = MagicMock()
    mock_table.schema = TEST_TABLE_SCHEMA
    mock_bigquery_client.get_table.return_value = mock_table
    
    # Initialize the service
    service = BigQueryService(
        project_id=TEST_PROJECT_ID,
        dataset_id=TEST_DATASET_ID
    )
    
    # Get schema
    schema = service.get_schema("test_table")
    
    # Verify the schema was retrieved
    mock_bigquery_client.get_table.assert_called_once_with(
        f"{TEST_PROJECT_ID}.{TEST_DATASET_ID}.test_table"
    )
    
    # Verify the schema fields match
    assert len(schema) == len(TEST_TABLE_SCHEMA)
    for i, field in enumerate(schema):
        # Convert SchemaField to dict for comparison
        field_dict = {
            'name': field['name'],
            'type': field['type'],
            'mode': field['mode']
        }
        expected_field = {
            'name': TEST_TABLE_SCHEMA[i].name,
            'type': TEST_TABLE_SCHEMA[i].field_type,
            'mode': TEST_TABLE_SCHEMA[i].mode
        }
        assert field_dict == expected_field

def actual_query_clean(query: str) -> str:
    """Remove extra whitespace from SQL queries for comparison."""
    return ' '.join(query.split())

def _format_query_results(results):
    """Helper function to format query results in a readable table."""
    if not results:
        return "No results returned"
    
    # Convert all values to strings and find max width for each column
    str_rows = []
    for row in results:
        str_rows.append({k: str(v) for k, v in row.items()})
    
    # Get max width for each column
    headers = list(results[0].keys())
    col_widths = {}
    for h in headers:
        max_len = max(len(h), max(len(row.get(h, '')) for row in str_rows))
        col_widths[h] = min(max_len, 30)  # Cap width at 30 characters for readability
    
    # Build the formatted output
    lines = []
    
    # Header
    header = " | ".join(h.ljust(col_widths[h]) for h in headers)
    separator = "-" * len(header)
    lines.append(separator)
    lines.append(header)
    lines.append(separator)
    
    # Rows
    for row in str_rows:
        line = " | ".join(
            (row.get(h, '')[:27] + '...' if len(row.get(h, '')) > 30 else row.get(h, '')).ljust(col_widths[h])
            for h in headers
        )
        lines.append(line)
    
    lines.append(separator)
    return "\n".join(lines)

@pytest.mark.integration
def test_integration_with_real_bigquery():
    """Integration test with real BigQuery."""
    # Test query
    query = """
        SELECT pantry_item_id, pantry_id, quantity, unit_of_measurement
        FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
        LIMIT 5
    """
    
    # Print the query that would be executed
    print("\n" + "="*80)
    print("DRY RUN - Query that would be executed:")
    print("-" * 80)
    print(query.strip())
    print("="*80 + "\n")
    
    # Show sample output format
    sample_data = [
        {
            "pantry_item_id": "12345",
            "pantry_id": "pantry_1",
            "quantity": 2.5,
            "unit_of_measurement": "kg"
        },
        {
            "pantry_item_id": "12346",
            "pantry_id": "pantry_1",
            "quantity": 1.0,
            "unit_of_measurement": "liter"
        },
        {
            "pantry_item_id": "12347",
            "pantry_id": "pantry_2",
            "quantity": 3,
            "unit_of_measurement": "pieces"
        }
    ]
    
    print("Example of how the results would be displayed:")
    print(_format_query_results(sample_data))
    
    # Check if we should actually run the query
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or not os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')):
        print("\n" + "!"*80)
        print("NOTE: To execute this query against the real database, set GOOGLE_APPLICATION_CREDENTIALS")
        print("!"*80 + "\n")
        return  # Skip the actual execution
    
    try:
        # Initialize the service with real credentials
        service = BigQueryService(
            project_id=os.getenv('BIGQUERY_PROJECT_ID'),
            dataset_id=os.getenv('BIGQUERY_DATASET')
        )
        
        # Execute the real query
        print("\nExecuting query against BigQuery...\n")
        result = service.execute_query(query)
        
        # Print the results
        print("Query Results:")
        print(_format_query_results(result))
        
        # Verify the structure
        assert isinstance(result, list)
        if result:
            assert all(isinstance(row, dict) for row in result)
            assert all("pantry_item_id" in row for row in result)
            
    except Exception as e:
        print(f"\nError executing query: {str(e)}")
        pytest.fail(f"Integration test failed: {str(e)}")

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "tests/test_bigquery_service.py"])
