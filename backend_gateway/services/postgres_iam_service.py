"""
PostgreSQL Service with IAM Authentication for PrepSense
Uses Google Cloud IAM tokens instead of passwords
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool
import threading
from google.auth import default
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

class PostgresIAMService:
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize PostgreSQL service with IAM authentication
        
        Args:
            connection_params: Dict with host, port, database, user (email)
        """
        self.connection_params = connection_params
        self.pool = None
        self._local = threading.local()
        self._credentials = None
        self._initialize_credentials()
        self._initialize_pool()
        
    def _initialize_credentials(self):
        """Initialize Google Cloud credentials"""
        try:
            # Get default credentials with Cloud SQL scopes
            self._credentials, self._project = default(
                scopes=["https://www.googleapis.com/auth/cloud-platform",
                        "https://www.googleapis.com/auth/sqlservice.admin"]
            )
            logger.info("Google Cloud credentials initialized")
        except Exception as e:
            logger.error(f"Failed to get Google Cloud credentials: {e}")
            raise
            
    def _get_access_token(self):
        """Get fresh access token for database connection"""
        try:
            # Refresh token if needed
            self._credentials.refresh(Request())
            return self._credentials.token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise
        
    def _initialize_pool(self):
        """Initialize connection pool with IAM authentication"""
        try:
            # Get initial token
            access_token = self._get_access_token()
            
            # Create connection parameters with token as password
            conn_params = self.connection_params.copy()
            conn_params['password'] = access_token
            conn_params['sslmode'] = 'require'  # SSL required for IAM auth
            
            self.pool = SimpleConnectionPool(
                1, 20,  # min and max connections
                host=conn_params['host'],
                port=conn_params.get('port', 5432),
                database=conn_params['database'],
                user=conn_params['user'],  # Should be email@domain
                password=conn_params['password'],
                sslmode=conn_params['sslmode']
            )
            logger.info(f"PostgreSQL IAM connection pool initialized for user {conn_params['user']}")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
            
    def _get_connection(self):
        """Get a connection with fresh token"""
        # Get fresh token for each connection
        access_token = self._get_access_token()
        
        # Create new connection with fresh token
        conn = psycopg2.connect(
            host=self.connection_params['host'],
            port=self.connection_params.get('port', 5432),
            database=self.connection_params['database'],
            user=self.connection_params['user'],
            password=access_token,
            sslmode='require'
        )
        return conn
            
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a database cursor with IAM authentication"""
        conn = None
        cursor = None
        try:
            # Use fresh connection with current token
            conn = self._get_connection()
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results
        
        Args:
            query: SQL query with %(param_name)s placeholders
            params: Dictionary of parameters
            
        Returns:
            List of dictionaries representing rows
        """
        with self.get_cursor() as cursor:
            # Convert BigQuery-style parameters to psycopg2 style
            if params:
                # Replace @param with %(param)s in query
                for param_name in params:
                    query = query.replace(f"@{param_name}", f"%({param_name})s")
                    
            cursor.execute(query, params or {})
            
            # Check if this is a SELECT query
            if cursor.description:
                return cursor.fetchall()
            else:
                # For INSERT/UPDATE/DELETE, return affected rows count
                return [{"affected_rows": cursor.rowcount}]
                
    def execute_batch_insert(self, table: str, data: List[Dict[str, Any]], 
                           conflict_resolution: Optional[str] = None) -> int:
        """
        Batch insert data into a table
        
        Args:
            table: Table name
            data: List of dictionaries to insert
            conflict_resolution: Optional ON CONFLICT clause
            
        Returns:
            Number of rows inserted
        """
        if not data:
            return 0
            
        # Get columns from first row
        columns = list(data[0].keys())
        
        # Build query
        placeholders = ", ".join([f"%({col})s" for col in columns])
        column_names = ", ".join(columns)
        
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        
        if conflict_resolution:
            query += f" {conflict_resolution}"
            
        with self.get_cursor() as cursor:
            execute_batch(cursor, query, data)
            return cursor.rowcount
            
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL IAM connection pool closed")
            
    # Include all the pantry-specific methods from postgres_service.py
    # (Same methods, just using IAM authentication internally)
    
    def get_user_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all pantry items for a user"""
        query = """
        SELECT 
            pi.pantry_item_id as id,
            pi.product_name as item_name,
            pi.brand_name as brand,
            pi.quantity as quantity_amount,
            pi.unit_of_measurement as quantity_unit,
            pi.expiration_date as expected_expiration,
            pi.category,
            pi.status,
            pi.created_at as "addedDate",
            pi.metadata
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = %(user_id)s
        ORDER BY pi.created_at DESC
        """
        
        results = self.execute_query(query, {"user_id": user_id})
        
        # Convert dates to ISO format strings
        for item in results:
            if item.get('expected_expiration'):
                item['expected_expiration'] = item['expected_expiration'].isoformat()
            if item.get('addedDate'):
                item['addedDate'] = item['addedDate'].isoformat()
                
        return results
        
    # ... (include other methods from postgres_service.py)