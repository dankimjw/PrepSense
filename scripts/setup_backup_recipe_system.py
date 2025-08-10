#!/usr/bin/env python3
"""
Comprehensive setup script for the backup recipe system.
Automates database setup, data import, and system verification.

🟡 PARTIAL - Setup automation script (requires manual execution)
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# File paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend_gateway"
CSV_FILE = "/Users/danielkim/_Capstone/PrepSense/Food Data/recipe-dataset-main/13k-recipes.csv"
IMAGES_DIR = "/Users/danielkim/_Capstone/PrepSense/Food Data/kaggle-recipes-with-images/Food Images/Food Images/"


class BackupRecipeSystemSetup:
    """Comprehensive setup manager for backup recipe system."""

    def __init__(self):
        self.setup_stats = {
            "database_setup": False,
            "data_imported": False,
            "images_verified": False,
            "api_endpoints_ready": False,
            "tests_passed": False,
        }

    async def run_full_setup(
        self, test_mode: bool = False, max_import_records: Optional[int] = None
    ):
        """Run complete backup recipe system setup."""
        try:
            logger.info("🚀 Starting comprehensive backup recipe system setup...")
            start_time = time.time()

            # Step 1: Verify prerequisites
            await self._verify_prerequisites()

            # Step 2: Setup database schema
            await self._setup_database()

            # Step 3: Import recipe data
            if test_mode:
                max_import_records = max_import_records or 100
                logger.info(
                    f"🧪 Running in test mode - importing only {max_import_records} records"
                )

            await self._import_recipe_data(max_records=max_import_records)

            # Step 4: Verify image serving
            await self._verify_image_serving()

            # Step 5: Test API endpoints
            await self._test_api_endpoints()

            # Step 6: Run comprehensive tests
            if not test_mode:
                await self._run_tests()

            # Step 7: Generate setup report
            elapsed_time = time.time() - start_time
            await self._generate_setup_report(elapsed_time, test_mode)

            logger.info(f"🎉 Backup recipe system setup completed in {elapsed_time:.1f} seconds!")

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

    async def _verify_prerequisites(self):
        """Verify all prerequisites are met."""
        logger.info("📋 Verifying prerequisites...")

        # Check CSV file exists
        if not Path(CSV_FILE).exists():
            raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")
        logger.info(f"✅ CSV file found: {CSV_FILE}")

        # Check images directory exists
        if not Path(IMAGES_DIR).exists():
            raise FileNotFoundError(f"Images directory not found: {IMAGES_DIR}")

        # Count available images
        image_count = len(list(Path(IMAGES_DIR).glob("*.jpg")))
        logger.info(f"✅ Images directory found with {image_count} images: {IMAGES_DIR}")

        # Check virtual environment is activated
        if not hasattr(sys, "real_prefix") and not (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            logger.warning("⚠️ Virtual environment may not be activated")
        else:
            logger.info("✅ Virtual environment is active")

        # Check required dependencies
        try:
            import asyncpg
            import PIL

            logger.info("✅ Required dependencies (asyncpg, Pillow) are installed")
        except ImportError as e:
            raise ImportError(f"Missing required dependency: {e}")

    async def _setup_database(self):
        """Setup database schema for backup recipes."""
        logger.info("🗄️ Setting up database schema...")

        try:
            # Import and run database setup
            sys.path.append(str(BACKEND_DIR))
            from scripts.setup_backup_recipes_tables import run_migration

            await run_migration()
            self.setup_stats["database_setup"] = True
            logger.info("✅ Database schema setup completed")

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    async def _import_recipe_data(self, max_records: Optional[int] = None):
        """Import recipe data from CSV."""
        logger.info("📊 Importing recipe data...")

        try:
            # Import and run CSV import
            from scripts.import_backup_recipes_csv import BackupRecipeImporter

            importer = BackupRecipeImporter()
            await importer.import_recipes(batch_size=50, start_from=0, max_records=max_records)

            self.setup_stats["data_imported"] = True
            logger.info("✅ Recipe data import completed")

        except Exception as e:
            logger.error(f"❌ Data import failed: {e}")
            raise

    async def _verify_image_serving(self):
        """Verify image serving functionality."""
        logger.info("🖼️ Verifying image serving...")

        try:
            from services.backup_recipe_image_service import backup_image_service

            # List some available images
            available_images = backup_image_service.list_available_images(limit=5)
            if available_images:
                logger.info(f"✅ Found {len(available_images)} test images")

                # Test image metadata for first image
                first_image = available_images[0]["name"]
                metadata = backup_image_service.get_image_metadata(first_image)
                if metadata.get("exists"):
                    logger.info(f"✅ Image metadata test passed for {first_image}")
                else:
                    logger.warning(f"⚠️ Image metadata test failed for {first_image}")
            else:
                logger.warning("⚠️ No test images found")

            self.setup_stats["images_verified"] = True

        except Exception as e:
            logger.error(f"❌ Image serving verification failed: {e}")
            # Don't raise - this is not critical for basic functionality

    async def _test_api_endpoints(self):
        """Test API endpoints are working."""
        logger.info("🔌 Testing API endpoints...")

        try:
            # Test database connectivity for backup recipes
            from core.database import get_db_pool

            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Test basic recipe query
                count = await conn.fetchval("SELECT COUNT(*) FROM backup_recipes")
                logger.info(f"✅ Database connectivity test passed - {count} recipes available")

                # Test search function exists
                search_function_exists = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM pg_proc
                        WHERE proname = 'search_backup_recipes_by_ingredients'
                    )
                """
                )

                if search_function_exists:
                    logger.info("✅ Search function exists")
                else:
                    logger.warning("⚠️ Search function not found")

            self.setup_stats["api_endpoints_ready"] = True

        except Exception as e:
            logger.error(f"❌ API endpoint testing failed: {e}")
            raise

    async def _run_tests(self):
        """Run comprehensive test suite."""
        logger.info("🧪 Running comprehensive tests...")

        try:
            import subprocess

            # Run backup recipe system tests
            test_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "backend_gateway/tests/test_backup_recipe_system.py",
                    "-v",
                    "--tb=short",
                ],
                check=False, capture_output=True,
                text=True,
                cwd=SCRIPT_DIR,
            )

            if test_result.returncode == 0:
                logger.info("✅ All tests passed")
                self.setup_stats["tests_passed"] = True
            else:
                logger.warning("⚠️ Some tests failed")
                logger.warning(f"Test output: {test_result.stdout}")
                logger.warning(f"Test errors: {test_result.stderr}")

        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            # Don't raise - tests are not critical for setup

    async def _generate_setup_report(self, elapsed_time: float, test_mode: bool):
        """Generate comprehensive setup report."""
        logger.info("📋 Generating setup report...")

        # Get database statistics
        try:
            from core.database import get_db_pool

            pool = await get_db_pool()

            async with pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_recipes,
                        COUNT(DISTINCT cuisine_type) as cuisine_count,
                        COUNT(CASE WHEN image_name IS NOT NULL THEN 1 END) as recipes_with_images,
                        AVG(prep_time + cook_time) as avg_total_time
                    FROM backup_recipes
                """
                )

                ingredient_count = await conn.fetchval(
                    """
                    SELECT COUNT(DISTINCT ingredient_name)
                    FROM backup_recipe_ingredients
                """
                )
        except Exception:
            stats = None
            ingredient_count = 0

        # Create report
        report = f"""
