"""
PostgreSQL Service with IAM Authentication for PrepSense
Uses Google Cloud IAM tokens instead of passwords
"""

import logging
import threading
from contextlib import contextmanager
from typing import Any, Optional

import psycopg2
from google.auth import default
from google.auth.transport.requests import Request
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)


class PostgresIAMService:
    def __init__(self, connection_params: dict[str, Any]):
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
                scopes=[
                    "https://www.googleapis.com/auth/cloud-platform",
                    "https://www.googleapis.com/auth/sqlservice.admin",
                ]
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
            conn_params["password"] = access_token
            conn_params["sslmode"] = "require"  # SSL required for IAM auth

            self.pool = SimpleConnectionPool(
                1,
                20,  # min and max connections
                host=conn_params["host"],
                port=conn_params.get("port", 5432),
                database=conn_params["database"],
                user=conn_params["user"],  # Should be email@domain
                password=conn_params["password"],
                sslmode=conn_params["sslmode"],
            )
            logger.info(
                f"PostgreSQL IAM connection pool initialized for user {conn_params['user']}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _get_connection(self):
        """Get a connection with fresh token"""
        # Get fresh token for each connection
        access_token = self._get_access_token()

        # Create new connection with fresh token
        conn = psycopg2.connect(
            host=self.connection_params["host"],
            port=self.connection_params.get("port", 5432),
            database=self.connection_params["database"],
            user=self.connection_params["user"],
            password=access_token,
            sslmode="require",
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

    def execute_query(
        self, query: str, params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
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

    def execute_batch_insert(
        self, table: str, data: list[dict[str, Any]], conflict_resolution: Optional[str] = None
    ) -> int:
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

    def get_user_pantry_items(self, user_id: int) -> list[dict[str, Any]]:
        """Get all pantry items for a user with full BigQuery-compatible schema"""
        # Query that matches the BigQuery user_pantry_full view structure
        # Adjusted for PostgreSQL schema differences
        query = """
        SELECT
            u.user_id,
            u.username as user_name,
            p.pantry_id,
            pi.pantry_item_id,
            pi.quantity,
            pi.unit_of_measurement,
            pi.expiration_date,
            pi.unit_price,
            pi.total_price,
            pi.created_at as pantry_item_created_at,
            pi.used_quantity,
            pi.status,
            NULL::integer as product_id,
            pi.product_name,
            pi.brand_name,
            pi.category as food_category,
            CAST(pi.metadata->>'upc_code' AS VARCHAR) as upc_code,
            pi.created_at as product_created_at
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        JOIN users u ON p.user_id = u.user_id
        WHERE p.user_id = %(user_id)s
        ORDER BY pi.created_at DESC
        """

        results = self.execute_query(query, {"user_id": user_id})

        # Convert dates to ISO format strings and ensure all fields are present
        for item in results:
            # Handle date conversions
            if item.get("expiration_date"):
                item["expiration_date"] = item["expiration_date"].isoformat()
            if item.get("pantry_item_created_at"):
                item["pantry_item_created_at"] = item["pantry_item_created_at"].isoformat()
            if item.get("product_created_at"):
                item["product_created_at"] = item["product_created_at"].isoformat()

            # Ensure all expected fields are present with defaults if null
            item["used_quantity"] = item.get("used_quantity", 0)
            item["unit_price"] = item.get("unit_price")
            item["total_price"] = item.get("total_price")
            item["upc_code"] = item.get("upc_code")
            item["status"] = item.get("status", "available")

        return results

    async def update_pantry_item(self, pantry_item_id: int, item_data: Any) -> dict[str, Any]:
        """Updates an existing pantry item"""

        try:
            # Build dynamic update query
            set_clauses = []
            params = {"pantry_item_id": pantry_item_id}

            # Map fields from PantryItemCreate to database columns
            if hasattr(item_data, "product_name") and item_data.product_name is not None:
                set_clauses.append("product_name = %(product_name)s")
                params["product_name"] = item_data.product_name

            if hasattr(item_data, "quantity") and item_data.quantity is not None:
                set_clauses.append("quantity = %(quantity)s")
                params["quantity"] = float(item_data.quantity)

            if (
                hasattr(item_data, "unit_of_measurement")
                and item_data.unit_of_measurement is not None
            ):
                set_clauses.append("unit_of_measurement = %(unit_of_measurement)s")
                params["unit_of_measurement"] = item_data.unit_of_measurement

            if hasattr(item_data, "expiration_date") and item_data.expiration_date is not None:
                set_clauses.append("expiration_date = %(expiration_date)s")
                params["expiration_date"] = item_data.expiration_date

            if hasattr(item_data, "category") and item_data.category is not None:
                set_clauses.append("category = %(category)s")
                params["category"] = item_data.category

            if hasattr(item_data, "unit_price") and item_data.unit_price is not None:
                set_clauses.append("unit_price = %(unit_price)s")
                params["unit_price"] = float(item_data.unit_price)

                # Calculate total price
                if hasattr(item_data, "quantity") and item_data.quantity is not None:
                    total_price = float(item_data.unit_price) * float(item_data.quantity)
                    set_clauses.append("total_price = %(total_price)s")
                    params["total_price"] = total_price

            if not set_clauses:
                return {"error": "No fields to update"}

            # Always update the updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")

            query = f"""
            UPDATE pantry_items
            SET {", ".join(set_clauses)}
            WHERE pantry_item_id = %(pantry_item_id)s
            RETURNING *
            """

            results = self.execute_query(query, params)

            if not results:
                return None

            result = results[0]

            # Return formatted response matching frontend expectations
            return {
                "id": str(result["pantry_item_id"]),
                "pantry_item_id": result["pantry_item_id"],
                "product_id": result.get("product_id"),
                "product_name": result["product_name"],
                "item_name": result["product_name"],
                "quantity": float(result["quantity"]),
                "quantity_amount": float(result["quantity"]),
                "unit_of_measurement": result["unit_of_measurement"],
                "quantity_unit": result["unit_of_measurement"],
                "expiration_date": (
                    result["expiration_date"].isoformat() if result["expiration_date"] else None
                ),
                "expected_expiration": (
                    result["expiration_date"].isoformat() if result["expiration_date"] else None
                ),
                "category": result.get("category", "Uncategorized"),
                "message": "Item updated successfully",
            }

        except Exception as e:
            logger.error(f"Error updating pantry item {pantry_item_id}: {str(e)}")
            raise

    async def delete_single_pantry_item(self, pantry_item_id: int) -> bool:
        """Delete a single pantry item"""
        query = """
        DELETE FROM pantry_items
        WHERE pantry_item_id = %(pantry_item_id)s
        """

        result = self.execute_query(query, {"pantry_item_id": pantry_item_id})
        return result[0]["affected_rows"] > 0 if result else False

    async def add_pantry_item(self, item_data: Any, user_id: int) -> dict[str, Any]:
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
                    {"user_id": user_id, "name": "My Pantry"},
                )
                pantry = cursor.fetchone()

            pantry_id = pantry["pantry_id"]

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

            # Calculate total price if unit price is provided
            total_price = None
            if hasattr(item_data, "unit_price") and item_data.unit_price:
                total_price = float(item_data.unit_price) * float(item_data.quantity)

            params = {
                "pantry_id": pantry_id,
                "product_name": (
                    item_data.product_name if hasattr(item_data, "product_name") else "Unknown"
                ),
                "brand_name": getattr(item_data, "brand_name", None),
                "category": getattr(item_data, "category", "Uncategorized"),
                "quantity": float(item_data.quantity) if hasattr(item_data, "quantity") else 0.0,
                "unit_of_measurement": (
                    item_data.unit_of_measurement
                    if hasattr(item_data, "unit_of_measurement")
                    else None
                ),
                "expiration_date": (
                    item_data.expiration_date if hasattr(item_data, "expiration_date") else None
                ),
                "unit_price": (
                    float(item_data.unit_price)
                    if hasattr(item_data, "unit_price") and item_data.unit_price
                    else None
                ),
                "total_price": total_price,
                "source": getattr(item_data, "source", "manual"),
                "status": getattr(item_data, "status", "available"),
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
                "expiration_date": (
                    params["expiration_date"].isoformat() if params["expiration_date"] else None
                ),
                "expected_expiration": (
                    params["expiration_date"].isoformat() if params["expiration_date"] else None
                ),
                "category": params["category"],
                "created_at": result["created_at"].isoformat(),
                "message": "Item added successfully",
            }
