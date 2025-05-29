"""Service for managing pantry items across all related BigQuery tables."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from backend_gateway.services.bigquery_service import BigQueryService

logger = logging.getLogger(__name__)

class PantryItemManager:
    """Manages the insertion of pantry items across all related tables."""
    
    def __init__(self, bq_service: BigQueryService):
        self.bq_service = bq_service
        
    def get_next_id(self, table: str, id_column: str) -> int:
        """Get the next available ID for a table by finding max + 1."""
        query = f"""
            SELECT COALESCE(MAX({id_column}), 0) + 1 as next_id
            FROM `adsp-34002-on02-prep-sense.Inventory.{table}`
        """
        result = self.bq_service.execute_query(query)
        return result[0]['next_id']
    
    def get_or_create_pantry(self, user_id: int) -> int:
        """Get existing pantry for user or create a new one."""
        # Check if user has a pantry
        query = """
            SELECT pantry_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
            WHERE user_id = @user_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = self.bq_service.execute_query(query, {"user_id": user_id})
        
        if result:
            return result[0]['pantry_id']
        
        # Create new pantry
        next_pantry_id = self.get_next_id('pantry', 'pantry_id')
        
        insert_query = """
            INSERT INTO `adsp-34002-on02-prep-sense.Inventory.pantry`
            (pantry_id, user_id, pantry_name, created_at)
            VALUES
            (@pantry_id, @user_id, @pantry_name, CURRENT_TIMESTAMP())
        """
        
        params = {
            "pantry_id": next_pantry_id,
            "user_id": user_id,
            "pantry_name": f"User {user_id} Pantry"
        }
        
        self.bq_service.execute_query(insert_query, params)
        logger.info(f"Created new pantry {next_pantry_id} for user {user_id}")
        
        return next_pantry_id
    
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
        pantry_id = self.get_or_create_pantry(user_id)
        
        # Get starting IDs
        next_pantry_item_id = self.get_next_id('pantry_items', 'pantry_item_id')
        next_product_id = self.get_next_id('products', 'product_id')
        
        saved_items = []
        errors = []
        
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
                    INSERT INTO `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                    (pantry_item_id, pantry_id, quantity, unit_of_measurement, 
                     expiration_date, unit_price, total_price, created_at, 
                     used_quantity, status)
                    VALUES
                    (@pantry_item_id, @pantry_id, @quantity, @unit, 
                     @exp_date, @unit_price, @total_price, CURRENT_TIMESTAMP(), 
                     @used_qty, @status)
                """
                
                pantry_item_params = {
                    "pantry_item_id": pantry_item_id,
                    "pantry_id": pantry_id,
                    "quantity": float(item.get('quantity_amount', 1.0)),
                    "unit": item.get('quantity_unit', 'unit'),
                    "exp_date": exp_date_obj,
                    "unit_price": 0.0,  # Default, can be updated later
                    "total_price": 0.0,  # Default
                    "used_qty": 0,
                    "status": "available"
                }
                
                self.bq_service.execute_query(pantry_item_query, pantry_item_params)
                
                # Insert into products
                product_query = """
                    INSERT INTO `adsp-34002-on02-prep-sense.Inventory.products`
                    (product_id, pantry_item_id, product_name, brand_name, 
                     category, upc_code, created_at)
                    VALUES
                    (@product_id, @pantry_item_id, @product_name, @brand, 
                     @category, @upc, CURRENT_TIMESTAMP())
                """
                
                product_params = {
                    "product_id": product_id,
                    "pantry_item_id": pantry_item_id,
                    "product_name": item.get('item_name', 'Unknown Item'),
                    "brand": item.get('brand', 'Generic'),
                    "category": item.get('category', 'Uncategorized'),
                    "upc": item.get('upc_code', ''),  # Can be empty
                }
                
                self.bq_service.execute_query(product_query, product_params)
                
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
        
        return {
            "pantry_id": pantry_id,
            "saved_count": len(saved_items),
            "error_count": len(errors),
            "saved_items": saved_items,
            "errors": errors,
            "message": f"Saved {len(saved_items)} items to pantry"
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
        # Get pantry for user
        pantry_query = """
            SELECT pantry_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
            WHERE user_id = @user_id
        """
        pantry_results = self.bq_service.execute_query(pantry_query, {"user_id": user_id})
        
        if not pantry_results:
            return {"deleted_count": 0, "message": "No pantry found for user"}
        
        pantry_ids = [p['pantry_id'] for p in pantry_results]
        
        # Build time filter
        time_filter = ""
        if hours is not None:
            time_filter = f"AND pi.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(hours * 60)} MINUTE)"
        
        # First, get the items to delete
        select_query = f"""
            SELECT pi.pantry_item_id, p.product_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items` pi
            JOIN `adsp-34002-on02-prep-sense.Inventory.products` p
            ON pi.pantry_item_id = p.pantry_item_id
            WHERE pi.pantry_id IN UNNEST(@pantry_ids)
            {time_filter}
        """
        
        items_to_delete = self.bq_service.execute_query(
            select_query, 
            {"pantry_ids": pantry_ids}
        )
        
        if not items_to_delete:
            return {"deleted_count": 0, "message": "No items found to delete"}
        
        # Delete from products first (foreign key constraint)
        product_ids = [item['product_id'] for item in items_to_delete]
        delete_products_query = """
            DELETE FROM `adsp-34002-on02-prep-sense.Inventory.products`
            WHERE product_id IN UNNEST(@product_ids)
        """
        self.bq_service.execute_query(delete_products_query, {"product_ids": product_ids})
        
        # Then delete from pantry_items
        pantry_item_ids = [item['pantry_item_id'] for item in items_to_delete]
        delete_items_query = """
            DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
            WHERE pantry_item_id IN UNNEST(@pantry_item_ids)
        """
        self.bq_service.execute_query(delete_items_query, {"pantry_item_ids": pantry_item_ids})
        
        return {
            "deleted_count": len(items_to_delete),
            "message": f"Deleted {len(items_to_delete)} items"
        }


# Add missing import
from datetime import timedelta