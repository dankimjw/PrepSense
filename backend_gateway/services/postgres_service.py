"""
PostgreSQL Service for PrepSense
Handles all database operations with PostgreSQL instead of BigQuery
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

logger = logging.getLogger(__name__)

class PostgresService:
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize PostgreSQL service with connection pooling
        
        Args:
            connection_params: Dict with host, port, database, user, password
        """
        self.connection_params = connection_params
        self.pool = None
        self._local = threading.local()
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                1, 20,  # min and max connections
                host=self.connection_params['host'],
                port=self.connection_params.get('port', 5432),
                database=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password']
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
            
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a database cursor from the pool"""
        conn = None
        try:
            conn = self.pool.getconn()
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
                self.pool.putconn(conn)
                
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
            # Convert BigQuery syntax to PostgreSQL
            # Remove backticks and project/dataset prefixes
            query = query.replace('`', '"')
            
            # Replace BigQuery table references with PostgreSQL table names
            bigquery_to_postgres = {
                '"adsp-34002-on02-prep-sense.Inventory.user_pantry_full"': 'user_pantry_full',
                '"adsp-34002-on02-prep-sense.Inventory.pantry_items"': 'pantry_items',
                '"adsp-34002-on02-prep-sense.Inventory.pantry"': 'pantries',
                '"adsp-34002-on02-prep-sense.Inventory.products"': 'products',
                '"adsp-34002-on02-prep-sense.Inventory.users"': 'users',
                '"adsp-34002-on02-prep-sense.Inventory.user_preferences"': 'user_preferences',
                '"adsp-34002-on02-prep-sense.Inventory.dietary_preferences"': 'user_dietary_preferences',
                '"adsp-34002-on02-prep-sense.Inventory.allergens"': 'user_allergens',
                '"adsp-34002-on02-prep-sense.Inventory.cuisine_preferences"': 'user_cuisine_preferences',
            }
            
            for bq_table, pg_table in bigquery_to_postgres.items():
                query = query.replace(bq_table, pg_table)
            
            # Convert BigQuery types to PostgreSQL
            query = query.replace('FLOAT64', 'NUMERIC')
            query = query.replace('INT64', 'INTEGER')
            
            # Convert BigQuery-style parameters to psycopg2 style
            if params:
                # Sort parameters by length (descending) to avoid partial replacements
                # e.g., replace @unit_price before @unit
                sorted_params = sorted(params.keys(), key=len, reverse=True)
                for param_name in sorted_params:
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
            logger.info("PostgreSQL connection pool closed")
            
    # Pantry-specific methods that match BigQueryService interface
    
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
        
    def add_pantry_item(self, user_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new pantry item"""
        # First get the user's pantry
        pantry_query = """
        SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s LIMIT 1
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(pantry_query, {"user_id": user_id})
            pantry = cursor.fetchone()
            
            if not pantry:
                # Create pantry if it doesn't exist
                cursor.execute(
                    "INSERT INTO pantries (user_id, pantry_name) VALUES (%(user_id)s, %(name)s) RETURNING pantry_id",
                    {"user_id": user_id, "name": "My Pantry"}
                )
                pantry = cursor.fetchone()
                
            pantry_id = pantry['pantry_id']
            
            # Insert pantry item
            insert_query = """
            INSERT INTO pantry_items (
                pantry_id, product_name, brand_name, category,
                quantity, unit_of_measurement, expiration_date,
                unit_price, total_price, source, status
            ) VALUES (
                %(pantry_id)s, %(product_name)s, %(brand_name)s, %(category)s,
                %(quantity)s, %(unit_of_measurement)s, %(expiration_date)s,
                %(unit_price)s, %(total_price)s, %(source)s, %(status)s
            ) RETURNING pantry_item_id, created_at
            """
            
            params = {
                "pantry_id": pantry_id,
                "product_name": item_data.get("product_name", "Unknown"),
                "brand_name": item_data.get("brand_name"),
                "category": item_data.get("category", "Uncategorized"),
                "quantity": float(item_data.get("quantity", 0)),
                "unit_of_measurement": item_data.get("unit_of_measurement"),
                "expiration_date": item_data.get("expiration_date"),
                "unit_price": float(item_data["unit_price"]) if item_data.get("unit_price") else None,
                "total_price": float(item_data["total_price"]) if item_data.get("total_price") else None,
                "source": item_data.get("source", "manual"),
                "status": item_data.get("status", "available")
            }
            
            cursor.execute(insert_query, params)
            result = cursor.fetchone()
            
            return {
                "id": str(result["pantry_item_id"]),
                "pantry_item_id": result["pantry_item_id"],
                "product_name": params["product_name"],
                "item_name": params["product_name"],
                "quantity": params["quantity"],
                "quantity_amount": params["quantity"],
                "unit_of_measurement": params["unit_of_measurement"],
                "quantity_unit": params["unit_of_measurement"],
                "expiration_date": params["expiration_date"].isoformat() if params["expiration_date"] else None,
                "expected_expiration": params["expiration_date"].isoformat() if params["expiration_date"] else None,
                "category": params["category"],
                "created_at": result["created_at"].isoformat(),
                "message": "Item added successfully"
            }
            
    def update_pantry_item(self, pantry_item_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pantry item"""
        # Build dynamic update query
        set_clauses = []
        params = {"pantry_item_id": pantry_item_id}
        
        field_mapping = {
            "product_name": "product_name",
            "quantity": "quantity",
            "unit_of_measurement": "unit_of_measurement",
            "expiration_date": "expiration_date",
            "category": "category",
            "brand_name": "brand_name",
            "unit_price": "unit_price",
            "total_price": "total_price",
            "status": "status"
        }
        
        for api_field, db_field in field_mapping.items():
            if api_field in updates:
                set_clauses.append(f"{db_field} = %({db_field})s")
                value = updates[api_field]
                
                # Handle numeric fields
                if db_field in ["quantity", "unit_price", "total_price"]:
                    value = float(value) if value is not None else None
                    
                params[db_field] = value
                
        if not set_clauses:
            return {"error": "No fields to update"}
            
        query = f"""
        UPDATE pantry_items
        SET {", ".join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
        WHERE pantry_item_id = %(pantry_item_id)s
        RETURNING *
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if not result:
                return None
                
            return {
                "id": str(result["pantry_item_id"]),
                "pantry_item_id": result["pantry_item_id"],
                "product_name": result["product_name"],
                "item_name": result["product_name"],
                "quantity": float(result["quantity"]),
                "quantity_amount": float(result["quantity"]),
                "unit_of_measurement": result["unit_of_measurement"],
                "quantity_unit": result["unit_of_measurement"],
                "expiration_date": result["expiration_date"].isoformat() if result["expiration_date"] else None,
                "expected_expiration": result["expiration_date"].isoformat() if result["expiration_date"] else None,
                "category": result["category"],
                "message": "Item updated successfully"
            }
            
    def delete_pantry_item(self, pantry_item_id: int) -> bool:
        """Delete a pantry item"""
        query = """
        DELETE FROM pantry_items
        WHERE pantry_item_id = %(pantry_item_id)s
        """
        
        result = self.execute_query(query, {"pantry_item_id": pantry_item_id})
        return result[0]["affected_rows"] > 0
        
    def batch_add_pantry_items(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple pantry items in a batch"""
        # Get user's pantry
        pantry_query = "SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s LIMIT 1"
        
        with self.get_cursor() as cursor:
            cursor.execute(pantry_query, {"user_id": user_id})
            pantry = cursor.fetchone()
            
            if not pantry:
                cursor.execute(
                    "INSERT INTO pantries (user_id, pantry_name) VALUES (%(user_id)s, %(name)s) RETURNING pantry_id",
                    {"user_id": user_id, "name": "My Pantry"}
                )
                pantry = cursor.fetchone()
                
            pantry_id = pantry['pantry_id']
            
            # Prepare batch data
            insert_data = []
            for item in items:
                insert_data.append({
                    "pantry_id": pantry_id,
                    "product_name": item.get("item_name", "Unknown"),
                    "brand_name": item.get("brand", "Generic"),
                    "category": item.get("category", "Uncategorized"),
                    "quantity": float(item.get("quantity_amount", 0)),
                    "unit_of_measurement": item.get("quantity_unit"),
                    "expiration_date": item.get("expected_expiration"),
                    "source": item.get("source", "manual"),
                    "status": "available"
                })
                
            # Batch insert
            if insert_data:
                columns = list(insert_data[0].keys())
                placeholders = ", ".join([f"%({col})s" for col in columns])
                column_names = ", ".join(columns)
                
                query = f"""
                INSERT INTO pantry_items ({column_names}) 
                VALUES ({placeholders})
                RETURNING pantry_item_id, product_name
                """
                
                saved_items = []
                for item_data in insert_data:
                    cursor.execute(query, item_data)
                    result = cursor.fetchone()
                    saved_items.append({
                        "pantry_item_id": result["pantry_item_id"],
                        "item_name": result["product_name"]
                    })
                    
                return {
                    "saved_count": len(saved_items),
                    "saved_items": saved_items
                }
                
        return {"saved_count": 0, "saved_items": []}
        
    # User preference methods
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences including dietary, allergens, and cuisine"""
        with self.get_cursor() as cursor:
            # Get basic preferences
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %(user_id)s",
                {"user_id": user_id}
            )
            prefs = cursor.fetchone() or {}
            
            # Get dietary preferences
            cursor.execute(
                "SELECT preference FROM user_dietary_preferences WHERE user_id = %(user_id)s",
                {"user_id": user_id}
            )
            dietary = [row["preference"] for row in cursor.fetchall()]
            
            # Get allergens
            cursor.execute(
                "SELECT allergen FROM user_allergens WHERE user_id = %(user_id)s",
                {"user_id": user_id}
            )
            allergens = [row["allergen"] for row in cursor.fetchall()]
            
            # Get cuisine preferences
            cursor.execute(
                "SELECT cuisine FROM user_cuisine_preferences WHERE user_id = %(user_id)s",
                {"user_id": user_id}
            )
            cuisines = [row["cuisine"] for row in cursor.fetchall()]
            
            return {
                "user_id": user_id,
                "household_size": prefs.get("household_size", 1),
                "dietary_preference": dietary,
                "allergens": allergens,
                "cuisine_preference": cuisines
            }
            
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        with self.get_cursor() as cursor:
            # Update or insert main preferences
            if "household_size" in preferences:
                cursor.execute("""
                    INSERT INTO user_preferences (user_id, household_size)
                    VALUES (%(user_id)s, %(household_size)s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET household_size = EXCLUDED.household_size,
                        updated_at = CURRENT_TIMESTAMP
                """, {
                    "user_id": user_id,
                    "household_size": preferences["household_size"]
                })
                
            # Update dietary preferences
            if "dietary_preference" in preferences:
                cursor.execute(
                    "DELETE FROM user_dietary_preferences WHERE user_id = %(user_id)s",
                    {"user_id": user_id}
                )
                
                for pref in preferences["dietary_preference"]:
                    cursor.execute(
                        "INSERT INTO user_dietary_preferences (user_id, preference) VALUES (%(user_id)s, %(pref)s)",
                        {"user_id": user_id, "pref": pref}
                    )
                    
            # Update allergens
            if "allergens" in preferences:
                cursor.execute(
                    "DELETE FROM user_allergens WHERE user_id = %(user_id)s",
                    {"user_id": user_id}
                )
                
                for allergen in preferences["allergens"]:
                    cursor.execute(
                        "INSERT INTO user_allergens (user_id, allergen) VALUES (%(user_id)s, %(allergen)s)",
                        {"user_id": user_id, "allergen": allergen}
                    )
                    
            # Update cuisine preferences
            if "cuisine_preference" in preferences:
                cursor.execute(
                    "DELETE FROM user_cuisine_preferences WHERE user_id = %(user_id)s",
                    {"user_id": user_id}
                )
                
                for cuisine in preferences["cuisine_preference"]:
                    cursor.execute(
                        "INSERT INTO user_cuisine_preferences (user_id, cuisine) VALUES (%(user_id)s, %(cuisine)s)",
                        {"user_id": user_id, "cuisine": cuisine}
                    )
                    
        return self.get_user_preferences(user_id)