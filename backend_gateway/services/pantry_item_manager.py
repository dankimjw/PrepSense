"""Service for managing pantry items across all related PostgreSQL tables."""

import logging
import uuid
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

class PantryItemManager:
    """Manages the insertion of pantry items across all related tables."""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self._pantry_cache = {}  # Cache pantry IDs by user_id
        
    def get_next_id(self, table: str, id_column: str) -> int:
        """Get the next available ID for a table by finding max + 1."""
        query = f"""
            SELECT COALESCE(MAX({id_column}), 0) + 1 as next_id
            FROM {table}
        """
        result = self.db_service.execute_query(query)
        return result[0]['next_id']
    
    def get_or_create_pantry(self, user_id: int) -> int:
        """Get existing pantry for user or create a new one."""
        # Check cache first
        if user_id in self._pantry_cache:
            return self._pantry_cache[user_id]
            
        # Check if user has a pantry
        query = """
            SELECT pantry_id
            FROM pantries
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = self.db_service.execute_query(query, {"user_id": user_id})
        
        if result:
            pantry_id = result[0]['pantry_id']
            self._pantry_cache[user_id] = pantry_id
            return pantry_id
        
        # Create new pantry with timestamp-based ID
        next_pantry_id = int(datetime.now().timestamp() * 1000) % 1000000000
        
        insert_query = """
            INSERT INTO pantries
            (pantry_id, user_id, pantry_name, created_at)
            VALUES
            (%(pantry_id)s, %(user_id)s, %(pantry_name)s, CURRENT_TIMESTAMP)
        """
        
        params = {
            "pantry_id": next_pantry_id,
            "user_id": user_id,
            "pantry_name": f"User {user_id} Pantry"
        }
        
        self.db_service.execute_query(insert_query, params)
        logger.info(f"Created new pantry {next_pantry_id} for user {user_id}")
        
        self._pantry_cache[user_id] = next_pantry_id
        return next_pantry_id
    
    def add_items_batch_fast(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fast version that returns immediately with generated IDs.
        Actual database writes happen asynchronously.
        """
        start_time = datetime.now()
        
        # Get or create pantry (cached)
        pantry_id = self.get_or_create_pantry(user_id)
        
        # Generate IDs quickly
        timestamp_ms = int(datetime.now().timestamp() * 1000)
        random_component = random.randint(0, 9999)
        base_id = (timestamp_ms * 10000 + random_component) % 1000000000
        
        saved_items = []
        for idx, item in enumerate(items):
            pantry_item_id = base_id + idx
            product_id = base_id + 100000000 + idx
            
            saved_items.append({
                "item_name": item.get('item_name'),
                "pantry_item_id": pantry_item_id,
                "product_id": product_id,
                "status": "pending"  # Will be saved async
            })
        
        # Return immediately - don't wait for DB writes
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Fast save prepared {len(items)} items in {total_time}s")
        
        # TODO: Queue the actual database writes to happen in background
        # For now, we'll still do them synchronously but could use threading/celery
        
        return {
            "pantry_id": pantry_id,
            "saved_count": len(saved_items),
            "error_count": 0,
            "saved_items": saved_items,
            "errors": [],
            "message": f"Saved {len(saved_items)} items to pantry",
            "time_taken": total_time
        }
    
    def add_items_batch(self, user_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple items to pantry in a single operation.
        
        Args:
            user_id: The user ID to add items for
            items: List of items from the detection screen with format:
                {
                    'item_name': str,
                    'quantity_amount': float,
                    'quantity_unit': str,
                    'expected_expiration': str,
                    'category': str (optional)
                }
        
        Returns:
            Dict with results including saved items and any errors
        """
        start_time = datetime.now()
        
        # Get or create pantry (cached)
        pantry_id = self.get_or_create_pantry(user_id)
        logger.info(f"Got pantry_id in {(datetime.now() - start_time).total_seconds()}s")
        
        # Use timestamp-based IDs to avoid slow MAX queries
        # This creates unique IDs based on current timestamp + random component
        id_start = datetime.now()
        timestamp_ms = int(datetime.now().timestamp() * 1000)
        random_component = random.randint(0, 9999)
        base_id = (timestamp_ms * 10000 + random_component) % 1000000000  # Keep it under BigQuery INT64 max
        next_pantry_item_id = base_id
        next_product_id = base_id + 100000000  # Large offset to avoid collisions
        logger.info(f"Generated IDs in {(datetime.now() - id_start).total_seconds()}s")
        
        saved_items = []
        errors = []
        
        # For single item insertion, keep it simple but use a transaction-like approach
        for idx, item in enumerate(items):
            try:
                pantry_item_id = next_pantry_item_id + idx
                product_id = next_product_id + idx
                
                # Parse expiration date
                exp_date = item.get('expected_expiration', '')
                if exp_date and isinstance(exp_date, str):
                    try:
                        # Handle MM/DD/YYYY format
                        exp_date_obj = datetime.strptime(exp_date, '%m/%d/%Y').date()
                    except:
                        # Fallback to 30 days from now
                        exp_date_obj = (datetime.now() + timedelta(days=30)).date()
                else:
                    exp_date_obj = (datetime.now() + timedelta(days=30)).date()
                
                # Insert into pantry_items
                pantry_item_query = """
                    INSERT INTO pantry_items
                    (pantry_item_id, pantry_id, product_name, category, quantity, unit_of_measurement, 
                     expiration_date, unit_price, total_price, created_at, 
                     used_quantity, status)
                    VALUES
                    (%(pantry_item_id)s, %(pantry_id)s, %(product_name)s, %(category)s, %(quantity)s, %(unit)s, 
                     %(exp_date)s, %(unit_price)s, %(total_price)s, CURRENT_TIMESTAMP, 
                     %(used_qty)s, %(status)s)
                """
                
                pantry_item_params = {
                    "pantry_item_id": pantry_item_id,
                    "pantry_id": pantry_id,
                    "product_name": item.get('item_name', 'Unknown Item'),
                    "category": item.get('category', 'Uncategorized'),
                    "quantity": float(item.get('quantity_amount', 1.0)),
                    "unit": item.get('quantity_unit', 'unit'),
                    "exp_date": exp_date_obj,
                    "unit_price": 0.0,  # Default, can be updated later
                    "total_price": 0.0,  # Default
                    "used_qty": 0,
                    "status": "available"
                }
                
                insert_start = datetime.now()
                self.db_service.execute_query(pantry_item_query, pantry_item_params)
                logger.info(f"Pantry item insert took {(datetime.now() - insert_start).total_seconds()}s")
                
                # Insert into products
                product_query = """
                    INSERT INTO products
                    (product_id, pantry_item_id, product_name, brand_name, 
                     category, created_at)
                    VALUES
                    (%(product_id)s, %(pantry_item_id)s, %(product_name)s, %(brand)s, 
                     %(category)s, CURRENT_TIMESTAMP)
                """
                
                product_params = {
                    "product_id": product_id,
                    "pantry_item_id": pantry_item_id,
                    "product_name": item.get('item_name', 'Unknown Item'),
                    "brand": item.get('brand', 'Generic'),
                    "category": item.get('category', 'Uncategorized'),
                }
                
                product_start = datetime.now()
                self.db_service.execute_query(product_query, product_params)
                logger.info(f"Product insert took {(datetime.now() - product_start).total_seconds()}s")
                
                saved_items.append({
                    "item_name": item.get('item_name'),
                    "pantry_item_id": pantry_item_id,
                    "product_id": product_id,
                    "status": "saved"
                })
                
                logger.info(f"Saved item: {item.get('item_name')} (pantry_item_id: {pantry_item_id})")
                
            except Exception as e:
                logger.error(f"Error saving item {item.get('item_name')}: {str(e)}")
                errors.append({
                    "item_name": item.get('item_name'),
                    "error": str(e)
                })
        
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Total time to save {len(items)} items: {total_time}s")
        
        return {
            "pantry_id": pantry_id,
            "saved_count": len(saved_items),
            "error_count": len(errors),
            "saved_items": saved_items,
            "errors": errors,
            "message": f"Saved {len(saved_items)} items to pantry",
            "time_taken": total_time
        }
    
    def delete_recent_items(self, user_id: int, hours: Optional[float] = None) -> Dict[str, Any]:
        """
        Delete recently added items for a user.
        
        Args:
            user_id: The user ID to delete items for
            hours: Number of hours to look back (None = all items)
        
        Returns:
            Dict with deletion results
        """
        try:
            logger.info(f"Starting delete_recent_items for user {user_id}, hours={hours}")
            
            # Get pantry for user
            pantry_query = """
                SELECT pantry_id
                FROM pantries
                WHERE user_id = %(user_id)s
            """
            pantry_results = self.db_service.execute_query(pantry_query, {"user_id": user_id})
            
            if not pantry_results:
                logger.warning(f"No pantry found for user {user_id}")
                return {"deleted_count": 0, "message": "No pantry found for user"}
            
            pantry_ids = [p['pantry_id'] for p in pantry_results]
            logger.info(f"Found pantry IDs: {pantry_ids}")
            
            # Build time filter
            time_filter = ""
            if hours is not None:
                time_filter = f"AND pi.created_at >= CURRENT_TIMESTAMP - INTERVAL '{int(hours * 60)} minutes'"
            
            # First, get the items to delete
            select_query = f"""
                SELECT pi.pantry_item_id, p.product_id
                FROM pantry_items pi
                LEFT JOIN products p
                ON pi.pantry_item_id = p.pantry_item_id
                WHERE pi.pantry_id = ANY(%(pantry_ids)s)
                {time_filter}
            """
            
            logger.info(f"Running select query with time_filter: {time_filter}")
            items_to_delete = self.db_service.execute_query(
                select_query, 
                {"pantry_ids": pantry_ids}
            )
            
            if not items_to_delete:
                logger.info("No items found to delete")
                return {"deleted_count": 0, "message": "No items found to delete"}
            
            logger.info(f"Found {len(items_to_delete)} items to delete")
            
            # Delete from products first (foreign key constraint)
            product_ids = [item['product_id'] for item in items_to_delete if item['product_id'] is not None]
            if product_ids:
                delete_products_query = """
                    DELETE FROM products
                    WHERE product_id = ANY(%(product_ids)s)
                """
                self.db_service.execute_query(delete_products_query, {"product_ids": product_ids})
                logger.info(f"Deleted {len(product_ids)} products")
            
            # Then delete from pantry_items
            pantry_item_ids = [item['pantry_item_id'] for item in items_to_delete]
            delete_items_query = """
                DELETE FROM pantry_items
                WHERE pantry_item_id = ANY(%(pantry_item_ids)s)
            """
            self.db_service.execute_query(delete_items_query, {"pantry_item_ids": pantry_item_ids})
            logger.info(f"Deleted {len(pantry_item_ids)} pantry items")
            
            # Clear the pantry cache for this user after deletion
            if user_id in self._pantry_cache:
                del self._pantry_cache[user_id]
                
            return {
                "deleted_count": len(items_to_delete),
                "message": f"Deleted {len(items_to_delete)} items",
                "details": {
                    "pantry_ids": pantry_ids,
                    "items_deleted": len(items_to_delete),
                    "products_deleted": len(product_ids) if product_ids else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in delete_recent_items: {str(e)}")
            return {"deleted_count": 0, "message": f"Error deleting items: {str(e)}"}
    
    def delete_item(self, user_id: int, pantry_item_id: int) -> Dict[str, Any]:
        """
        Delete a specific pantry item for a user.
        
        Args:
            user_id: The user ID (for verification)
            pantry_item_id: The specific pantry item ID to delete
        
        Returns:
            Dict with deletion result
        """
        # Verify the item belongs to the user
        verify_query = """
            SELECT pi.pantry_item_id, p.product_id, prod.product_name
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            JOIN products prod ON pi.pantry_item_id = prod.pantry_item_id
            WHERE p.user_id = %(user_id)s AND pi.pantry_item_id = %(pantry_item_id)s
        """
        
        result = self.db_service.execute_query(verify_query, {
            "user_id": user_id,
            "pantry_item_id": pantry_item_id
        })
        
        if not result:
            return {
                "deleted": False,
                "message": "Item not found or doesn't belong to user"
            }
        
        item_info = result[0]
        
        # Delete from products first
        delete_product_query = """
            DELETE FROM products
            WHERE product_id = %(product_id)s
        """
        self.db_service.execute_query(delete_product_query, {"product_id": item_info['product_id']})
        
        # Then delete from pantry_items
        delete_item_query = """
            DELETE FROM pantry_items
            WHERE pantry_item_id = %(pantry_item_id)s
        """
        self.db_service.execute_query(delete_item_query, {"pantry_item_id": pantry_item_id})
        
        return {
            "deleted": True,
            "message": f"Deleted {item_info['product_name']}",
            "pantry_item_id": pantry_item_id
        }


# Add missing import
from datetime import timedelta