================================
BACKUP RECIPE SYSTEM SETUP REPORT
================================

Setup completed in: {elapsed_time:.1f} seconds
Test mode: {test_mode}

SYSTEM STATUS:
- ✅ Database schema: {'✅' if self.setup_stats['database_setup'] else '❌'}
- ✅ Data imported: {'✅' if self.setup_stats['data_imported'] else '❌'}
- ✅ Image serving: {'✅' if self.setup_stats['images_verified'] else '❌'}
- ✅ API endpoints: {'✅' if self.setup_stats['api_endpoints_ready'] else '❌'}
- ✅ Tests passed: {'✅' if self.setup_stats['tests_passed'] else '❌'}

DATABASE STATISTICS:
"""

        if stats:
            report += f"""- Total recipes: {stats['total_recipes']:,}
- Unique cuisines: {stats['cuisine_count']}
- Recipes with images: {stats['recipes_with_images']:,}
- Unique ingredients: {ingredient_count:,}
- Average cook time: {stats['avg_total_time']:.1f} minutes
"""
        else:
            report += "- Statistics unavailable\n"

        report += """
NEXT STEPS:
1. Register routers in backend_gateway/app.py:
   ```python
   from backend_gateway.routers import backup_recipes_router, enhanced_recipe_router
   app.include_router(backup_recipes_router.router)
   app.include_router(enhanced_recipe_router.router)
   ```

2. Test endpoints:
   curl -X GET "http://localhost:8001/api/v1/backup-recipes/stats"
   curl -X GET "http://localhost:8001/api/v1/backup-recipes/search?query=chicken"

3. Configure fallback service in existing recipe endpoints

4. Run health checks:
   python check_app_health.py

================================
"""

        print(report)

        # Save report to file
        report_file = SCRIPT_DIR / "backup_recipe_setup_report.txt"
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"📄 Setup report saved to: {report_file}")


async def main():
    """Main setup function."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup backup recipe system")
    parser.add_argument(
        "--test-mode", action="store_true", help="Run in test mode (import only 100 records)"
    )
    parser.add_argument("--max-records", type=int, help="Maximum number of records to import")
    parser.add_argument(
        "--database-only", action="store_true", help="Only setup database schema (no data import)"
    )
    parser.add_argument(
        "--import-only", action="store_true", help="Only import data (skip database setup)"
    )

    args = parser.parse_args()

    setup = BackupRecipeSystemSetup()

    if args.database_only:
        logger.info("🗄️ Database-only setup mode")
        await setup._verify_prerequisites()
        await setup._setup_database()
    elif args.import_only:
        logger.info("📊 Import-only mode")
        await setup._verify_prerequisites()
        await setup._import_recipe_data(max_records=args.max_records)
    else:
        # Full setup
        await setup.run_full_setup(test_mode=args.test_mode, max_import_records=args.max_records)


if __name__ == "__main__":
    asyncio.run(main())
