"""
Semantic Search API Router
Provides endpoints for semantic search functionality using vector embeddings
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.config.database import get_database_service
from backend_gateway.routers.users import get_current_user
from backend_gateway.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/semantic-search",
    tags=["semantic-search"]
)


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity score")


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    available_ingredients: List[str] = Field(default_factory=list, description="List of available ingredients")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    semantic_weight: float = Field(0.6, ge=0.0, le=1.0, description="Weight for semantic similarity")
    ingredient_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for ingredient matching")


class RecipeSearchResult(BaseModel):
    """Response model for recipe search results"""
    recipe_id: int
    recipe_name: str
    similarity_score: float
    ingredients: List[str]
    description: Optional[str]
    # Additional fields for hybrid search
    ingredient_match_score: Optional[float] = None
    combined_score: Optional[float] = None
    matched_ingredients: Optional[List[str]] = None
    missing_ingredients: Optional[List[str]] = None


class ProductSearchResult(BaseModel):
    """Response model for product search results"""
    product_id: int
    product_name: str
    brand: Optional[str]
    category: Optional[str]
    similarity_score: float


class PantryItemSearchResult(BaseModel):
    """Response model for pantry item search results"""
    id: int
    item_name: str
    category: Optional[str]
    location: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    similarity_score: float


@router.post("/recipes", response_model=List[RecipeSearchResult])
async def semantic_search_recipes(
    request: SemanticSearchRequest,
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> List[RecipeSearchResult]:
    """
    Search for recipes using semantic similarity
    
    This endpoint uses vector embeddings to find recipes that are semantically
    similar to the search query, even if they don't contain the exact keywords.
    """
    try:
        # Perform semantic search
        results = await db_service.semantic_search_recipes(
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Log search query for analytics
        await db_service.log_search_query(
            user_id=current_user.id,
            query_text=request.query,
            query_type="recipe",
            results_count=len(results)
        )
        
        # Convert results to response model
        return [
            RecipeSearchResult(
                recipe_id=result['recipe_id'],
                recipe_name=result['recipe_name'],
                similarity_score=result['similarity_score'],
                ingredients=result['ingredients'] or [],
                description=result.get('description')
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error in semantic recipe search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform semantic search")


@router.post("/recipes/hybrid", response_model=List[RecipeSearchResult])
async def hybrid_recipe_search(
    request: HybridSearchRequest,
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> List[RecipeSearchResult]:
    """
    Search for recipes using hybrid approach (semantic + ingredient matching)
    
    This endpoint combines semantic similarity with ingredient availability
    to find the most relevant recipes based on both the search intent and
    available ingredients in the pantry.
    """
    try:
        # Validate weights sum to 1.0
        if abs(request.semantic_weight + request.ingredient_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="Semantic weight and ingredient weight must sum to 1.0"
            )
        
        # Perform hybrid search
        results = await db_service.hybrid_recipe_search(
            query=request.query,
            available_ingredients=request.available_ingredients,
            limit=request.limit,
            semantic_weight=request.semantic_weight,
            ingredient_weight=request.ingredient_weight
        )
        
        # Log search query for analytics
        await db_service.log_search_query(
            user_id=current_user.id,
            query_text=f"Hybrid: {request.query}",
            query_type="recipe",
            results_count=len(results)
        )
        
        # Convert results to response model
        return [
            RecipeSearchResult(
                recipe_id=result['recipe_id'],
                recipe_name=result['recipe_name'],
                similarity_score=result['semantic_score'],
                ingredients=[],  # Not returned by stored procedure
                description=None,
                ingredient_match_score=result['ingredient_match_score'],
                combined_score=result['combined_score'],
                matched_ingredients=result['matched_ingredients'] or [],
                missing_ingredients=result['missing_ingredients'] or []
            )
            for result in results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hybrid recipe search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform hybrid search")


@router.post("/products", response_model=List[ProductSearchResult])
async def semantic_search_products(
    request: SemanticSearchRequest,
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> List[ProductSearchResult]:
    """
    Search for products using semantic similarity
    
    This endpoint uses vector embeddings to find products that are semantically
    similar to the search query.
    """
    try:
        # Perform semantic search
        results = await db_service.semantic_search_products(
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # Log search query for analytics
        await db_service.log_search_query(
            user_id=current_user.id,
            query_text=request.query,
            query_type="product",
            results_count=len(results)
        )
        
        # Convert results to response model
        return [
            ProductSearchResult(
                product_id=result['product_id'],
                product_name=result['product_name'],
                brand=result.get('brand'),
                category=result.get('category'),
                similarity_score=result['similarity_score']
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error in semantic product search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform semantic search")


@router.get("/pantry/similar/{item_name}", response_model=List[PantryItemSearchResult])
async def find_similar_pantry_items(
    item_name: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of similar items"),
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> List[PantryItemSearchResult]:
    """
    Find pantry items similar to a given item name
    
    This endpoint is useful for finding duplicates or similar items
    that might be the same product with slightly different names.
    """
    try:
        # Find similar items
        results = await db_service.find_similar_pantry_items(
            item_name=item_name,
            limit=limit
        )
        
        # Convert results to response model
        return [
            PantryItemSearchResult(
                id=result['id'],
                item_name=result['item_name'],
                category=result.get('category'),
                location=result.get('location'),
                quantity=result.get('quantity'),
                unit=result.get('unit'),
                similarity_score=result['similarity_score']
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Error finding similar pantry items: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar items")


@router.post("/update-embedding/{entity_type}/{entity_id}")
async def update_entity_embedding(
    entity_type: str,
    entity_id: int,
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> Dict[str, Any]:
    """
    Update the embedding for a specific entity
    
    This endpoint regenerates the embedding for a recipe, product, or pantry item.
    Useful when the entity data has been updated.
    """
    try:
        if entity_type not in ["recipe", "product"]:
            raise HTTPException(
                status_code=400,
                detail="Entity type must be 'recipe' or 'product'"
            )
        
        # Update embedding based on entity type
        if entity_type == "recipe":
            success = await db_service.update_recipe_embedding(entity_id)
        else:  # product
            success = await db_service.update_product_embedding(entity_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Embedding updated for {entity_type} {entity_id}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"{entity_type.capitalize()} {entity_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to update embedding")


@router.get("/search-analytics")
async def get_search_analytics(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: UserInDB = Depends(get_current_user),
    db_service: PostgresService = Depends(get_database_service)
) -> Dict[str, Any]:
    """
    Get search analytics for the current user
    
    Returns information about recent searches, popular queries, and search patterns.
    """
    try:
        with db_service.get_cursor() as cursor:
            # Get user's recent searches
            cursor.execute("""
                SELECT 
                    query_text,
                    query_type,
                    results_count,
                    clicked_result_id,
                    created_at
                FROM search_query_embeddings
                WHERE user_id = %(user_id)s
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '%(days)s days'
                ORDER BY created_at DESC
                LIMIT 20
            """, {"user_id": current_user.id, "days": days})
            
            recent_searches = cursor.fetchall()
            
            # Get popular search terms
            cursor.execute("""
                SELECT 
                    query_text,
                    COUNT(*) as search_count,
                    AVG(results_count) as avg_results
                FROM search_query_embeddings
                WHERE user_id = %(user_id)s
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '%(days)s days'
                GROUP BY query_text
                ORDER BY search_count DESC
                LIMIT 10
            """, {"user_id": current_user.id, "days": days})
            
            popular_searches = cursor.fetchall()
            
            # Get search type distribution
            cursor.execute("""
                SELECT 
                    query_type,
                    COUNT(*) as count
                FROM search_query_embeddings
                WHERE user_id = %(user_id)s
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '%(days)s days'
                GROUP BY query_type
            """, {"user_id": current_user.id, "days": days})
            
            search_types = cursor.fetchall()
            
        return {
            "recent_searches": recent_searches,
            "popular_searches": popular_searches,
            "search_types": search_types,
            "analysis_period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search analytics")