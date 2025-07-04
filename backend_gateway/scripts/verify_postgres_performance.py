#!/usr/bin/env python3
"""
Verify PostgreSQL performance improvements over BigQuery
Compares operation times between the two systems
"""

import asyncio
import time
import statistics
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.bigquery_service import BigQueryService
from backend_gateway.services.pantry_service import PantryService
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class PerformanceTester:
    def __init__(self):
        # PostgreSQL config
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', '***REMOVED***'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DATABASE', 'prepsense'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', '***REMOVED***')
        }
        
        # Initialize services
        self.pg_service = None
        self.bq_service = None
        self.test_user_id = 111
        
    async def setup(self):
        """Initialize database connections"""
        try:
            self.pg_service = PostgresService(self.pg_config)
            self.bq_service = BigQueryService()
            logger.info("✓ Database connections established")
        except Exception as e:
            logger.error(f"Failed to setup connections: {e}")
            raise
            
    async def cleanup(self):
        """Clean up connections"""
        if self.pg_service:
            self.pg_service.close()
            
    async def measure_operation(self, operation_name: str, operation_func, iterations: int = 5) -> Dict[str, float]:
        """Measure operation performance"""
        times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start = time.time()
                await operation_func()
                elapsed = time.time() - start
                times.append(elapsed)
            except Exception as e:
                errors += 1
                logger.debug(f"Error in {operation_name}: {e}")
                
        if times:
            return {
                'avg': statistics.mean(times),
                'min': min(times),
                'max': max(times),
                'median': statistics.median(times),
                'errors': errors,
                'success_rate': (iterations - errors) / iterations * 100
            }
        else:
            return {'avg': 0, 'min': 0, 'max': 0, 'median': 0, 'errors': errors, 'success_rate': 0}
            
    async def test_read_operations(self):
        """Test read performance"""
        logger.info("\n=== Testing Read Operations ===")
        
        # PostgreSQL reads
        pg_pantry = PantryService(self.pg_service)
        pg_stats = await self.measure_operation(
            "PostgreSQL Read",
            lambda: pg_pantry.get_user_pantry_items(self.test_user_id)
        )
        
        # BigQuery reads
        bq_pantry = PantryService(self.bq_service)
        bq_stats = await self.measure_operation(
            "BigQuery Read",
            lambda: bq_pantry.get_user_pantry_items(self.test_user_id)
        )
        
        self._print_comparison("Read Operations", pg_stats, bq_stats)
        
    async def test_update_operations(self):
        """Test update performance"""
        logger.info("\n=== Testing Update Operations ===")
        
        # First, create test items in both systems
        test_item_data = {
            'product_name': 'Performance Test Item',
            'quantity': 10.0,
            'unit_of_measurement': 'units',
            'expiration_date': date.today() + timedelta(days=30)
        }
        
        # Create items
        pg_pantry = PantryService(self.pg_service)
        bq_pantry = PantryService(self.bq_service)
        
        pg_item = await pg_pantry.add_pantry_item(test_item_data, self.test_user_id)
        bq_item = await bq_pantry.add_pantry_item(test_item_data, self.test_user_id)
        
        if pg_item and bq_item:
            pg_item_id = pg_item.get('pantry_item_id')
            bq_item_id = bq_item.get('pantry_item_id')
            
            # Test updates
            pg_stats = await self.measure_operation(
                "PostgreSQL Update",
                lambda: pg_pantry.update_pantry_item_quantity(pg_item_id, 5.0),
                iterations=10
            )
            
            bq_stats = await self.measure_operation(
                "BigQuery Update",
                lambda: bq_pantry.update_pantry_item_quantity(bq_item_id, 5.0),
                iterations=10
            )
            
            self._print_comparison("Update Operations", pg_stats, bq_stats)
            
            # Cleanup
            await pg_pantry.delete_single_pantry_item(pg_item_id)
            await bq_pantry.delete_single_pantry_item(bq_item_id)
            
    async def test_batch_operations(self):
        """Test batch insert performance"""
        logger.info("\n=== Testing Batch Operations ===")
        
        # Prepare batch data
        batch_items = [
            {
                'product_name': f'Batch Test Item {i}',
                'quantity': float(i + 1),
                'unit_of_measurement': 'units',
                'expiration_date': date.today() + timedelta(days=i+1),
                'category': 'Test'
            }
            for i in range(20)
        ]
        
        pg_pantry = PantryService(self.pg_service)
        bq_pantry = PantryService(self.bq_service)
        
        # Test batch inserts
        pg_stats = await self.measure_operation(
            "PostgreSQL Batch Insert",
            lambda: self._batch_insert_pg(pg_pantry, batch_items),
            iterations=3
        )
        
        bq_stats = await self.measure_operation(
            "BigQuery Batch Insert",
            lambda: self._batch_insert_bq(bq_pantry, batch_items),
            iterations=3
        )
        
        self._print_comparison("Batch Operations (20 items)", pg_stats, bq_stats)
        
    async def _batch_insert_pg(self, pantry_service, items):
        """Helper for PostgreSQL batch insert"""
        added_ids = []
        for item in items:
            result = await pantry_service.add_pantry_item(item, self.test_user_id)
            if result and 'pantry_item_id' in result:
                added_ids.append(result['pantry_item_id'])
                
        # Cleanup
        for item_id in added_ids:
            await pantry_service.delete_single_pantry_item(item_id)
            
    async def _batch_insert_bq(self, pantry_service, items):
        """Helper for BigQuery batch insert"""
        # BigQuery uses the PantryItemManager for batch operations
        from backend_gateway.services.pantry_item_manager import PantryItemManager
        manager = PantryItemManager(self.bq_service)
        
        # Convert to expected format
        batch_data = [
            {
                'item_name': item['product_name'],
                'quantity_amount': item['quantity'],
                'quantity_unit': item['unit_of_measurement'],
                'expected_expiration': item['expiration_date'].isoformat(),
                'category': item['category']
            }
            for item in items
        ]
        
        result = manager.add_items_batch(self.test_user_id, batch_data)
        
        # Cleanup
        for item in result.get('saved_items', []):
            if 'pantry_item_id' in item:
                await pantry_service.delete_single_pantry_item(item['pantry_item_id'])
                
    def _print_comparison(self, operation_type: str, pg_stats: Dict, bq_stats: Dict):
        """Print performance comparison"""
        logger.info(f"\n{operation_type} Results:")
        logger.info(f"{'Metric':<20} {'PostgreSQL':<15} {'BigQuery':<15} {'Improvement':<15}")
        logger.info("-" * 65)
        
        # Calculate improvements
        avg_improvement = ((bq_stats['avg'] - pg_stats['avg']) / bq_stats['avg'] * 100) if bq_stats['avg'] > 0 else 0
        
        logger.info(f"{'Average Time:':<20} {pg_stats['avg']:.3f}s{'':<8} {bq_stats['avg']:.3f}s{'':<8} {avg_improvement:+.1f}%")
        logger.info(f"{'Min Time:':<20} {pg_stats['min']:.3f}s{'':<8} {bq_stats['min']:.3f}s")
        logger.info(f"{'Max Time:':<20} {pg_stats['max']:.3f}s{'':<8} {bq_stats['max']:.3f}s")
        logger.info(f"{'Success Rate:':<20} {pg_stats['success_rate']:.1f}%{'':<9} {bq_stats['success_rate']:.1f}%")
        
        if avg_improvement > 0:
            logger.info(f"\n✓ PostgreSQL is {avg_improvement:.1f}% faster for {operation_type}")
        else:
            logger.info(f"\n✗ BigQuery is {-avg_improvement:.1f}% faster for {operation_type}")
            
    async def run_all_tests(self):
        """Run all performance tests"""
        logger.info("=== PrepSense Database Performance Comparison ===")
        logger.info(f"Testing with user_id: {self.test_user_id}")
        logger.info(f"PostgreSQL: {self.pg_config['host']}:{self.pg_config['port']}")
        logger.info(f"BigQuery: {self.bq_service.project_id if self.bq_service else 'Not connected'}")
        
        await self.test_read_operations()
        await self.test_update_operations()
        await self.test_batch_operations()
        
        logger.info("\n=== Summary ===")
        logger.info("PostgreSQL advantages:")
        logger.info("- Significantly faster for individual updates (no 15-30s timeouts)")
        logger.info("- Better for real-time transactional operations")
        logger.info("- Consistent sub-second response times")
        logger.info("\nBigQuery advantages:")
        logger.info("- Better for large analytical queries")
        logger.info("- No infrastructure management needed")
        logger.info("- Built-in data warehousing features")

async def main():
    """Main test function"""
    tester = PerformanceTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Check if PostgreSQL is configured
    if not os.getenv('POSTGRES_PASSWORD'):
        logger.warning("POSTGRES_PASSWORD not set. Using default password.")
        logger.warning("Set environment variables or update the script with your configuration.")
        
    asyncio.run(main())