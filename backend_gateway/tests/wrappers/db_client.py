"""
Database Client Wrapper for Testing

This wrapper provides a clean interface for testing database operations
without direct dependencies on PostgreSQL or connection management.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from contextlib import contextmanager
import random
import string


class MockDatabaseClient:
    """Mock implementation of database operations for testing"""
    
    def __init__(self):
        self.data_store = {
            'users': {},
            'pantries': {},
            'pantry_items': {},
            'products': {},
            'user_preferences': {},
            'user_dietary_preferences': {},
            'user_allergens': {},
            'user_cuisine_preferences': {},
            'recipes': {},
            'user_recipes': {},
            'shopping_lists': {},
            'shopping_list_items': {}
        }
        self.query_history = []
        self.transaction_active = False
        self._id_counters = {}
    
    def _get_next_id(self, table: str) -> int:
        """Get next auto-increment ID for a table"""
        if table not in self._id_counters:
            self._id_counters[table] = 1
        current_id = self._id_counters[table]
        self._id_counters[table] += 1
        return current_id
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Mock cursor context manager"""
        class MockCursor:
            def __init__(self, client):
                self.client = client
                self.description = None
                self.rowcount = 0
            
            def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
                self.client.query_history.append((query, params))
            
            def fetchall(self):
                return []
            
            def fetchone(self):
                return None
            
            def close(self):
                pass
        
        cursor = MockCursor(self)
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return mock results
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of mock result dictionaries
        """
        self.query_history.append((query, params))
        
        # Analyze query to determine what kind of results to return
        query_lower = query.lower()
        
        # Handle specific query patterns
        if "select * from pantry_items" in query_lower:
            return self._get_mock_pantry_items(params)
        elif "select * from user_pantry_full" in query_lower:
            return self._get_mock_user_pantry_full(params)
        elif "select * from users" in query_lower:
            return self._get_mock_users(params)
        elif "select * from recipes" in query_lower:
            return self._get_mock_recipes(params)
        elif "insert into" in query_lower:
            return [{"affected_rows": 1}]
        elif "update" in query_lower:
            return [{"affected_rows": 1}]
        elif "delete" in query_lower:
            return [{"affected_rows": 1}]
        
        # Default empty result
        return []
    
    def execute_batch_insert(
        self, 
        table: str, 
        data: List[Dict[str, Any]], 
        conflict_resolution: Optional[str] = None
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
        if table not in self.data_store:
            self.data_store[table] = {}
        
        inserted_count = 0
        for row in data:
            # Generate ID if needed
            if 'id' not in row:
                row['id'] = self._get_next_id(table)
            
            # Handle conflict resolution
            if conflict_resolution and f"{table}_id" in row:
                existing_id = row[f"{table}_id"]
                if existing_id in self.data_store[table]:
                    if "DO NOTHING" in conflict_resolution:
                        continue
                    elif "DO UPDATE" in conflict_resolution:
                        self.data_store[table][existing_id].update(row)
                        inserted_count += 1
                        continue
            
            # Insert new row
            row_id = row.get('id', self._get_next_id(table))
            self.data_store[table][row_id] = row.copy()
            inserted_count += 1
        
        return inserted_count
    
    def _get_mock_pantry_items(self, params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock pantry items"""
        user_id = params.get('user_id', 111) if params else 111
        
        return [
            {
                'pantry_item_id': 1,
                'user_id': user_id,
                'product_id': 101,
                'product_name': 'Chicken Breast',
                'quantity': 2.0,
                'unit': 'lb',
                'expiration_date': (datetime.now() + timedelta(days=3)).date(),
                'category': 'meat',
                'created_at': datetime.now()
            },
            {
                'pantry_item_id': 2,
                'user_id': user_id,
                'product_id': 102,
                'product_name': 'Rice',
                'quantity': 1.0,
                'unit': 'kg',
                'expiration_date': (datetime.now() + timedelta(days=90)).date(),
                'category': 'grain',
                'created_at': datetime.now()
            },
            {
                'pantry_item_id': 3,
                'user_id': user_id,
                'product_id': 103,
                'product_name': 'Broccoli',
                'quantity': 0.5,
                'unit': 'lb',
                'expiration_date': (datetime.now() + timedelta(days=5)).date(),
                'category': 'vegetable',
                'created_at': datetime.now()
            }
        ]
    
    def _get_mock_user_pantry_full(self, params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock full pantry view data"""
        items = self._get_mock_pantry_items(params)
        # Add additional fields that would come from joined tables
        for item in items:
            item['pantry_id'] = 1
            item['pantry_name'] = 'Main Pantry'
            item['product_brand'] = 'Generic'
            item['barcode'] = f"123456789{item['product_id']}"
        return items
    
    def _get_mock_users(self, params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock users"""
        return [
            {
                'user_id': 111,
                'email': 'test@example.com',
                'username': 'testuser',
                'full_name': 'Test User',
                'created_at': datetime.now()
            }
        ]
    
    def _get_mock_recipes(self, params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock recipes"""
        return [
            {
                'recipe_id': 1,
                'title': 'Chicken Stir Fry',
                'ingredients': ['chicken breast', 'broccoli', 'rice', 'soy sauce'],
                'instructions': ['Cook rice', 'Cut chicken', 'Stir fry chicken', 'Add broccoli'],
                'cuisine_type': 'asian',
                'prep_time': 15,
                'cook_time': 20,
                'servings': 4
            },
            {
                'recipe_id': 2,
                'title': 'Grilled Chicken and Rice',
                'ingredients': ['chicken breast', 'rice', 'olive oil', 'herbs'],
                'instructions': ['Marinate chicken', 'Grill chicken', 'Cook rice', 'Serve'],
                'cuisine_type': 'american',
                'prep_time': 10,
                'cook_time': 25,
                'servings': 2
            }
        ]
    
    def begin_transaction(self):
        """Begin a transaction"""
        self.transaction_active = True
    
    def commit_transaction(self):
        """Commit a transaction"""
        self.transaction_active = False
    
    def rollback_transaction(self):
        """Rollback a transaction"""
        self.transaction_active = False
    
    def test_connection(self) -> bool:
        """Test database connection"""
        return True


class DatabaseClientWrapper:
    """Wrapper for the actual database service"""
    
    def __init__(self, db_service=None):
        """
        Initialize wrapper with optional real service
        
        Args:
            db_service: Real database service instance or None for mock
        """
        self._service = db_service
        self._mock = MockDatabaseClient()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get database cursor"""
        if self._service and hasattr(self._service, 'get_cursor'):
            with self._service.get_cursor(dict_cursor) as cursor:
                yield cursor
        else:
            with self._mock.get_cursor(dict_cursor) as cursor:
                yield cursor
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query"""
        if self._service and hasattr(self._service, 'execute_query'):
            return self._service.execute_query(query, params)
        return self._mock.execute_query(query, params)
    
    def execute_batch_insert(
        self, 
        table: str, 
        data: List[Dict[str, Any]], 
        conflict_resolution: Optional[str] = None
    ) -> int:
        """Batch insert data"""
        if self._service and hasattr(self._service, 'execute_batch_insert'):
            return self._service.execute_batch_insert(table, data, conflict_resolution)
        return self._mock.execute_batch_insert(table, data, conflict_resolution)
    
    def get_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get pantry items for a user"""
        query = """
            SELECT * FROM pantry_items 
            WHERE user_id = %(user_id)s
            ORDER BY expiration_date ASC
        """
        return self.execute_query(query, {'user_id': user_id})
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences"""
        # Simplified version - in real implementation this would join multiple tables
        return {
            'dietary_preferences': ['vegetarian'],
            'allergens': ['nuts'],
            'cuisine_preferences': ['italian', 'asian']
        }
    
    def add_pantry_item(self, item_data: Dict[str, Any]) -> int:
        """Add a single pantry item"""
        return self.execute_batch_insert('pantry_items', [item_data])
    
    def update_pantry_item(self, item_id: int, updates: Dict[str, Any]) -> int:
        """Update a pantry item"""
        set_clause = ", ".join([f"{k} = %({k})s" for k in updates.keys()])
        query = f"""
            UPDATE pantry_items 
            SET {set_clause}
            WHERE pantry_item_id = %(item_id)s
        """
        params = updates.copy()
        params['item_id'] = item_id
        
        result = self.execute_query(query, params)
        return result[0]['affected_rows'] if result else 0
    
    def delete_pantry_item(self, item_id: int) -> int:
        """Delete a pantry item"""
        query = "DELETE FROM pantry_items WHERE pantry_item_id = %(item_id)s"
        result = self.execute_query(query, {'item_id': item_id})
        return result[0]['affected_rows'] if result else 0
    
    def search_products(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products"""
        query = """
            SELECT * FROM products 
            WHERE LOWER(product_name) LIKE %(search_term)s
            LIMIT %(limit)s
        """
        return self.execute_query(query, {
            'search_term': f"%{search_term.lower()}%",
            'limit': limit
        })
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if self._service and hasattr(self._service, 'test_connection'):
            return self._service.test_connection()
        return self._mock.test_connection()


def get_db_client(service=None) -> DatabaseClientWrapper:
    """Factory function to get database client"""
    return DatabaseClientWrapper(service)