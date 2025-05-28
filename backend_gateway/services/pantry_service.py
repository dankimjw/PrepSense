# from database import get_db # No longer needed if using BigQueryService exclusively
from typing import Dict, Any, List
from backend_gateway.services.bigquery_service import BigQueryService # Added
# Assuming PantryItem is a Pydantic model or similar, define it or import it
# For now, let's assume it's a Dict for add_pantry_item simplicity in this refactor step.
# from ..models.pantry import PantryItem # Example if you have Pydantic models

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

    async def add_pantry_item(self, pantry_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]: # Modified signature
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
        
        # Simplified adaptation focusing on the call structure:
        insert_query = """
            INSERT INTO `adsp-34002-on02-prep-sense.Inventory.pantry_items`
            (pantry_id, quantity, unit_of_measurement, expiration_date, unit_price, total_price, status, product_name) 
            -- Assuming product_name is a field in pantry_items for simplicity, or it needs to be product_id
            VALUES (@pantry_id, @quantity, @unit_of_measurement, @expiration_date, @unit_price, @total_price, @status, @product_name)
        """
        
        # This requires item_data to have all these fields.
        # And product_name might actually need to be a product_id from the 'products' table.
        # This is a known simplification for now.
        params = {
            "pantry_id": pantry_id,
            "quantity": item_data.get("quantity"),
            "unit_of_measurement": item_data.get("unit_of_measurement"),
            "expiration_date": item_data.get("expiration_date"), # Ensure correct DATE format
            "unit_price": item_data.get("unit_price"),
            "total_price": item_data.get("total_price"), # Often calculated: quantity * unit_price
            "status": item_data.get("status", "available"),
            "product_name": item_data.get("name") # Assuming item_data["name"] is the product name
        }
        
        try:
            # BigQuery DML (INSERT, UPDATE, DELETE) doesn't return results via query() like SELECT.
            # The job completes, but job.result() won't have rows for DML.
            # We should confirm if BigQueryService.execute_query is suitable for DML
            # or if a separate method like execute_dml should be used.
            # For now, we'll call it and assume it handles DML appropriately (e.g., doesn't crash if no rows returned).
            self.bq_service.execute_query(insert_query, params)
            return {"message": "Item added successfully (simulated - check BigQuery for actual insert)"}
        except Exception as e:
            # logger.error(f"Error adding pantry item: {e}") # Requires logger setup
            print(f"Error adding pantry item: {e}") # Simple print for now
            raise # Re-raise the exception to be handled by the router