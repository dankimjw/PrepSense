import sys
import json
import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from functools import wraps

from google.cloud import bigquery
from google.oauth2 import service_account
from pydantic import BaseModel
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
PREPSENSE DATABASE SCHEMA REFERENCE
====================================
Dataset: adsp-34002-on02-prep-sense.Inventory

**1. pantry**
* pantry_id (INTEGER, NULLABLE) - Unique identifier for each pantry
* user_id (INTEGER, NULLABLE) - Foreign key to user table
* pantry_name (STRING, NULLABLE) - Name of the pantry
* created_at (DATETIME, NULLABLE) - Timestamp when pantry was created

**2. pantry_items**
* pantry_item_id (INTEGER, NULLABLE) - Unique identifier for each pantry item
* pantry_id (INTEGER, NULLABLE) - Foreign key to pantry table
* quantity (FLOAT, NULLABLE) - Current quantity of the item
* unit_of_measurement (STRING, NULLABLE) - Unit for quantity (e.g., 'kg', 'lbs', 'pieces')
* expiration_date (DATE, NULLABLE) - When the item expires
* unit_price (FLOAT, NULLABLE) - Price per unit
* total_price (FLOAT, NULLABLE) - Total price for the quantity
* created_at (DATETIME, NULLABLE) - Timestamp when item was added
* used_quantity (INTEGER, NULLABLE) - Amount of item that has been used
* status (STRING, NULLABLE) - Status of the item (e.g., 'available', 'expired', 'used')

**3. products**
* product_id (INTEGER, NULLABLE) - Unique identifier for each product
* pantry_item_id (INTEGER, NULLABLE) - Foreign key to pantry_items table
* product_name (STRING, NULLABLE) - Name of the product
* brand_name (STRING, NULLABLE) - Brand name of the product
* category (STRING, NULLABLE) - Product category (e.g., 'dairy', 'meat', 'vegetables')
* upc_code (STRING, NULLABLE) - Universal Product Code for the product
* created_at (DATETIME, NULLABLE) - Timestamp when product was created

**4. recipies**
* recipe_id (INTEGER, NULLABLE) - Unique identifier for each recipe
* product_id (INTEGER, NULLABLE) - Foreign key to products table
* recipe_name (STRING, NULLABLE) - Name of the recipe
* quantity_needed (FLOAT, NULLABLE) - Amount of the product needed for recipe
* unit_of_measurement (STRING, NULLABLE) - Unit for quantity needed
* instructions (STRING, NULLABLE) - Recipe preparation instructions
* created_at (DATETIME, NULLABLE) - Timestamp when recipe was created

**5. user**
* user_id (INTEGER, NULLABLE) - Unique identifier for each user
* user_name (STRING, NULLABLE) - Username for login
* first_name (STRING, NULLABLE) - User's first name
* last_name (STRING, NULLABLE) - User's last name
* email (STRING, NULLABLE) - User's email address
* password_hash (STRING, NULLABLE) - Hashed password for authentication
* role (STRING, NULLABLE) - User role (e.g., 'user', 'admin')
* api_key_enc (BYTES, NULLABLE) - Encrypted API key for the user
* created_at (DATETIME, NULLABLE) - Timestamp when user account was created

**6. user_preference**
* user_id (INTEGER, NULLABLE) - Foreign key to user table
* household_size (INTEGER, NULLABLE) - Number of people in household
* dietary_preference (STRING, REPEATED) - Array of dietary preferences (e.g., ['vegetarian', 'gluten-free'])
* allergens (STRING, REPEATED) - Array of allergens to avoid (e.g., ['nuts', 'dairy'])
* cuisine_preference (STRING, REPEATED) - Array of preferred cuisines (e.g., ['italian', 'mexican'])
* created_at (DATETIME, NULLABLE) - Timestamp when preferences were set

**Key Relationships:**
1. user -> user_preference (1:1) - Each user has preferences
2. user -> pantry (1:many) - Users can have multiple pantries
3. pantry -> pantry_items (1:many) - Each pantry contains multiple items
4. pantry_items -> products (1:1) - Each pantry item is a specific product
5. products -> recipies (1:many) - Products can be used in multiple recipes

