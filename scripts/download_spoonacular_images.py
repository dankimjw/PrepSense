#!/usr/bin/env python3
"""
Download Spoonacular recipe images to local Recipe Images folder
This ensures we have local backups for demos and faster loading
"""

import asyncio
import json
import logging
import os

# Add parent directory to path
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.config.database import db_config
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.spoonacular_service import SpoonacularService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpoonacularImageDownloader:
    def __init__(self):
        self.spoonacular_service = SpoonacularService()
        self.postgres_service = PostgresService(db_config.postgres_config)
        self.images_dir = Path("Recipe Images")
        self.images_dir.mkdir(exist_ok=True)

        # Priority recipes to download first
        self.priority_recipe_ids = [
            638071,  # Chicken En Papillote
            633212,  # Baba Ganoush
            632835,  # Asian Green Pea Soup
            1512847,  # Avocado Egg Salad
            # Add more recipe IDs as needed
        ]

    def sanitize_filename(self, text: str) -> str:
        """Create safe filename from text"""
        # Remove special characters
        safe_text = "".join(c for c in text if c.isalnum() or c in " -_")
        # Replace spaces with underscores
        safe_text = safe_text.replace(" ", "_")
        # Limit length
        return safe_text[:100]

    def get_local_image_path(self, recipe_id: int, recipe_title: str) -> Path:
        """Generate local image path"""
        safe_title = self.sanitize_filename(recipe_title)
        filename = f"recipe_{recipe_id}_{safe_title}.jpg"
        return self.images_dir / filename

    async def download_image(self, url: str, save_path: Path) -> bool:
        """Download image from URL to local path"""
        try:
            # Skip if already exists
            if save_path.exists():
                logger.info(f"✅ Already exists: {save_path.name}")
                return True

            # Download image
            response = requests.get(url, timeout=30, headers={"User-Agent": "PrepSense/1.0"})
            response.raise_for_status()

            # Save to file
            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded: {save_path.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download {url}: {e}")
            return False

    async def download_recipe_image(self, recipe_id: int) -> Dict[str, Any]:
        """Download image for a single recipe"""
        try:
            # Get recipe info from Spoonacular
            recipe = await self.spoonacular_service.get_recipe_information(
                recipe_id=recipe_id, include_nutrition=False
            )

            if not recipe:
                return {"recipe_id": recipe_id, "status": "not_found"}

            recipe_title = recipe.get("title", f"Recipe {recipe_id}")
            image_url = recipe.get("image")

            if not image_url:
                logger.warning(f"No image URL for recipe {recipe_id}: {recipe_title}")
                return {"recipe_id": recipe_id, "title": recipe_title, "status": "no_image"}

            # Download and save
            local_path = self.get_local_image_path(recipe_id, recipe_title)
            success = await self.download_image(image_url, local_path)

            return {
                "recipe_id": recipe_id,
                "title": recipe_title,
                "image_url": image_url,
                "local_path": str(local_path),
                "status": "success" if success else "failed",
            }

        except Exception as e:
            logger.error(f"Error processing recipe {recipe_id}: {e}")
            return {"recipe_id": recipe_id, "status": "error", "error": str(e)}

    async def download_popular_recipes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Download images for popular recipes from pantry searches"""
        results = []

        try:
            # Get recently searched recipes from database
            query = """
                SELECT DISTINCT recipe_data->>'id' as recipe_id, 
                       recipe_data->>'title' as title,
                       recipe_data->>'image' as image_url
                FROM user_recipes 
                WHERE recipe_data IS NOT NULL 
                  AND recipe_data->>'image' IS NOT NULL
                  AND recipe_data->>'id' IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
            """

            db_recipes = self.postgres_service.execute_query(query, (limit,))

            for row in db_recipes:
                try:
                    recipe_id = int(row["recipe_id"])
                    recipe_title = row["title"]
                    image_url = row["image_url"]

                    if image_url and "spoonacular.com" in image_url:
                        local_path = self.get_local_image_path(recipe_id, recipe_title)
                        success = await self.download_image(image_url, local_path)

                        results.append(
                            {
                                "recipe_id": recipe_id,
                                "title": recipe_title,
                                "status": "success" if success else "failed",
                                "local_path": str(local_path) if success else None,
                            }
                        )
                except Exception as e:
                    logger.error(f"Error processing saved recipe: {e}")

        except Exception as e:
            logger.error(f"Error querying database: {e}")

        return results

    async def run(self):
        """Main download process"""
        print("\n🖼️  Spoonacular Image Downloader")
        print("=" * 50)

        all_results = []

        # 1. Download priority recipes first
        print(f"\n📥 Downloading {len(self.priority_recipe_ids)} priority recipes...")
        for recipe_id in self.priority_recipe_ids:
            result = await self.download_recipe_image(recipe_id)
            all_results.append(result)
            print(f"   • Recipe {recipe_id}: {result['status']}")

        # 2. Download popular/recent recipes from database
        print("\n📊 Downloading popular recipes from database...")
        popular_results = await self.download_popular_recipes(limit=30)
        all_results.extend(popular_results)
        print(
            f"   • Downloaded {len([r for r in popular_results if r['status'] == 'success'])} images"
        )

        # 3. Generate summary
        success_count = len([r for r in all_results if r.get("status") == "success"])
        failed_count = len([r for r in all_results if r.get("status") == "failed"])

        print(f"\n✅ Summary:")
        print(f"   • Total processed: {len(all_results)}")
        print(f"   • Downloaded: {success_count}")
        print(f"   • Failed: {failed_count}")
        print(f"   • Images saved to: {self.images_dir.absolute()}")

        # Save manifest
        manifest_path = self.images_dir / "manifest.json"
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "total_images": success_count,
            "recipes": [r for r in all_results if r.get("status") == "success"],
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"   • Manifest saved: {manifest_path}")


async def main():
    """Run the downloader"""
    # Load environment
    from dotenv import load_dotenv

    load_dotenv()

    downloader = SpoonacularImageDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
