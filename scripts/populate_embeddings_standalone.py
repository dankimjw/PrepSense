#!/usr/bin/env python3
"""
Standalone script to populate embeddings without circular imports
"""

import asyncio
import json
import logging
import os
from datetime import datetime

import httpx
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleEmbeddingService:
    """Simplified embedding service"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}, timeout=30.0
        )
        self.model = "text-embedding-3-small"

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text"""
        response = await self.client.post(
            "https://api.openai.com/v1/embeddings", json={"input": text, "model": self.model}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def close(self):
        await self.client.aclose()


class EmbeddingPopulator:
    """Populate embeddings for PrepSense data"""

    def __init__(self):
        # Database connection
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST"),
            "database": os.getenv("POSTGRES_DATABASE"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

        self.embedding_service = SimpleEmbeddingService()

        # Stats
        self.stats = {
            "recipes": {"total": 0, "processed": 0, "failed": 0},
            "products": {"total": 0, "processed": 0, "failed": 0},
            "pantry_items": {"total": 0, "processed": 0, "failed": 0},
        }

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)

    async def populate_recipes(self):
        """Populate recipe embeddings"""
        logger.info("Processing recipe embeddings...")

        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get recipes without embeddings
        cursor.execute(
            """
            SELECT recipe_id, recipe_name, cuisine_type, recipe_data
            FROM recipes
            WHERE embedding IS NULL
            ORDER BY recipe_id
        """
        )
        recipes = cursor.fetchall()

        self.stats["recipes"]["total"] = len(recipes)
        logger.info(f"Found {len(recipes)} recipes without embeddings")

        for i, recipe in enumerate(recipes):
            try:
                # Build text for embedding
                text_parts = [f"Recipe: {recipe['recipe_name']}"]

                if recipe.get("cuisine_type"):
                    text_parts.append(f"Cuisine: {recipe['cuisine_type']}")

                # Extract from recipe_data
                if recipe.get("recipe_data"):
                    try:
                        data = json.loads(recipe["recipe_data"])
                        if data.get("description"):
                            text_parts.append(f"Description: {data['description']}")
                        if data.get("ingredients"):
                            text_parts.append(f"Ingredients: {', '.join(data['ingredients'])}")
                    except:
                        pass

                full_text = " | ".join(text_parts)

                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(full_text)

                # Update database
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                cursor.execute(
                    """
                    UPDATE recipes
                    SET embedding = %s::vector,
                        embedding_updated_at = CURRENT_TIMESTAMP
                    WHERE recipe_id = %s
                """,
                    (embedding_str, recipe["recipe_id"]),
                )
                conn.commit()

                self.stats["recipes"]["processed"] += 1
                logger.info(f"Processed recipe {i+1}/{len(recipes)}: {recipe['recipe_name']}")

            except Exception as e:
                logger.error(f"Failed recipe {recipe['recipe_id']}: {e}")
                self.stats["recipes"]["failed"] += 1
                conn.rollback()

        cursor.close()
        conn.close()

    async def populate_products(self):
        """Populate product embeddings"""
        logger.info("Processing product embeddings...")

        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get products without embeddings
        cursor.execute(
            """
            SELECT product_id, product_name, brand_name, category
            FROM products
            WHERE embedding IS NULL
            ORDER BY product_id
        """
        )
        products = cursor.fetchall()

        self.stats["products"]["total"] = len(products)
        logger.info(f"Found {len(products)} products without embeddings")

        for i, product in enumerate(products):
            try:
                # Build text for embedding
                text_parts = [f"Product: {product['product_name']}"]

                if product.get("brand_name"):
                    text_parts.append(f"Brand: {product['brand_name']}")
                if product.get("category"):
                    text_parts.append(f"Category: {product['category']}")

                full_text = " | ".join(text_parts)

                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(full_text)

                # Update database
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                cursor.execute(
                    """
                    UPDATE products
                    SET embedding = %s::vector,
                        embedding_updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = %s
                """,
                    (embedding_str, product["product_id"]),
                )
                conn.commit()

                self.stats["products"]["processed"] += 1
                logger.info(f"Processed product {i+1}/{len(products)}: {product['product_name']}")

            except Exception as e:
                logger.error(f"Failed product {product['product_id']}: {e}")
                self.stats["products"]["failed"] += 1
                conn.rollback()

        cursor.close()
        conn.close()

    async def populate_pantry_items(self):
        """Populate pantry item embeddings"""
        logger.info("Processing pantry item embeddings...")

        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get pantry items without embeddings
        cursor.execute(
            """
            SELECT
                pi.id,
                pi.item_name,
                pi.category,
                pi.location,
                p.name as product_name,
                p.brand as product_brand
            FROM pantry_items pi
            LEFT JOIN products p ON pi.product_id = p.id
            WHERE pi.embedding IS NULL
            ORDER BY pi.id
            LIMIT 100
        """
        )  # Process in smaller batches
        items = cursor.fetchall()

        self.stats["pantry_items"]["total"] = len(items)
        logger.info(f"Processing first {len(items)} pantry items without embeddings")

        for i, item in enumerate(items):
            try:
                # Build text for embedding
                text_parts = [f"Item: {item['item_name']}"]

                if item.get("category"):
                    text_parts.append(f"Category: {item['category']}")
                if item.get("location"):
                    text_parts.append(f"Location: {item['location']}")
                if item.get("product_name"):
                    text_parts.append(f"Product: {item['product_name']}")
                if item.get("product_brand"):
                    text_parts.append(f"Brand: {item['product_brand']}")

                full_text = " | ".join(text_parts)

                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(full_text)

                # Update database
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                cursor.execute(
                    """
                    UPDATE pantry_items
                    SET embedding = %s::vector,
                        embedding_updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """,
                    (embedding_str, item["id"]),
                )
                conn.commit()

                self.stats["pantry_items"]["processed"] += 1
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i+1}/{len(items)} pantry items")

            except Exception as e:
                logger.error(f"Failed pantry item {item['id']}: {e}")
                self.stats["pantry_items"]["failed"] += 1
                conn.rollback()

        cursor.close()
        conn.close()

    async def run(self, entity_type: str = "all"):
        """Run the population process"""
        start_time = datetime.now()

        try:
            if entity_type in ["all", "recipes"]:
                await self.populate_recipes()

            if entity_type in ["all", "products"]:
                await self.populate_products()

            if entity_type in ["all", "pantry"]:
                await self.populate_pantry_items()

            # Report results
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"\nEmbedding population completed in {duration:.2f} seconds")
            logger.info("Summary:")
            for entity, stats in self.stats.items():
                if stats["total"] > 0:
                    logger.info(
                        f"  {entity}: {stats['processed']}/{stats['total']} processed, {stats['failed']} failed"
                    )

        finally:
            await self.embedding_service.close()


async def main():
    """Main function"""
    import sys

    entity_type = sys.argv[1] if len(sys.argv) > 1 else "all"

    if entity_type not in ["all", "recipes", "products", "pantry"]:
        print("Usage: python populate_embeddings_standalone.py [all|recipes|products|pantry]")
        sys.exit(1)

    populator = EmbeddingPopulator()
    await populator.run(entity_type)


if __name__ == "__main__":
    asyncio.run(main())
