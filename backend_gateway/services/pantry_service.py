# from database import get_db # No longer needed if using BigQueryService exclusively
from typing import Dict, Any, List
from backend_gateway.services.bigquery_service import BigQueryService # Added
import logging
# Assuming PantryItem is a Pydantic model or similar, define it or import it
# For now, let's assume it's a Dict for add_pantry_item simplicity in this refactor step.
# from ..models.pantry import PantryItem # Example if you have Pydantic models

logger = logging.getLogger(__name__)

class PantryService:
    def __init__(self, bq_service: BigQueryService): # Modified
        """
        Initializes the PantryService with a BigQueryService instance.
        """
        self.bq_service = bq_service

    async def get_user_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves all pantry items for a specific user from BigQuery.
        """
        query = """
            SELECT *
            FROM
              `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
            WHERE
              user_id = @user_id;
        """
        params = {"user_id": user_id}
        # BigQueryService.execute_query is synchronous, if it needs to be async,
        # it should be called with await or run in a thread pool.
        # For now, assuming BigQueryService.execute_query can be called directly.
        # If BigQueryService methods are async, this method should be async too.
        # Based on view_file output, execute_query is synchronous.
        return self.bq_service.execute_query(query, params)

    async def add_pantry_item(self, item_data: Any, user_id: int) -> Dict[str, Any]: # Modified signature
        """
        Adds a new pantry item to the database for a given pantry_id.
        NOTE: This is a basic adaptation and might need further review based on
        full product/pantry item creation workflow and Pydantic models.
        """
        # This query is a placeholder and needs to be adapted to your actual schema and needs
        # for inserting into pantry_items. It assumes pantry_id is known.
        # It also doesn't handle linking to a 'products' table, which might be necessary.
        
        # Example:
        # query = """
        #     INSERT INTO `adsp-34002-on02-prep-sense.Inventory.pantry_items`
        #     (pantry_id, product_name, quantity, unit_of_measurement, expiration_date, unit_price, total_price, status)
        #     VALUES (@pantry_id, @product_name, @quantity, @unit_of_measurement, @expiration_date, @unit_price, @total_price, @status)
        # """
        # params = {
        #     "pantry_id": pantry_id,
        #     "product_name": item_data.get("name"), # Assuming 'name' is product name
        #     "quantity": item_data.get("quantity"),
        #     "unit_of_measurement": item_data.get("unit_of_measurement"),
        #     "expiration_date": item_data.get("expiration_date"),
        #     "unit_price": item_data.get("unit_price"),
        #     "total_price": item_data.get("total_price"), # Often calculated
        #     "status": item_data.get("status", "available")
        # }
        # self.bq_service.execute_query(query, params) # INSERT queries might not return rows with execute_query
                                                    # BigQuery DML doesn't return the inserted row by default.
                                                    # Might need a different method in BigQueryService for DML
                                                    # or handle the fact that execute_query returns list of rows (empty for INSERT).
        
        # For now, let's make it clear this part is not fully implemented for BigQuery
        # and needs the actual INSERT logic.
        # raise NotImplementedError("add_pantry_item for BigQuery is not fully implemented yet.")
        
        # A more realistic add_pantry_item would be more complex, potentially checking
        # if product exists, getting product_id, then inserting into pantry_items.
        # The original add_pantry_item was very simple:
        # self.db.execute(
        # "INSERT INTO pantry_items (name, quantity, expiration_date) VALUES (?, ?, ?)",
        # (item["name"], item["quantity"], item["expiration_date"])
        # )
        # self.db.commit()
        # return {"message": "Item added successfully"}

        # Let's adapt the old logic to the new structure, acknowledging it's simplified:
        # This assumes 'pantry_items' has 'name', 'quantity', 'expiration_date' directly
        # and doesn't require pantry_id to be passed separately if item_data contains it,
        # or that the table structure is simpler.
        # The schema shows pantry_items needs pantry_id.
        
        # Use PantryItemManager for proper multi-table insertion
        from backend_gateway.services.pantry_item_manager import PantryItemManager
        
        pantry_manager = PantryItemManager(self.bq_service)
        
        # Convert PantryItemCreate to the format expected by add_items_batch
        items_to_add = [{
            'item_name': item_data.product_name,
            'quantity_amount': item_data.quantity,
            'quantity_unit': item_data.unit_of_measurement,
            'expected_expiration': item_data.expiration_date.isoformat() if item_data.expiration_date else None,
            'category': 'Uncategorized',  # Default category
            'brand': 'Generic'  # Default brand
        }]
        
        try:
            # Use the fast version for better UX
            result = pantry_manager.add_items_batch_fast(user_id, items_to_add)
            
            # Queue the actual DB write in background
            # For now, we'll do it synchronously but in production use Celery/background tasks
            import threading
            def write_to_db():
                try:
                    pantry_manager.add_items_batch(user_id, items_to_add)
                except Exception as e:
                    logger.error(f"Background write failed: {e}")
            
            # Start background thread
            thread = threading.Thread(target=write_to_db)
            thread.daemon = True
            thread.start()
            
            if result['saved_count'] > 0:
                saved_item = result['saved_items'][0]
                # Return a response immediately with the generated IDs
                # The actual database write happens but we don't wait for it
                return {
                    'id': str(saved_item['pantry_item_id']),
                    'pantry_item_id': saved_item['pantry_item_id'],
                    'product_id': saved_item['product_id'],
                    'product_name': saved_item['item_name'],
                    'item_name': saved_item['item_name'],
                    'quantity': item_data.quantity,
                    'quantity_amount': item_data.quantity,
                    'unit_of_measurement': item_data.unit_of_measurement,
                    'quantity_unit': item_data.unit_of_measurement,
                    'expiration_date': item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                    'expected_expiration': item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                    'category': 'Uncategorized',
                    'message': 'Item added successfully'
                }
            else:
                raise Exception("Failed to save item")
                
        except Exception as e:
            print(f"Error adding pantry item: {e}")
            raise
            
    async def delete_user_pantry_items(self, user_id: int, hours_ago: int = None, delete_all: bool = False) -> Dict[str, Any]:
        """
        Deletes pantry items for a specific user.
        
        Args:
            user_id: The user ID whose pantry items to delete
            hours_ago: If provided, only delete items added within the last X hours
            delete_all: If True, delete all items for this user (overrides hours_ago)
        
        Returns:
            Dict with deletion status and count of deleted items
        """
        # First get the pantry IDs for this user to ensure we only delete their items
        pantry_query = """
            SELECT pantry_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
            WHERE user_id = @user_id
        """
        pantry_params = {"user_id": user_id}
        pantry_results = self.bq_service.execute_query(pantry_query, pantry_params)
        
        if not pantry_results:
            return {"message": "No pantry found for this user", "deleted_count": 0}
            
        # Extract pantry IDs
        pantry_ids = [row["pantry_id"] for row in pantry_results]
        
        # Build the deletion query
        if delete_all:
            # Delete all items for this user's pantries
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_id IN UNNEST(@pantry_ids)
            """
            delete_params = {"pantry_ids": pantry_ids}
        elif hours_ago is not None:
            # Delete only items added within the specified time window
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_id IN UNNEST(@pantry_ids)
                AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours_ago HOUR)
            """
            delete_params = {"pantry_ids": pantry_ids, "hours_ago": hours_ago}
        else:
            # Default: delete items added in the last 24 hours
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_id IN UNNEST(@pantry_ids)
                AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            """
            delete_params = {"pantry_ids": pantry_ids}
        
        # Execute the deletion
        try:
            result = self.bq_service.execute_query(delete_query, delete_params)
            # For DML operations like DELETE, the result typically contains statistics
            # about the operation rather than deleted rows
            return {
                "message": "Pantry items deleted successfully", 
                "deleted_count": "See BigQuery job statistics",
                "user_id": user_id,
                "pantry_ids": pantry_ids
            }
        except Exception as e:
            print(f"Error deleting pantry items: {str(e)}")
            return {"message": f"Error deleting pantry items: {str(e)}", "deleted_count": 0}
            
    async def delete_detected_items(self, user_id: int, hours_ago: int = None) -> Dict[str, Any]:
        """
        Deletes ONLY pantry items that were added via vision detection.
        This is safer than delete_user_pantry_items as it preserves manually added items.
        
        Args:
            user_id: The user ID whose detected items to delete
            hours_ago: If provided, only delete detected items added within the last X hours
        
        Returns:
            Dict with deletion status and count of deleted items
        """
        # First get the pantry IDs for this user to ensure we only delete their items
        pantry_query = """
            SELECT pantry_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
            WHERE user_id = @user_id
        """
        pantry_params = {"user_id": user_id}
        pantry_results = self.bq_service.execute_query(pantry_query, pantry_params)
        
        if not pantry_results:
            return {"message": "No pantry found for this user", "deleted_count": 0}
            
        # Extract pantry IDs
        pantry_ids = [row["pantry_id"] for row in pantry_results]
        
        # Build the deletion query that ONLY targets items tagged with 'vision_detected'
        if hours_ago is not None:
            # Delete only vision-detected items added within the specified time window
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_id IN UNNEST(@pantry_ids)
                AND source = 'vision_detected'
                AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours_ago HOUR)
            """
            delete_params = {"pantry_ids": pantry_ids, "hours_ago": hours_ago}
        else:
            # Default: delete all vision-detected items regardless of time
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_id IN UNNEST(@pantry_ids)
                AND source = 'vision_detected'
            """
            delete_params = {"pantry_ids": pantry_ids}
        
        # Execute the deletion
        try:
            result = self.bq_service.execute_query(delete_query, delete_params)
            return {
                "message": "Vision detected items deleted successfully", 
                "deleted_count": "See BigQuery job statistics",
                "user_id": user_id,
                "pantry_ids": pantry_ids
            }
        except Exception as e:
            print(f"Error deleting vision detected items: {str(e)}")
            return {"message": f"Error deleting vision detected items: {str(e)}", "deleted_count": 0}
            
    async def update_pantry_item(self, pantry_item_id: int, item_data: Any) -> Dict[str, Any]:
        """
        Updates an existing pantry item and its associated product.
        
        Args:
            pantry_item_id: The ID of the pantry item to update
            item_data: The updated item data (PantryItemCreate)
            
        Returns:
            Dict with the updated item information
        """
        try:
            # First, check if the item exists and get its details
            check_query = """
                SELECT pi.*, p.product_id, p.product_name
                FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items` pi
                LEFT JOIN `adsp-34002-on02-prep-sense.Inventory.products` p
                ON pi.pantry_item_id = p.pantry_item_id
                WHERE pi.pantry_item_id = @pantry_item_id
            """
            check_params = {"pantry_item_id": pantry_item_id}
            existing_items = self.bq_service.execute_query(check_query, check_params)
            
            if not existing_items:
                return None
                
            existing_item = existing_items[0]
            
            # Update the pantry_items table
            update_pantry_query = """
                UPDATE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                SET 
                    quantity = @quantity,
                    unit_of_measurement = @unit_of_measurement,
                    expiration_date = @expiration_date,
                    unit_price = CASE WHEN @unit_price IS NULL THEN NULL ELSE CAST(@unit_price AS FLOAT64) END,
                    total_price = CASE WHEN @total_price IS NULL THEN NULL ELSE CAST(@total_price AS FLOAT64) END
                WHERE pantry_item_id = @pantry_item_id
            """
            
            # Calculate total price if unit price is provided
            total_price = None
            if item_data.unit_price:
                total_price = item_data.unit_price * item_data.quantity
            
            pantry_params = {
                "pantry_item_id": pantry_item_id,
                "quantity": float(item_data.quantity) if item_data.quantity is not None else 0.0,
                "unit_of_measurement": item_data.unit_of_measurement,
                "expiration_date": item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                "unit_price": float(item_data.unit_price) if item_data.unit_price is not None else None,
                "total_price": float(total_price) if total_price is not None else None
            }
            
            self.bq_service.execute_query(update_pantry_query, pantry_params)
            
            # Update the products table if product exists
            if existing_item.get('product_id'):
                update_product_query = """
                    UPDATE `adsp-34002-on02-prep-sense.Inventory.products`
                    SET 
                        product_name = @product_name,
                        category = @category
                    WHERE product_id = @product_id
                """
                
                product_params = {
                    "product_id": existing_item['product_id'],
                    "product_name": item_data.product_name,
                    "category": getattr(item_data, 'category', 'Uncategorized')
                }
                
                self.bq_service.execute_query(update_product_query, product_params)
            
            # Return the updated item information
            return {
                'id': str(pantry_item_id),
                'pantry_item_id': pantry_item_id,
                'product_id': existing_item.get('product_id'),
                'product_name': item_data.product_name,
                'item_name': item_data.product_name,
                'quantity': item_data.quantity,
                'quantity_amount': item_data.quantity,
                'unit_of_measurement': item_data.unit_of_measurement,
                'quantity_unit': item_data.unit_of_measurement,
                'expiration_date': item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                'expected_expiration': item_data.expiration_date.isoformat() if item_data.expiration_date else None,
                'category': getattr(item_data, 'category', 'Uncategorized'),
                'message': 'Item updated successfully'
            }
            
        except Exception as e:
            print(f"Error updating pantry item: {str(e)}")
            raise
            
    async def delete_single_pantry_item(self, pantry_item_id: int) -> bool:
        """
        Deletes a single pantry item by ID.
        
        Args:
            pantry_item_id: The ID of the pantry item to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # First check if the item exists
            check_query = """
                SELECT pantry_item_id
                FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_item_id = @pantry_item_id
            """
            check_params = {"pantry_item_id": pantry_item_id}
            existing_items = self.bq_service.execute_query(check_query, check_params)
            
            if not existing_items:
                return False
            
            # Delete the item
            delete_query = """
                DELETE FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
                WHERE pantry_item_id = @pantry_item_id
            """
            delete_params = {"pantry_item_id": pantry_item_id}
            
            self.bq_service.execute_query(delete_query, delete_params)
            
            # Note: We might also want to delete from products table if this was the only pantry_item
            # referencing that product, but for now we'll leave products intact
            
            return True
            
        except Exception as e:
            print(f"Error deleting single pantry item: {str(e)}")
            raise
    
    async def get_pantry_item_by_id(self, pantry_item_id: int) -> Dict[str, Any]:
        """
        Get a specific pantry item by its ID
        
        Args:
            pantry_item_id: The pantry item ID
            
        Returns:
            Dict with pantry item details or None if not found
        """
        query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry_items`
            WHERE pantry_item_id = @pantry_item_id
        """
        params = {"pantry_item_id": pantry_item_id}
        
        try:
            results = self.bq_service.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting pantry item {pantry_item_id}: {str(e)}")
            raise
    
    async def update_pantry_item_quantity(self, pantry_item_id: int, new_quantity: float) -> Dict[str, Any]:
        """
        Update the quantity of a pantry item
        
        Args:
            pantry_item_id: The pantry item ID
            new_quantity: The new quantity value
            
        Returns:
            Dict with update status
        """
        update_query = """
            UPDATE `adsp-34002-on02-prep-sense.Inventory.pantry_items`
            SET quantity = @new_quantity,
                updated_at = CURRENT_TIMESTAMP()
            WHERE pantry_item_id = @pantry_item_id
        """
        params = {
            "pantry_item_id": pantry_item_id,
            "new_quantity": new_quantity
        }
        
        try:
            result = self.bq_service.execute_query(update_query, params)
            return {
                "success": True,
                "pantry_item_id": pantry_item_id,
                "new_quantity": new_quantity,
                "message": "Quantity updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating pantry item quantity: {str(e)}")
            raise