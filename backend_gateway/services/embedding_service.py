"""
Embedding Service for PrepSense
Generates vector embeddings for semantic search using OpenAI's embedding models
"""

import os
import logging
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import asyncio
import httpx
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingService:
    """
    Service for generating embeddings for recipes, products, and pantry items
    using OpenAI's text embedding models
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding service
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY env var
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required for embedding service")
        
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0
        )
        
        # Model configuration
        self.model = "text-embedding-3-small"  # 1536 dimensions, good balance of performance/cost
        self.dimensions = 1536
        
        # Rate limiting
        self.requests_per_minute = 3000
        self.tokens_per_minute = 1000000
        self._request_times = []
        
    async def generate_embedding(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> EmbeddingResult:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            metadata: Optional metadata to attach to the result
            
        Returns:
            EmbeddingResult with the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Rate limiting
        await self._check_rate_limit()
        
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "input": text,
                    "model": self.model
                }
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data['data'][0]['embedding']
            
            return EmbeddingResult(
                text=text,
                embedding=embedding,
                model=self.model,
                dimensions=self.dimensions,
                metadata=metadata
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResults
        """
        if not texts:
            return []
        
        # OpenAI allows up to 2048 embeddings per request
        batch_size = 100  # Conservative batch size
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Rate limiting
            await self._check_rate_limit()
            
            try:
                response = await self.client.post(
                    "https://api.openai.com/v1/embeddings",
                    json={
                        "input": batch,
                        "model": self.model
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                for j, embedding_data in enumerate(data['data']):
                    results.append(EmbeddingResult(
                        text=batch[j],
                        embedding=embedding_data['embedding'],
                        model=self.model,
                        dimensions=self.dimensions
                    ))
                    
            except Exception as e:
                logger.error(f"Error in batch embedding generation: {e}")
                # Continue with next batch instead of failing completely
                continue
        
        return results
    
    async def generate_recipe_embedding(self, recipe: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a recipe by combining relevant fields
        
        Args:
            recipe: Recipe dictionary with name, description, ingredients, etc.
            
        Returns:
            Embedding vector
        """
        # Combine relevant recipe information
        text_parts = []
        
        # Add recipe name with weight
        if recipe.get('name'):
            text_parts.append(f"Recipe: {recipe['name']}")
        
        # Add description
        if recipe.get('description'):
            text_parts.append(f"Description: {recipe['description']}")
        
        # Add ingredients
        if recipe.get('ingredients'):
            if isinstance(recipe['ingredients'], list):
                ingredients_text = ", ".join(recipe['ingredients'])
            else:
                ingredients_text = str(recipe['ingredients'])
            text_parts.append(f"Ingredients: {ingredients_text}")
        
        # Add cuisine type if available
        if recipe.get('cuisine'):
            text_parts.append(f"Cuisine: {recipe['cuisine']}")
        
        # Add tags if available
        if recipe.get('tags'):
            if isinstance(recipe['tags'], list):
                tags_text = ", ".join(recipe['tags'])
            else:
                tags_text = str(recipe['tags'])
            text_parts.append(f"Tags: {tags_text}")
        
        # Add dietary info
        if recipe.get('dietary_preferences'):
            dietary = recipe['dietary_preferences']
            if isinstance(dietary, list):
                dietary_text = ", ".join(dietary)
            else:
                dietary_text = str(dietary)
            text_parts.append(f"Dietary: {dietary_text}")
        
        # Combine all parts
        full_text = " | ".join(text_parts)
        
        # Generate embedding
        result = await self.generate_embedding(full_text, metadata={'type': 'recipe', 'id': recipe.get('id')})
        return result.embedding
    
    async def generate_product_embedding(self, product: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a product
        
        Args:
            product: Product dictionary with name, category, brand, etc.
            
        Returns:
            Embedding vector
        """
        # Combine relevant product information
        text_parts = []
        
        # Add product name
        if product.get('name'):
            text_parts.append(f"Product: {product['name']}")
        
        # Add brand
        if product.get('brand'):
            text_parts.append(f"Brand: {product['brand']}")
        
        # Add category
        if product.get('category'):
            text_parts.append(f"Category: {product['category']}")
        
        # Add description if available
        if product.get('description'):
            text_parts.append(f"Description: {product['description']}")
        
        # Add barcode for uniqueness
        if product.get('barcode'):
            text_parts.append(f"Barcode: {product['barcode']}")
        
        # Combine all parts
        full_text = " | ".join(text_parts)
        
        # Generate embedding
        result = await self.generate_embedding(full_text, metadata={'type': 'product', 'id': product.get('id')})
        return result.embedding
    
    async def generate_pantry_item_embedding(self, item: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a pantry item
        
        Args:
            item: Pantry item dictionary
            
        Returns:
            Embedding vector
        """
        # Get product info if available
        product_info = item.get('product', {})
        
        # Combine relevant information
        text_parts = []
        
        # Add item name
        if item.get('item_name'):
            text_parts.append(f"Item: {item['item_name']}")
        elif product_info.get('name'):
            text_parts.append(f"Item: {product_info['name']}")
        
        # Add category
        if item.get('category'):
            text_parts.append(f"Category: {item['category']}")
        
        # Add brand if available
        if product_info.get('brand'):
            text_parts.append(f"Brand: {product_info['brand']}")
        
        # Add location
        if item.get('location'):
            text_parts.append(f"Location: {item['location']}")
        
        # Combine all parts
        full_text = " | ".join(text_parts)
        
        # Generate embedding
        result = await self.generate_embedding(full_text, metadata={'type': 'pantry_item', 'id': item.get('id')})
        return result.embedding
    
    async def generate_query_embedding(self, query: str, query_type: str = "general") -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            query_type: Type of query (recipe, product, pantry, general)
            
        Returns:
            Embedding vector
        """
        # Add context based on query type
        if query_type == "recipe":
            full_text = f"Recipe search: {query}"
        elif query_type == "product":
            full_text = f"Product search: {query}"
        elif query_type == "pantry":
            full_text = f"Pantry item search: {query}"
        else:
            full_text = query
        
        # Generate embedding
        result = await self.generate_embedding(full_text, metadata={'type': 'query', 'query_type': query_type})
        return result.embedding
    
    async def _check_rate_limit(self):
        """Simple rate limiting to avoid hitting OpenAI limits"""
        current_time = datetime.now()
        
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if (current_time - t).seconds < 60]
        
        # If we're at the limit, wait
        if len(self._request_times) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self._request_times[0]).seconds
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self._request_times.append(current_time)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global service instance
_embedding_service = None

def get_embedding_service(api_key: Optional[str] = None) -> EmbeddingService:
    """Get singleton instance of EmbeddingService"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(api_key)
    return _embedding_service