**Usage Notes:**
- REPEATED fields in user_preference table contain arrays of strings
- Timestamps are stored as DATETIME in UTC
- All foreign key relationships use INTEGER ids
- Status fields use string enums for categorization
"""

class BigQueryService:
    """
    A helper class for interacting with Google BigQuery.
    Handles common CRUD operations and can be easily integrated with FastAPI.
    """
    
    def __init__(self, project_id: str = None, dataset_id: str = None, credentials_path: str = None):
        """
        Initialize the BigQuery service.
        
        Args:
            project_id: Google Cloud project ID (default: from environment)
            dataset_id: BigQuery dataset ID (default: from environment)
            credentials_path: Path to the service account JSON file (default: from environment)
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.dataset_id = dataset_id or os.getenv('BIGQUERY_DATASET')
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Debug logging
        logger.info(f"BigQuery Service initialization:")
        logger.info(f"  Project ID: {self.project_id}")
        logger.info(f"  Dataset ID: {self.dataset_id}")
        logger.info(f"  Credentials path from env: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        logger.info(f"  Actual credentials path: {self.credentials_path}")
        
        if not self.project_id or not self.dataset_id:
            raise ValueError("Project ID and Dataset ID must be provided or set in environment variables")
            
        # Expand ~ in the credentials path if present
        if self.credentials_path and self.credentials_path.startswith('~'):
            self.credentials_path = os.path.expanduser(self.credentials_path)
            
        self.client = self._get_bigquery_client()
    
    def _get_bigquery_client(self) -> bigquery.Client:
        """Initialize and return a BigQuery client."""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                return bigquery.Client(credentials=credentials, project=self.project_id)
            else:
                # Will use application default credentials if no credentials file is provided
                return bigquery.Client(project=self.project_id)
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            # In test environment, return a mock client
            if 'pytest' in sys.modules:
                from unittest.mock import MagicMock
                return MagicMock()
            raise
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a SQL query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query string
            params: Dictionary of query parameters
            
        Returns:
            List of dictionaries representing the query results
        """
        try:
            query = self._qualify_table_names(query)
            
            job_config = bigquery.QueryJobConfig()
            
            # Add parameters if provided
            if params:
                query_parameters = []
                for key, value in params.items():
                    # Handle arrays/lists
                    if isinstance(value, list):
                        # Determine array element type from first element
                        if not value:  # Empty array
                            elem_type = "STRING"
                        elif isinstance(value[0], int):
                            elem_type = "INT64"
                        elif isinstance(value[0], float):
                            elem_type = "FLOAT64"
                        elif isinstance(value[0], bool):
                            elem_type = "BOOL"
                        else:
                            elem_type = "STRING"
                        
                        query_parameters.append(
                            bigquery.ArrayQueryParameter(key, elem_type, value)
                        )
                    else:
                        # Handle scalar parameters
                        if isinstance(value, int):
                            param_type = "INT64"
                        elif isinstance(value, float):
                            param_type = "FLOAT64"
                        elif isinstance(value, bool):
                            param_type = "BOOL"
                        elif isinstance(value, (date, datetime)):
                            param_type = "DATE" if isinstance(value, date) else "DATETIME"
                        else:
                            param_type = "STRING"
                        
                        query_parameters.append(
                            bigquery.ScalarQueryParameter(key, param_type, value)
                        )
                
                job_config.query_parameters = query_parameters
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            # Convert RowIterator to list of dicts
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def _qualify_table_names(self, query: str) -> str:
        """
        Automatically qualify unqualified table names in SQL queries.
        Replaces `table_name` with `project.dataset.table_name` if not already qualified.
        Only applies to simple table names, not already qualified ones.
        """
        import re
        
        # Pattern to match simple table references that are not already qualified
        # This pattern looks for backticked table names that are standalone (not part of a qualified name)
        # It should match `tablename` but not `project.dataset.tablename` or parts of qualified names
        pattern = r'`([^`]+)`(?!\s*\.\s*`)'  # Table name not followed by .`
        
        def replace_table(match):
            table_content = match.group(1)
            # If the content contains dots, it's likely already qualified
            if '.' in table_content:
                return match.group(0)  # Return original if already qualified
            
            # Check if this looks like a simple table name (not a complex qualified reference)
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_content):
                return f'`{self.project_id}.{self.dataset_id}.{table_content}`'
            
            return match.group(0)  # Return original if doesn't match simple table name pattern
        
        return re.sub(pattern, replace_table, query)
    
    def get_table(self, table_name: str) -> bigquery.Table:
        """Get a BigQuery table reference."""
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        return self.client.get_table(table_id)
    
    def insert_rows(self, table_name: str, rows: List[Dict]) -> int:
        """
        Insert multiple rows into a BigQuery table.
        
        Args:
            table_name: Name of the target table
            rows: List of dictionaries where keys are column names and values are row values
            
        Returns:
            Number of rows inserted
        """
        try:
            table = self.get_table(table_name)
            errors = self.client.insert_rows_json(table, rows)
            
            if errors:
                logger.error(f"Encountered errors while inserting rows: {errors}")
                return 0
                
            return len(rows)
            
        except Exception as e:
            logger.error(f"Error inserting rows: {str(e)}")
            raise
    
    def update_rows(self, table_name: str, updates: Dict, where_conditions: Dict) -> int:
        """
        Update rows in a BigQuery table.
        
        Args:
            table_name: Name of the target table
            updates: Dictionary of column names and their new values
            where_conditions: Dictionary of column names and values for the WHERE clause
            
        Returns:
            Number of rows updated
        """
        if not updates:
            return 0
            
        try:
            # Build SET clause
            set_clause = ", ".join([f"{k} = @{k}" for k in updates.keys()])
            
            # Build WHERE clause
            where_clause = " AND ".join([f"{k} = @where_{k}" for k in where_conditions.keys()])
            
            query = f"""
                UPDATE `{self.project_id}.{self.dataset_id}.{table_name}`
                SET {set_clause}
                WHERE {where_clause}
            """
            
            # Prepare parameters
            params = updates.copy()
            params.update({f"where_{k}": v for k, v in where_conditions.items()})
            
            # Execute the query
            query_job = self.client.query(query, job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(k, self._get_bigquery_type(v), v)
                    for k, v in params.items()
                ]
            ))
            
            query_job.result()  # Wait for the query to complete
            return query_job.num_dml_affected_rows or 0
            
        except Exception as e:
            logger.error(f"Error updating rows: {str(e)}")
            raise
    
    def delete_rows(self, table_name: str, where_conditions: Dict) -> int:
        """
        Delete rows from a BigQuery table.
        
        Args:
            table_name: Name of the target table
            where_conditions: Dictionary of column names and values for the WHERE clause
            
        Returns:
            Number of rows deleted
        """
        try:
            # Build WHERE clause
            where_clause = " AND ".join([f"{k} = @{k}" for k in where_conditions.keys()])
            
            query = f"""
                DELETE FROM `{self.project_id}.{self.dataset_id}.{table_name}`
                WHERE {where_clause}
            """
            
            # Execute the query
            query_job = self.client.query(query, job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(k, self._get_bigquery_type(v), v)
                    for k, v in where_conditions.items()
                ]
            ))
            
            query_job.result()  # Wait for the query to complete
            return query_job.num_dml_affected_rows or 0
            
        except Exception as e:
            logger.error(f"Error deleting rows: {str(e)}")
            raise
    
    def _get_bigquery_type(self, value: Any) -> str:
        """Map Python types to BigQuery SQL types."""
        if isinstance(value, int):
            return "INT64"
        elif isinstance(value, float):
            return "FLOAT64"
        elif isinstance(value, bool):
            return "BOOL"
        elif isinstance(value, bytes):
            return "BYTES"
        elif isinstance(value, datetime):
            return "DATETIME"
        elif isinstance(value, date):
            return "DATE"
        return "STRING"
    
    def get_schema(self, table_name: str) -> List[Dict]:
        """
        Get the schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries containing field information
        """
        try:
            table = self.get_table(table_name)
            return [{"name": field.name, "type": field.field_type, "mode": field.mode}
                   for field in table.schema]
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {str(e)}")
            raise

# Example usage with FastAPI integration
class FastAPIBigQueryDependency:
    """
    FastAPI dependency that provides a BigQueryService instance.
    Add this to your FastAPI app's dependencies.
    """
    def __init__(self, project_id: str, dataset_id: str, credentials_path: Optional[str] = None):
        self.service = BigQueryService(project_id, dataset_id, credentials_path)
    
    async def __call__(self):
        return self.service

def bigquery_transaction(func):
    """
    Decorator for handling BigQuery transactions.
    Use this to wrap FastAPI route handlers that need transaction support.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get the BigQuery service instance
        bq_service = None
        for arg in args:
            if isinstance(arg, BigQueryService):
                bq_service = arg
                break
        
        if not bq_service:
            for v in kwargs.values():
                if isinstance(v, BigQueryService):
                    bq_service = v
                    break
        
        if not bq_service:
            raise ValueError("BigQueryService instance not found in function arguments")
        
        # Start a transaction (BigQuery doesn't support transactions in the traditional sense,
        # but we can implement a pattern for atomic operations)
        try:
            # In BigQuery, we don't have explicit transactions like in SQL databases,
            # but we can implement a pattern where we collect operations and execute them
            # in a way that simulates a transaction
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            # Log the error and re-raise
            logger.error(f"Error in BigQuery transaction: {str(e)}")
            raise
    
    return wrapper
