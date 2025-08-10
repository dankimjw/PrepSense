"""
Script to populate embeddings for existing data in the database
This script generates embeddings for all recipes, products, and pantry items
that don't already have embeddings.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.core.config import get_settings
from backend_gateway.services.embedding_service import get_embedding_service
from backend_gateway.services.postgres_service import PostgresService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmbeddingPopulator:
    """Handles population of embeddings for existing database records"""

    def __init__(self):
        """Initialize the embedding populator"""
        settings = get_settings()

        # Initialize PostgreSQL service
        self.db_service = PostgresService(
            {
                "host": settings.db_host,
                "port": settings.db_port,
                "database": settings.db_name,
                "user": settings.db_user,
                "password": settings.db_password,
            }
        )

        # Initialize embedding service
        self.embedding_service = get_embedding_service()

        # Track progress
        self.stats = {
            "recipes": {"total": 0, "processed": 0, "failed": 0},
            "products": {"total": 0, "processed": 0, "failed": 0},
            "pantry_items": {"total": 0, "processed": 0, "failed": 0},
        }

    async def populate_all(self):
        """Populate embeddings for all entities"""
        logger.info("Starting embedding population process...")

        start_time = datetime.now()

        # Process each entity type
        await self.populate_recipe_embeddings()
        await self.populate_product_embeddings()
        await self.populate_pantry_item_embeddings()

        # Report results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"\nEmbedding population completed in {duration:.2f} seconds")
        logger.info("Summary:")
        for entity_type, stats in self.stats.items():
            logger.info(
                f"  {entity_type}: {stats['processed']}/{stats['total']} processed, {stats['failed']} failed"
            )

    async def populate_recipe_embeddings(self):
        """Populate embeddings for all recipes without embeddings"""
        logger.info("Processing recipe embeddings...")

        # Get recipes without embeddings
        with self.db_service.get_cursor() as cursor:
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

        # Process in batches
        batch_size = 10
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i : i + batch_size]
            await self._process_recipe_batch(batch)

            # Log progress
            processed = min(i + batch_size, len(recipes))
            logger.info(f"Processed {processed}/{len(recipes)} recipes")

    async def _process_recipe_batch(self, recipes: list[dict[str, Any]]):
        """Process a batch of recipes"""
        for recipe in recipes:
            try:
                # Parse recipe_data JSON if it exists
                recipe_info = {
                    "id": recipe["recipe_id"],
                    "name": recipe["recipe_name"],
                    "cuisine": recipe.get("cuisine_type"),
                    "description": "",
                    "ingredients": [],
                    "tags": [],
                }

                # Extract ingredients and description from recipe_data
                if recipe.get("recipe_data"):
                    import json

                    try:
                        data = json.loads(recipe["recipe_data"])
                        recipe_info["description"] = data.get("description", "")
                        recipe_info["ingredients"] = data.get("ingredients", [])
                        recipe_info["tags"] = data.get("tags", [])
                    except Exception:
                        pass

                # Generate embedding
                embedding = await self.embedding_service.generate_recipe_embedding(recipe_info)

                # Convert to PostgreSQL array format
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                # Update database
                with self.db_service.get_cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE recipes
                        SET embedding = %s::vector,
                            embedding_updated_at = CURRENT_TIMESTAMP
                        WHERE recipe_id = %s
                    """,
                        (embedding_str, recipe["recipe_id"]),
                    )

                self.stats["recipes"]["processed"] += 1

            except Exception as e:
                logger.error(f"Failed to generate embedding for recipe {recipe['recipe_id']}: {e}")
                self.stats["recipes"]["failed"] += 1

    async def populate_product_embeddings(self):
        """Populate embeddings for all products without embeddings"""
        logger.info("Processing product embeddings...")

        # Get products without embeddings
        with self.db_service.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, brand, category, description, barcode
                FROM products
                WHERE embedding IS NULL
                ORDER BY id
            """
            )
            products = cursor.fetchall()

        self.stats["products"]["total"] = len(products)
        logger.info(f"Found {len(products)} products without embeddings")

        # Process in batches
        batch_size = 20
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            await self._process_product_batch(batch)

            # Log progress
            processed = min(i + batch_size, len(products))
            logger.info(f"Processed {processed}/{len(products)} products")

    async def _process_product_batch(self, products: list[dict[str, Any]]):
        """Process a batch of products"""
        for product in products:
            try:
                # Generate embedding
                embedding = await self.embedding_service.generate_product_embedding(product)

                # Convert to PostgreSQL array format
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                # Update database
                with self.db_service.get_cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE products
                        SET embedding = %s::vector,
                            embedding_updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """,
                        (embedding_str, product["id"]),
                    )

                self.stats["products"]["processed"] += 1

            except Exception as e:
                logger.error(f"Failed to generate embedding for product {product['id']}: {e}")
                self.stats["products"]["failed"] += 1

    async def populate_pantry_item_embeddings(self):
        """Populate embeddings for all pantry items without embeddings"""
        logger.info("Processing pantry item embeddings...")

        # Get pantry items without embeddings
        with self.db_service.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pi.id,
                    pi.item_name,
                    pi.category,
                    pi.location,
                    p.name as product_name,
                    p.brand as product_brand,
                    p.category as product_category
                FROM pantry_items pi
                LEFT JOIN products p ON pi.product_id = p.id
                WHERE pi.embedding IS NULL
                ORDER BY pi.id
            """
            )
            items = cursor.fetchall()

        self.stats["pantry_items"]["total"] = len(items)
        logger.info(f"Found {len(items)} pantry items without embeddings")

        # Process in batches
        batch_size = 20
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            await self._process_pantry_item_batch(batch)

            # Log progress
            processed = min(i + batch_size, len(items))
            logger.info(f"Processed {processed}/{len(items)} pantry items")

    async def _process_pantry_item_batch(self, items: list[dict[str, Any]]):
        """Process a batch of pantry items"""
        for item in items:
            try:
                # Prepare item data with product info
                item_data = {
                    "id": item["id"],
                    "item_name": item["item_name"],
                    "category": item["category"],
                    "location": item["location"],
                    "product": (
                        {
                            "name": item["product_name"],
                            "brand": item["product_brand"],
                            "category": item["product_category"],
                        }
                        if item["product_name"]
                        else {}
                    ),
                }

                # Generate embedding
                embedding = await self.embedding_service.generate_pantry_item_embedding(item_data)

                # Convert to PostgreSQL array format
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                # Update database
                with self.db_service.get_cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE pantry_items
                        SET embedding = %s::vector,
                            embedding_updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """,
                        (embedding_str, item["id"]),
                    )

                self.stats["pantry_items"]["processed"] += 1

            except Exception as e:
                logger.error(f"Failed to generate embedding for pantry item {item['id']}: {e}")
                self.stats["pantry_items"]["failed"] += 1

    async def populate_specific_recipe(self, recipe_id: int):
        """Populate embedding for a specific recipe"""
        logger.info(f"Generating embedding for recipe {recipe_id}")

        success = await self.db_service.update_recipe_embedding(recipe_id)
        if success:
            logger.info(f"Successfully generated embedding for recipe {recipe_id}")
        else:
            logger.error(f"Failed to generate embedding for recipe {recipe_id}")

    async def populate_specific_product(self, product_id: int):
        """Populate embedding for a specific product"""
        logger.info(f"Generating embedding for product {product_id}")

        success = await self.db_service.update_product_embedding(product_id)
        if success:
            logger.info(f"Successfully generated embedding for product {product_id}")
        else:
            logger.error(f"Failed to generate embedding for product {product_id}")

    async def cleanup(self):
        """Clean up resources"""
        await self.embedding_service.close()


