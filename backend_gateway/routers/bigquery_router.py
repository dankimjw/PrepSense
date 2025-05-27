"""REST endpoints for interacting with BigQuery tables."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv

# Import our BigQuery service
from ..services.bigquery_service import BigQueryService
from ..core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["bigquery"],
    responses={404: {"description": "Not found"}},
)

# Initialize the BigQuery dependency with proper error handling
def get_bigquery_service():
    """Dependency that provides a BigQueryService instance."""
    try:
        service = BigQueryService()
        return service
    except Exception as e:
        logger.error(f"BigQuery service initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"BigQuery service unavailable: {str(e)}"
        )

# Pydantic models for request/response validation
class PantryItemBase(BaseModel):
    pantry_id: int
    quantity: float
    unit_of_measurement: str
    expiration_date: date
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    status: Optional[str] = "active"

class PantryItemCreate(PantryItemBase):
    pass

class PantryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit_of_measurement: Optional[str] = None
    expiration_date: Optional[date] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    status: Optional[str] = None

class PantryItem(PantryItemBase):
    pantry_item_id: int
    created_at: datetime
    used_quantity: Optional[int] = 0

    class Config:
        from_attributes = True

# Helper function to convert BigQuery row to Pydantic model
def row_to_pantry_item(row: Dict) -> PantryItem:
    return PantryItem(**row)

# Query execution models for the BigQuery tester
class QueryExecuteRequest(BaseModel):
    query: str
    queryType: Optional[str] = "SELECT"
    table: Optional[str] = None

class QueryExecuteResponse(BaseModel):
    success: bool
    query: str
    result: List[Dict[str, Any]]
    execution_time: str
    rows_affected: Optional[int] = None
    error: Optional[str] = None

# Routes
@router.get("/pantry-items/", response_model=List[PantryItem])
async def get_pantry_items(
    pantry_id: Optional[int] = None,
    status: Optional[str] = None,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Get all pantry items, optionally filtered by pantry_id and/or status.
    """
    try:
        query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.pantry_items`
            WHERE 1=1
        """
        params = {}
        
        if pantry_id is not None:
            query += " AND pantry_id = @pantry_id"
            params["pantry_id"] = pantry_id
            
        if status is not None:
            query += " AND status = @status"
            params["status"] = status
            
        query += " ORDER BY created_at DESC"
        
        rows = bq.execute_query(query, params)
        return [row_to_pantry_item(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Error fetching pantry items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pantry items"
        )

@router.get("/pantry-items/{item_id}", response_model=PantryItem)
async def get_pantry_item(
    item_id: int,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Get a single pantry item by ID.
    """
    try:
        query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.pantry_items`
            WHERE pantry_item_id = @item_id
            LIMIT 1
        """
        
        rows = bq.execute_query(query, {"item_id": item_id})
        
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pantry item with ID {item_id} not found"
            )
            
        return row_to_pantry_item(rows[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pantry item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pantry item"
        )

@router.post("/pantry-items/", response_model=PantryItem, status_code=status.HTTP_201_CREATED)
async def create_pantry_item(
    item: PantryItemCreate,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Create a new pantry item.
    """
    try:
        # Calculate total price if unit price is provided but total price is not
        item_data = item.dict()
        if item_data.get("unit_price") is not None and item_data.get("total_price") is None:
            item_data["total_price"] = item_data["unit_price"] * item_data["quantity"]
        
        # Set default values
        item_data["created_at"] = datetime.utcnow()
        item_data["used_quantity"] = 0
        
        # Insert the new item
        inserted_rows = bq.insert_rows("pantry_items", [item_data])
        
        if inserted_rows == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create pantry item"
            )
        
        # Get the newly created item (this is a limitation of BigQuery's streaming buffer)
        # In a production app, you might use a transaction or a different approach
        query = f"""
            SELECT * FROM `{bq.project_id}.{bq.dataset_id}.pantry_items`
            WHERE pantry_id = @pantry_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        rows = bq.execute_query(query, {"pantry_id": item.pantry_id})
        
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created pantry item"
            )
            
        return row_to_pantry_item(rows[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pantry item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pantry item"
        )

@router.put("/pantry-items/{item_id}", response_model=PantryItem)
async def update_pantry_item(
    item_id: int,
    item_update: PantryItemUpdate,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Update an existing pantry item.
    """
    try:
        # Get the current item to ensure it exists
        current_item = await get_pantry_item(item_id, bq)
        
        # Prepare the update data
        update_data = item_update.dict(exclude_unset=True)
        
        # Recalculate total price if quantity or unit_price is being updated
        if ("quantity" in update_data or "unit_price" in update_data) and "total_price" not in update_data:
            quantity = update_data.get("quantity", current_item.quantity)
            unit_price = update_data.get("unit_price", current_item.unit_price)
            if unit_price is not None:
                update_data["total_price"] = quantity * unit_price
        
        # Update the item
        updated_rows = bq.update_rows(
            "pantry_items",
            update_data,
            {"pantry_item_id": item_id}
        )
        
        if updated_rows == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update pantry item"
            )
        
        # Return the updated item
        return await get_pantry_item(item_id, bq)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pantry item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pantry item"
        )

@router.delete("/pantry-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pantry_item(
    item_id: int,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Delete a pantry item.
    """
    try:
        # Check if the item exists
        await get_pantry_item(item_id, bq)
        
        # Delete the item
        deleted_rows = bq.delete_rows(
            "pantry_items",
            {"pantry_item_id": item_id}
        )
        
        if deleted_rows == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete pantry item"
            )
            
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pantry item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete pantry item"
        )

@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    request: QueryExecuteRequest,
    bq: BigQueryService = Depends(get_bigquery_service)
) -> QueryExecuteResponse:
    """
    Execute a BigQuery SQL query.
    Supports SELECT, INSERT, UPDATE, DELETE, and custom queries.
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Executing query: {request.query}")
        
        result = bq.execute_query(request.query)
        
        end_time = time.time()
        execution_time = f"{end_time - start_time:.2f}s"
        
        # Determine rows affected for non-SELECT queries
        rows_affected = None
        if request.queryType and request.queryType.upper() != 'SELECT':
            rows_affected = len(result) if result else 0
        
        return QueryExecuteResponse(
            success=True,
            query=request.query,
            result=result,
            execution_time=execution_time,
            rows_affected=rows_affected
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return QueryExecuteResponse(
            success=False,
            query=request.query,
            result=[],
            execution_time="0s",
            error=str(e)
        )

@router.get("/tables")
async def get_tables(
    bq: BigQueryService = Depends(get_bigquery_service)
) -> List[Dict[str, str]]:
    """
    Get list of available tables in the dataset.
    """
    try:
        # Get dataset reference from real BigQuery service
        dataset_ref = bq.client.dataset(bq.dataset_id)
        tables = bq.client.list_tables(dataset_ref)
        
        table_list = []
        for table in tables:
            table_list.append({
                "tableId": table.table_id,
                "description": f"Table: {table.table_id}"
            })
        
        return table_list
        
    except Exception as e:
        logger.error(f"Failed to get tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tables"
        )
