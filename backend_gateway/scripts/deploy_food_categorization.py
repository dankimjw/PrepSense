"""
Deployment script for the food categorization system
Handles database setup, API key configuration, and incremental rollout
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend_gateway directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from backend_gateway.services.food_database_service import FoodDatabaseService
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.unit_validation_service import UnitValidationService

logger = logging.getLogger(__name__)


class FoodCategorizationDeployer:
    """Handles deployment of the food categorization system"""

    def __init__(self):
        self.db_service = PostgresService()

    def run_deployment(self, mode="incremental"):
        """
        Run the deployment process

        Args:
            mode: 'incremental' for gradual rollout, 'full' for complete deployment
        """
        print("🚀 Starting Food Categorization System Deployment")

        try:
            # Step 1: Database setup
            print("\n📁 Step 1: Setting up database schema...")
            self.setup_database()

            # Step 2: API configuration check
            print("\n🔑 Step 2: Checking API configurations...")
            self.check_api_configuration()

            # Step 3: Initialize cache with common items
            print("\n💾 Step 3: Initializing food cache...")
            asyncio.run(self.initialize_food_cache())

            # Step 4: Test the system
            print("\n🧪 Step 4: Running system tests...")
            asyncio.run(self.run_tests())

            # Step 5: Create migration strategy
            if mode == "incremental":
                print("\n📈 Step 5: Setting up incremental rollout...")
                self.setup_incremental_rollout()
            else:
                print("\n🔄 Step 5: Setting up full migration...")
                self.setup_full_migration()

            print("\n✅ Deployment completed successfully!")
            self.print_next_steps()

        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")
            logger.error(f"Deployment error: {str(e)}")
            raise

    def setup_database(self):
        """Set up the database schema"""
        schema_file = Path(__file__).parent / "create_food_categorization_tables.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        # Execute the schema creation
        try:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

            for statement in statements:
                if statement:
                    self.db_service.execute_query(statement)

            print("   ✓ Database schema created successfully")

        except Exception as e:
            print(f"   ❌ Database setup failed: {str(e)}")
            raise

    def check_api_configuration(self):
        """Check API key configuration"""
        api_configs = {
            "SPOONACULAR_API_KEY": "Spoonacular",
            "USDA_API_KEY": "USDA FoodData Central",
            "OPENAI_API_KEY": "OpenAI (for enhanced parsing)",
        }

        configured_apis = []

        for env_var, api_name in api_configs.items():
            if os.getenv(env_var):
                configured_apis.append(api_name)
                print(f"   ✓ {api_name} API key configured")
            else:
                print(f"   ⚠️  {api_name} API key not found (optional)")

        if not configured_apis:
            print("   ⚠️  No API keys configured - system will use pattern matching only")
        else:
            print(f"   ✓ {len(configured_apis)} API(s) configured")

    async def initialize_food_cache(self):
        """Initialize the cache with common food items"""
        food_service = FoodDatabaseService(self.db_service)

        # Common food items to pre-populate
        common_items = [
            # Produce
            ("apple", None),
            ("banana", None),
            ("orange", None),
            ("spinach", None),
            ("lettuce", None),
            ("tomato", None),
            # Dairy
            ("milk", None),
            ("cheese", None),
            ("yogurt", None),
            ("butter", None),
            ("eggs", None),
            # Meat & Seafood
            ("chicken breast", None),
            ("ground beef", None),
            ("salmon", None),
            # Pantry staples
            ("bread", None),
            ("rice", None),
            ("pasta", None),
            ("flour", None),
            ("sugar", None),
            ("olive oil", None),
            # Snacks
            ("cereal bar", None),
            ("protein bar", None),
            ("crackers", None),
            # Branded items
            ("Trader Joe's Cereal Bars", "Trader Joe's"),
            ("Great Value Milk", "Great Value"),
            ("Kirkland Chicken", "Kirkland"),
        ]

        cached_count = 0
        errors = []

        for item_name, brand in common_items:
            try:
                result = await food_service.categorize_food_item(item_name, brand)
                if result:
                    cached_count += 1
                    print(f"   ✓ Cached: {item_name} -> {result['category']}")
            except Exception as e:
                errors.append(f"{item_name}: {str(e)}")
                print(f"   ❌ Failed to cache: {item_name}")

        print(f"\n   📊 Cache initialization: {cached_count} items cached")
        if errors:
            print(f"   ⚠️  {len(errors)} errors occurred")

    async def run_tests(self):
        """Run basic system tests"""
        food_service = FoodDatabaseService(self.db_service)
        unit_service = UnitValidationService(self.db_service)

        test_cases = [
            # Test the main edge case
            ("Trader Joe's Cereal Bars", "liter"),
            # Test common items
            ("apple", "each"),
            ("milk", "cup"),
            ("chicken", "pound"),
        ]

        passed = 0
        failed = 0

        for item_name, unit in test_cases:
            try:
                # Test categorization
                cat_result = await food_service.categorize_food_item(item_name)

                # Test unit validation
                unit_result = await unit_service.validate_unit(item_name, unit)

                if cat_result and unit_result:
                    passed += 1
                    print(f"   ✓ Test passed: {item_name} -> {cat_result['category']}")
                else:
                    failed += 1
                    print(f"   ❌ Test failed: {item_name}")

            except Exception as e:
                failed += 1
                print(f"   ❌ Test error: {item_name} - {str(e)}")

        print(f"\n   📊 Test results: {passed} passed, {failed} failed")

        if failed > 0:
            print("   ⚠️  Some tests failed - check logs for details")

    def setup_incremental_rollout(self):
        """Set up incremental rollout strategy"""
        print("   📋 Incremental rollout plan:")
        print("      Phase 1: Enable for new items only (recommended)")
        print("      Phase 2: Migrate existing uncategorized items")
        print("      Phase 3: Full validation of all items")
        print("      Phase 4: Enable user corrections learning")

        # Create a feature flag table
        try:
            feature_flag_sql = """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_name VARCHAR(100) PRIMARY KEY,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    rollout_percentage INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                INSERT INTO feature_flags (flag_name, is_enabled, rollout_percentage, description)
                VALUES 
                    ('food_categorization_new_items', TRUE, 100, 'Enable categorization for new pantry items'),
                    ('food_categorization_existing', FALSE, 0, 'Migrate existing pantry items'),
                    ('unit_validation', FALSE, 10, 'Enable unit validation with 10% rollout'),
                    ('user_corrections', FALSE, 0, 'Enable user correction learning')
                ON CONFLICT (flag_name) DO NOTHING;
            """

            self.db_service.execute_query(feature_flag_sql)
            print("   ✓ Feature flags configured for incremental rollout")

        except Exception as e:
            print(f"   ❌ Feature flag setup failed: {str(e)}")

    def setup_full_migration(self):
        """Set up full migration strategy"""
        print("   📋 Full migration plan:")
        print("      ⚠️  This will enable all features immediately")
        print("      - All new items will be categorized")
        print("      - All existing items will be validated")
        print("      - Unit validation will be enabled")
        print("      - User corrections will be tracked")

        try:
            feature_flag_sql = """
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_name VARCHAR(100) PRIMARY KEY,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    rollout_percentage INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                INSERT INTO feature_flags (flag_name, is_enabled, rollout_percentage, description)
                VALUES 
                    ('food_categorization_new_items', TRUE, 100, 'Enable categorization for new pantry items'),
                    ('food_categorization_existing', TRUE, 100, 'Migrate existing pantry items'),
                    ('unit_validation', TRUE, 100, 'Enable unit validation'),
                    ('user_corrections', TRUE, 100, 'Enable user correction learning')
                ON CONFLICT (flag_name) DO NOTHING;
            """

            self.db_service.execute_query(feature_flag_sql)
            print("   ✓ All features enabled for full deployment")

        except Exception as e:
            print(f"   ❌ Full migration setup failed: {str(e)}")

    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n🎯 Next Steps:")
        print("\n1. API Integration:")
        print("   - Add your Spoonacular API key to environment variables")
        print("   - Optionally add USDA API key for better nutrition data")
        print("   - Set up monitoring for API rate limits")

        print("\n2. Router Integration:")
        print("   - Add the food categorization router to your main app:")
        print("   ```python")
        print("   from backend_gateway.routers import food_categorization_router")
        print("   app.include_router(food_categorization_router.router)")
        print("   ```")

        print("\n3. Frontend Integration:")
        print("   - Update pantry item forms to use new categorization endpoint")
        print("   - Add unit validation to prevent user errors")
        print("   - Implement user correction interface")

        print("\n4. Monitoring:")
        print("   - Monitor API usage: GET /api/food/stats/api-usage")
        print("   - Track corrections: GET /api/food/stats/corrections")
        print("   - Set up alerts for API limits")

        print("\n5. Gradual Rollout (if using incremental):")
        print("   - Phase 1: Monitor new item categorization")
        print("   - Phase 2: Enable existing item migration")
        print("   - Phase 3: Enable unit validation")
        print("   - Phase 4: Enable user learning system")


def main():
    """Main deployment function"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy Food Categorization System")
    parser.add_argument(
        "--mode",
        choices=["incremental", "full"],
        default="incremental",
        help="Deployment mode (default: incremental)",
    )
    parser.add_argument(
        "--test-only", action="store_true", help="Run tests only without deployment"
    )

    args = parser.parse_args()

    deployer = FoodCategorizationDeployer()

    if args.test_only:
        print("🧪 Running tests only...")
        asyncio.run(deployer.run_tests())
    else:
        deployer.run_deployment(args.mode)


if __name__ == "__main__":
    main()