async def main():
    """Main function to run the embedding population"""
    populator = EmbeddingPopulator()

    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == "recipe" and len(sys.argv) > 2:
                # Populate specific recipe
                recipe_id = int(sys.argv[2])
                await populator.populate_specific_recipe(recipe_id)

            elif command == "product" and len(sys.argv) > 2:
                # Populate specific product
                product_id = int(sys.argv[2])
                await populator.populate_specific_product(product_id)

            elif command == "recipes":
                # Populate all recipes
                await populator.populate_recipe_embeddings()

            elif command == "products":
                # Populate all products
                await populator.populate_product_embeddings()

            elif command == "pantry":
                # Populate all pantry items
                await populator.populate_pantry_item_embeddings()

            else:
                logger.error(f"Unknown command: {command}")
                print_usage()
        else:
            # Populate all by default
            await populator.populate_all()

    except Exception as e:
        logger.error(f"Error during embedding population: {e}")
        raise
    finally:
        await populator.cleanup()


def print_usage():
    """Print usage information"""
    print(
        """
Usage:
    python populate_embeddings.py [command] [args]

Commands:
    (no command)     - Populate embeddings for all entities
    recipes          - Populate embeddings for all recipes
    products         - Populate embeddings for all products
    pantry           - Populate embeddings for all pantry items
    recipe <id>      - Populate embedding for specific recipe
    product <id>     - Populate embedding for specific product

Examples:
    python populate_embeddings.py
    python populate_embeddings.py recipes
    python populate_embeddings.py recipe 123
    """
    )


if __name__ == "__main__":
    asyncio.run(main())
