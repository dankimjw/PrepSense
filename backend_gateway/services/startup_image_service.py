"""
Startup Image Management Service

Runs on application startup to:
- Check and refresh expiring image URLs
- Pre-generate images for popular recipes
- Download missing local backups
- Report system status
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend_gateway.services.recipe_image_manager import RecipeImageManager
from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


class StartupImageService:
    """Manages recipe images during application startup"""

    def __init__(self):
        self.image_manager = RecipeImageManager()
        self.spoonacular_service = SpoonacularService()

        # Popular recipe IDs to pre-generate (customize based on your needs)
        self.priority_recipes = [
            638071,  # Chicken En Papillote With Basil and Cherry Tomatoes
            633212,  # Baba Ganoush
            1512847,  # Avocado Egg Salad
            123456,  # Apple Delight Canadian 1962
            999999,  # Smoked Gouda and Garlic Mashed Potatoes
        ]

    async def run_startup_checks(self, max_concurrent_downloads: int = 3) -> dict[str, Any]:
        """
        Run comprehensive startup image checks

        Args:
            max_concurrent_downloads: Maximum concurrent image downloads

        Returns:
            Dictionary with startup results and statistics
        """
        print("\n🖼️  PrepSense Image Management Startup")
        print("=" * 50)

        results = {
            "start_time": datetime.now(),
            "table_setup": False,
            "url_refresh": {},
            "priority_generation": {},
            "statistics": {},
            "errors": [],
        }

        try:
            # 1. Ensure database table exists
            print("📋 Setting up recipe images table...")
            await self.image_manager.ensure_table_exists()
            results["table_setup"] = True
            print("✅ Database table ready")

            # 2. Check and refresh expiring URLs
            print("\n🔄 Checking for expiring image URLs...")
            url_stats = await self.image_manager.check_and_refresh_expiring_urls()
            results["url_refresh"] = url_stats

            if url_stats.get("total_checked", 0) > 0:
                print(f"   • Found {url_stats['total_checked']} expiring URLs")
                print(f"   • Refreshed: {url_stats.get('refreshed', 0)}")
                print(f"   • Local fallbacks: {url_stats.get('local_fallbacks', 0)}")
                print(f"   • Failed: {url_stats.get('failed', 0)}")
            else:
                print("   • No expiring URLs found")

            # 3. Pre-generate priority recipe images
            print(f"\n🎨 Pre-generating {len(self.priority_recipes)} priority recipe images...")
            generation_stats = await self._generate_priority_images(max_concurrent_downloads)
            results["priority_generation"] = generation_stats

            # 4. Get final statistics
            print("\n📊 Gathering image statistics...")
            stats = await self.image_manager.get_image_statistics()
            results["statistics"] = stats

            # Print summary
            self._print_summary(results)

        except Exception as e:
            error_msg = f"Startup image service error: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

        results["end_time"] = datetime.now()
        results["duration_seconds"] = (results["end_time"] - results["start_time"]).total_seconds()

        return results

    async def _generate_priority_images(self, max_concurrent: int) -> dict[str, Any]:
        """Generate images for priority recipes with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single_image(recipe_id: int) -> dict[str, Any]:
            async with semaphore:
                try:
                    print(f"   🔍 Processing recipe {recipe_id}...")

                    # Check if image already exists and is valid
                    existing_record = await self.image_manager.get_image_record(str(recipe_id))
                    if existing_record and existing_record.get("gcs_signed_url"):
                        expires_at = existing_record.get("url_expires_at")
                        if expires_at and expires_at > datetime.now().astimezone():
                            print(f"   ✅ Recipe {recipe_id} already has valid image")
                            return {
                                "recipe_id": recipe_id,
                                "status": "already_exists",
                                "action": "skipped",
                            }

                    # Get recipe details from Spoonacular
                    try:
                        recipe_data = self.spoonacular_service.get_recipe_information(recipe_id)
                        recipe_title = recipe_data.get("title", f"Recipe {recipe_id}")
                        ingredients = [
                            ing.get("name", "")
                            for ing in recipe_data.get("extendedIngredients", [])[:3]
                        ]
                    except Exception as e:
                        print(f"   ⚠️  Could not fetch recipe {recipe_id} from Spoonacular: {e}")
                        recipe_title = f"Recipe {recipe_id}"
                        ingredients = []

                    # Generate and store image
                    image_url = await self.image_manager.generate_and_store_recipe_image(
                        str(recipe_id), recipe_title, ingredients
                    )

                    if image_url:
                        print(f"   ✅ Generated image for recipe {recipe_id}: {recipe_title}")
                        return {
                            "recipe_id": recipe_id,
                            "status": "generated",
                            "title": recipe_title,
                            "url": image_url,
                        }
                    else:
                        print(f"   ❌ Failed to generate image for recipe {recipe_id}")
                        return {"recipe_id": recipe_id, "status": "failed", "title": recipe_title}

                except Exception as e:
                    error_msg = f"Error processing recipe {recipe_id}: {e}"
                    print(f"   ❌ {error_msg}")
                    return {"recipe_id": recipe_id, "status": "error", "error": str(e)}

        # Process all priority recipes concurrently
        tasks = [generate_single_image(recipe_id) for recipe_id in self.priority_recipes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile statistics
        stats = {
            "total_processed": len(results),
            "generated": 0,
            "already_exists": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
        }

        for result in results:
            if isinstance(result, Exception):
                stats["errors"] += 1
                stats["details"].append({"status": "exception", "error": str(result)})
            else:
                status = result.get("status")
                stats[status] = stats.get(status, 0) + 1
                stats["details"].append(result)

        return stats

    def _print_summary(self, results: dict[str, Any]):
        """Print comprehensive startup summary"""
        print("\n📈 Startup Summary")
        print("-" * 30)

        duration = results.get("duration_seconds", 0)
        print(f"⏱️  Total time: {duration:.2f} seconds")

        # URL refresh summary
        url_stats = results.get("url_refresh", {})
        if url_stats:
            print(
                f"🔄 URL Refresh: {url_stats.get('refreshed', 0)} refreshed, {url_stats.get('failed', 0)} failed"
            )

        # Generation summary
        gen_stats = results.get("priority_generation", {})
        if gen_stats:
            print(
                f"🎨 Image Generation: {gen_stats.get('generated', 0)} new, {gen_stats.get('already_exists', 0)} existing"
            )

        # Database statistics
        db_stats = results.get("statistics", {}).get("database", {})
        if db_stats:
            print(
                f"💾 Database: {db_stats.get('total_images', 0)} total, {db_stats.get('valid_urls', 0)} valid URLs"
            )

        # Local backup statistics
        local_stats = results.get("statistics", {}).get("local_directory", {})
        if local_stats:
            files_count = local_stats.get("files_count", 0)
            size_mb = local_stats.get("total_size_mb", 0)
            print(f"📁 Local Backups: {files_count} files, {size_mb:.1f} MB")

        # Errors
        errors = results.get("errors", [])
        if errors:
            print(f"❌ Errors: {len(errors)}")
            for error in errors:
                print(f"   • {error}")

        print("✅ Image management startup complete!")

    async def quick_health_check(self) -> dict[str, Any]:
        """Quick health check for image system"""
        try:
            stats = await self.image_manager.get_image_statistics()

            db_stats = stats.get("database", {})
            local_stats = stats.get("local_directory", {})

            return {
                "status": "healthy",
                "total_images": db_stats.get("total_images", 0),
                "valid_urls": db_stats.get("valid_urls", 0),
                "local_backups": local_stats.get("files_count", 0),
                "local_size_mb": round(local_stats.get("total_size_mb", 0), 1),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
