"""
Food Database Import Pipeline for PrepSense
Handles scheduled imports from USDA FoodData Central and Open Food Facts
"""

import os
import sys
import json
import logging
import asyncio
import aiohttp
import aiofiles
import zipfile
import csv
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import schedule
import time

# Add the backend_gateway directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.food_database_service import FoodDatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FoodDatabaseImportPipeline:
    """Handles importing and updating food data from external sources"""
    
    def __init__(self):
        self.db_service = PostgresService()
        self.food_service = FoodDatabaseService(self.db_service)
        self.import_dir = Path(__file__).parent / 'food_data_imports'
        self.import_dir.mkdir(exist_ok=True)
        
        # API endpoints
        self.usda_api_key = os.getenv('USDA_API_KEY')
        self.usda_base_url = 'https://api.nal.usda.gov/fdc/v1'
        self.off_base_url = 'https://static.openfoodfacts.org/data'
        
        # Import configurations
        self.batch_size = 100
        self.max_concurrent_requests = 5
        
    async def run_import_pipeline(self, sources: List[str] = None):
        """
        Run the import pipeline for specified sources
        
        Args:
            sources: List of sources to import from ['usda', 'openfoodfacts']
                    If None, imports from all available sources
        """
        if sources is None:
            sources = ['usda', 'openfoodfacts']
        
        logger.info(f"Starting food database import pipeline for sources: {sources}")
        
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Check API rate limits
            await self._check_rate_limits(sources)
            
            # Import from each source
            if 'usda' in sources and self.usda_api_key:
                logger.info("Importing from USDA FoodData Central...")
                usda_results = await self._import_usda_data()
                self._merge_results(results, usda_results)
            
            if 'openfoodfacts' in sources:
                logger.info("Importing from Open Food Facts...")
                off_results = await self._import_openfoodfacts_data()
                self._merge_results(results, off_results)
            
            # Update statistics
            await self._update_import_statistics(results)
            
            # Clean up old data
            await self._cleanup_old_data()
            
            logger.info(f"Import pipeline completed: {results}")
            
        except Exception as e:
            logger.error(f"Import pipeline error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    async def _check_rate_limits(self, sources: List[str]):
        """Check and update API rate limits"""
        for source in sources:
            query = """
                SELECT requests_today, daily_limit, last_reset 
                FROM api_rate_limits 
                WHERE api_name = %s
            """
            result = self.db_service.fetch_one(query, (source,))
            
            if result:
                # Reset if it's a new day
                if result['last_reset'].date() < datetime.now().date():
                    reset_query = """
                        UPDATE api_rate_limits 
                        SET requests_today = 0, last_reset = %s 
                        WHERE api_name = %s
                    """
                    self.db_service.execute_query(reset_query, (datetime.now(), source))
                
                # Check if we're near the limit
                usage_percent = (result['requests_today'] / result['daily_limit']) * 100
                if usage_percent > 90:
                    logger.warning(f"{source} API usage at {usage_percent:.1f}% of daily limit")
    
    async def _import_usda_data(self) -> Dict[str, Any]:
        """Import data from USDA FoodData Central"""
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Get list of common foods (Foundation and SR Legacy types)
            food_types = ['Foundation', 'SR Legacy']
            
            for food_type in food_types:
                logger.info(f"Importing USDA {food_type} foods...")
                
                # Search for foods by type
                search_url = f"{self.usda_base_url}/foods/list"
                params = {
                    'api_key': self.usda_api_key,
                    'dataType': food_type,
                    'pageSize': 200,
                    'pageNumber': 1
                }
                
                async with aiohttp.ClientSession() as session:
                    while True:
                        try:
                            async with session.get(search_url, params=params) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    foods = data if isinstance(data, list) else []
                                    
                                    if not foods:
                                        break
                                    
                                    # Process foods in batches
                                    for i in range(0, len(foods), self.batch_size):
                                        batch = foods[i:i + self.batch_size]
                                        batch_results = await self._process_usda_batch(batch, session)
                                        self._merge_results(results, batch_results)
                                    
                                    # Update rate limit counter
                                    await self._increment_api_counter('usda', len(foods))
                                    
                                    # Check if there are more pages
                                    if len(foods) < params['pageSize']:
                                        break
                                    
                                    params['pageNumber'] += 1
                                    
                                else:
                                    logger.error(f"USDA API error: {response.status}")
                                    results['errors'].append(f"USDA API error: {response.status}")
                                    break
                                    
                        except Exception as e:
                            logger.error(f"Error fetching USDA data: {str(e)}")
                            results['errors'].append(str(e))
                            break
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"USDA import error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    async def _process_usda_batch(self, foods: List[Dict], session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Process a batch of USDA foods"""
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for food in foods:
            try:
                # Extract food information
                food_data = {
                    'normalized_name': self._normalize_food_name(food.get('description', '')),
                    'original_name': food.get('description', ''),
                    'category': self._map_usda_food_category(food),
                    'brand': food.get('brandOwner', None),
                    'data_source': 'usda',
                    'source_id': str(food.get('fdcId', '')),
                    'metadata': {
                        'food_type': food.get('dataType', ''),
                        'food_category': food.get('foodCategory', ''),
                        'additional_descriptions': food.get('additionalDescriptions', '')
                    }
                }
                
                # Get detailed nutrition if available
                if food.get('fdcId'):
                    nutrition = await self._get_usda_nutrition(food['fdcId'], session)
                    if nutrition:
                        food_data.update(nutrition)
                
                # Save to database
                if await self._save_food_item(food_data):
                    results['success'] += 1
                else:
                    results['skipped'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing USDA food {food.get('description', 'unknown')}: {str(e)}")
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results
    
    async def _get_usda_nutrition(self, fdc_id: int, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get nutrition information for a USDA food"""
        try:
            url = f"{self.usda_base_url}/food/{fdc_id}"
            params = {'api_key': self.usda_api_key}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract key nutrients
                    nutrients = {}
                    for nutrient in data.get('foodNutrients', []):
                        nutrient_name = nutrient.get('nutrient', {}).get('name', '').lower()
                        
                        if 'energy' in nutrient_name:
                            nutrients['calories_per_100g'] = nutrient.get('amount', 0)
                        elif 'protein' in nutrient_name:
                            nutrients['protein_per_100g'] = nutrient.get('amount', 0)
                        elif 'carbohydrate' in nutrient_name and 'fiber' not in nutrient_name:
                            nutrients['carbs_per_100g'] = nutrient.get('amount', 0)
                        elif 'total lipid' in nutrient_name:
                            nutrients['fat_per_100g'] = nutrient.get('amount', 0)
                    
                    return nutrients
                    
        except Exception as e:
            logger.error(f"Error getting USDA nutrition for {fdc_id}: {str(e)}")
        
        return None
    
    async def _import_openfoodfacts_data(self) -> Dict[str, Any]:
        """Import data from Open Food Facts"""
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Download the latest export (smaller file with common products)
            export_url = f"{self.off_base_url}/en.openfoodfacts.org.products.csv.gz"
            export_file = self.import_dir / 'openfoodfacts_products.csv.gz'
            
            # Download if not exists or older than 7 days
            if not export_file.exists() or \
               datetime.fromtimestamp(export_file.stat().st_mtime) < datetime.now() - timedelta(days=7):
                logger.info("Downloading Open Food Facts export...")
                await self._download_file(export_url, export_file)
            
            # Process the CSV file
            logger.info("Processing Open Food Facts data...")
            with gzip.open(export_file, 'rt', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f, delimiter='\t')
                
                batch = []
                for row in reader:
                    # Filter for products with good data quality
                    if self._is_quality_off_product(row):
                        batch.append(row)
                        
                        if len(batch) >= self.batch_size:
                            batch_results = await self._process_off_batch(batch)
                            self._merge_results(results, batch_results)
                            batch = []
                            
                            # Limit total imports for performance
                            if results['success'] >= 10000:
                                logger.info("Reached Open Food Facts import limit")
                                break
                
                # Process remaining batch
                if batch:
                    batch_results = await self._process_off_batch(batch)
                    self._merge_results(results, batch_results)
                    
        except Exception as e:
            logger.error(f"Open Food Facts import error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    async def _process_off_batch(self, products: List[Dict]) -> Dict[str, Any]:
        """Process a batch of Open Food Facts products"""
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        for product in products:
            try:
                # Extract product information
                food_data = {
                    'normalized_name': self._normalize_food_name(product.get('product_name', '')),
                    'original_name': product.get('product_name', ''),
                    'category': self._map_off_category(product),
                    'brand': product.get('brands', None),
                    'barcode': product.get('code', None),
                    'data_source': 'openfoodfacts',
                    'source_id': product.get('code', ''),
                    'metadata': {
                        'categories': product.get('categories', ''),
                        'countries': product.get('countries', ''),
                        'ingredients': product.get('ingredients_text', '')
                    }
                }
                
                # Extract nutrition per 100g
                try:
                    if product.get('energy-kcal_100g'):
                        food_data['calories_per_100g'] = float(product['energy-kcal_100g'])
                    if product.get('proteins_100g'):
                        food_data['protein_per_100g'] = float(product['proteins_100g'])
                    if product.get('carbohydrates_100g'):
                        food_data['carbs_per_100g'] = float(product['carbohydrates_100g'])
                    if product.get('fat_100g'):
                        food_data['fat_per_100g'] = float(product['fat_100g'])
                except (ValueError, TypeError):
                    pass
                
                # Save to database
                if await self._save_food_item(food_data):
                    results['success'] += 1
                else:
                    results['skipped'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing OFF product {product.get('product_name', 'unknown')}: {str(e)}")
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results
    
    def _is_quality_off_product(self, product: Dict) -> bool:
        """Check if an Open Food Facts product has good data quality"""
        # Must have a name
        if not product.get('product_name'):
            return False
        
        # Should have some nutritional data
        has_nutrition = any(product.get(f) for f in ['energy-kcal_100g', 'proteins_100g', 'carbohydrates_100g'])
        
        # Should have categories or be a known brand
        has_category = bool(product.get('categories'))
        has_brand = bool(product.get('brands'))
        
        return has_nutrition and (has_category or has_brand)
    
    async def _save_food_item(self, food_data: Dict) -> bool:
        """Save a food item to the database"""
        try:
            # Check if item already exists
            check_query = """
                SELECT item_id, confidence_score 
                FROM food_items_cache 
                WHERE normalized_name = %s AND (brand = %s OR (brand IS NULL AND %s IS NULL))
            """
            existing = self.db_service.fetch_one(
                check_query, 
                (food_data['normalized_name'], food_data.get('brand'), food_data.get('brand'))
            )
            
            if existing:
                # Update only if new data has higher confidence
                new_confidence = self._calculate_confidence_score(food_data)
                if new_confidence > float(existing['confidence_score']):
                    update_query = """
                        UPDATE food_items_cache 
                        SET category = %s, data_source = %s, source_id = %s,
                            confidence_score = %s, metadata = %s, updated_at = CURRENT_TIMESTAMP,
                            calories_per_100g = COALESCE(%s, calories_per_100g),
                            protein_per_100g = COALESCE(%s, protein_per_100g),
                            carbs_per_100g = COALESCE(%s, carbs_per_100g),
                            fat_per_100g = COALESCE(%s, fat_per_100g)
                        WHERE item_id = %s
                    """
                    self.db_service.execute_query(update_query, (
                        food_data['category'],
                        food_data['data_source'],
                        food_data['source_id'],
                        new_confidence,
                        json.dumps(food_data.get('metadata', {})),
                        food_data.get('calories_per_100g'),
                        food_data.get('protein_per_100g'),
                        food_data.get('carbs_per_100g'),
                        food_data.get('fat_per_100g'),
                        existing['item_id']
                    ))
                    return True
                return False  # Skip - existing data is better
            
            # Insert new item
            confidence = self._calculate_confidence_score(food_data)
            
            insert_query = """
                INSERT INTO food_items_cache 
                (normalized_name, original_name, category, subcategory, brand, barcode,
                 calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g,
                 data_source, source_id, confidence_score, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING item_id
            """
            
            result = self.db_service.fetch_one(insert_query, (
                food_data['normalized_name'],
                food_data['original_name'],
                food_data['category'],
                food_data.get('subcategory'),
                food_data.get('brand'),
                food_data.get('barcode'),
                food_data.get('calories_per_100g'),
                food_data.get('protein_per_100g'),
                food_data.get('carbs_per_100g'),
                food_data.get('fat_per_100g'),
                food_data['data_source'],
                food_data['source_id'],
                confidence,
                json.dumps(food_data.get('metadata', {}))
            ))
            
            if result:
                # Add unit mappings for the item
                await self._add_unit_mappings(result['item_id'], food_data['category'])
                return True
                
        except Exception as e:
            logger.error(f"Error saving food item {food_data['normalized_name']}: {str(e)}")
        
        return False
    
    async def _add_unit_mappings(self, item_id: int, category: str):
        """Add unit mappings for a food item based on its category"""
        try:
            # Get allowed units for this category from food service
            category_info = self.food_service.category_unit_mappings.get(
                category, 
                self.food_service.category_unit_mappings['other']
            )
            
            # Insert unit mappings
            for i, unit in enumerate(category_info['allowed']):
                is_primary = (unit == category_info['default'])
                
                insert_query = """
                    INSERT INTO food_unit_mappings 
                    (item_id, unit, is_primary, confidence_score)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (item_id, unit) DO NOTHING
                """
                
                self.db_service.execute_query(insert_query, (
                    item_id, unit, is_primary, 0.8
                ))
                
        except Exception as e:
            logger.error(f"Error adding unit mappings for item {item_id}: {str(e)}")
    
    def _normalize_food_name(self, name: str) -> str:
        """Normalize food name for consistency"""
        if not name:
            return ""
        
        # Convert to lowercase and strip
        normalized = name.lower().strip()
        
        # Remove common suffixes
        suffixes = [', raw', ', cooked', ', fresh', ', frozen', ', canned', ', dried']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _map_usda_food_category(self, food: Dict) -> str:
        """Map USDA food data to our categories"""
        food_category = food.get('foodCategory', '').lower()
        description = food.get('description', '').lower()
        
        # Check specific patterns
        if any(term in description for term in ['bar', 'cereal bar', 'protein bar', 'energy bar']):
            return 'snacks_bars'
        
        # Map USDA categories
        category_mapping = {
            'dairy and egg products': 'dairy',
            'spices and herbs': 'dry_goods',
            'beef products': 'meat_seafood',
            'pork products': 'meat_seafood',
            'poultry products': 'meat_seafood',
            'finfish and shellfish': 'meat_seafood',
            'vegetables and vegetable products': 'produce_measurable',
            'fruits and fruit juices': 'produce_countable',
            'nut and seed products': 'packaged_snacks',
            'legumes and legume products': 'dry_goods',
            'cereal grains and pasta': 'dry_goods',
            'breakfast cereals': 'dry_goods',
            'baked products': 'bakery',
            'snacks': 'packaged_snacks',
            'beverages': 'liquids',
            'fats and oils': 'liquids'
        }
        
        for key, value in category_mapping.items():
            if key in food_category:
                return value
        
        return 'other'
    
    def _map_off_category(self, product: Dict) -> str:
        """Map Open Food Facts categories to our categories"""
        categories = product.get('categories', '').lower()
        product_name = product.get('product_name', '').lower()
        
        # Check for bars first
        if any(term in product_name for term in ['bar', 'cereal bar', 'protein bar', 'energy bar']):
            return 'snacks_bars'
        
        # Map OFF categories
        if 'dairy' in categories or 'milk' in categories or 'cheese' in categories:
            return 'dairy'
        elif 'meat' in categories or 'fish' in categories or 'seafood' in categories:
            return 'meat_seafood'
        elif 'fruits' in categories or 'fresh fruits' in categories:
            return 'produce_countable'
        elif 'vegetables' in categories or 'fresh vegetables' in categories:
            return 'produce_measurable'
        elif 'beverages' in categories or 'drinks' in categories:
            return 'liquids'
        elif 'cereals' in categories or 'pasta' in categories or 'rice' in categories:
            return 'dry_goods'
        elif 'breads' in categories or 'bakery' in categories:
            return 'bakery'
        elif 'snacks' in categories or 'chips' in categories:
            return 'packaged_snacks'
        
        return 'other'
    
    def _calculate_confidence_score(self, food_data: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        score = 0.5  # Base score
        
        # Boost for having nutrition data
        nutrition_fields = ['calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g']
        nutrition_count = sum(1 for field in nutrition_fields if food_data.get(field) is not None)
        score += nutrition_count * 0.1
        
        # Boost for having brand
        if food_data.get('brand'):
            score += 0.1
        
        # Boost for having barcode
        if food_data.get('barcode'):
            score += 0.05
        
        # Source-specific boosts
        if food_data['data_source'] == 'usda':
            score += 0.15  # USDA is authoritative
        elif food_data['data_source'] == 'user_verified':
            score = 0.95  # User verified is highest
        
        return min(score, 1.0)
    
    async def _download_file(self, url: str, destination: Path):
        """Download a file with progress tracking"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                async with aiofiles.open(destination, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"Download progress: {progress:.1f}%")
    
    async def _increment_api_counter(self, api_name: str, count: int = 1):
        """Increment API request counter"""
        query = """
            UPDATE api_rate_limits 
            SET requests_today = requests_today + %s 
            WHERE api_name = %s
        """
        self.db_service.execute_query(query, (count, api_name))
    
    async def _update_import_statistics(self, results: Dict):
        """Update import statistics in the database"""
        try:
            # Create statistics table if not exists
            create_table_query = """
                CREATE TABLE IF NOT EXISTS food_import_statistics (
                    import_id SERIAL PRIMARY KEY,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    items_imported INTEGER DEFAULT 0,
                    items_updated INTEGER DEFAULT 0,
                    items_failed INTEGER DEFAULT 0,
                    duration_seconds INTEGER,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """
            self.db_service.execute_query(create_table_query)
            
            # Insert statistics
            insert_query = """
                INSERT INTO food_import_statistics 
                (items_imported, items_updated, items_failed, metadata)
                VALUES (%s, %s, %s, %s)
            """
            
            metadata = {
                'errors': results.get('errors', []),
                'sources': list(results.keys())
            }
            
            self.db_service.execute_query(insert_query, (
                results['success'],
                results['skipped'],
                results['failed'],
                json.dumps(metadata)
            ))
            
        except Exception as e:
            logger.error(f"Error updating import statistics: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Clean up old or low-quality data"""
        try:
            # Remove items not accessed in 6 months with low confidence
            cleanup_query = """
                DELETE FROM food_items_cache 
                WHERE confidence_score < 0.3 
                AND last_verified_at < %s
            """
            cutoff_date = datetime.now() - timedelta(days=180)
            self.db_service.execute_query(cleanup_query, (cutoff_date,))
            
            # Remove orphaned unit mappings
            orphan_query = """
                DELETE FROM food_unit_mappings 
                WHERE item_id NOT IN (SELECT item_id FROM food_items_cache)
            """
            self.db_service.execute_query(orphan_query)
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def _merge_results(self, total: Dict, partial: Dict):
        """Merge partial results into total results"""
        total['success'] += partial.get('success', 0)
        total['failed'] += partial.get('failed', 0)
        total['skipped'] += partial.get('skipped', 0)
        total['errors'].extend(partial.get('errors', []))


class FoodDatabaseScheduler:
    """Handles scheduling of regular imports"""
    
    def __init__(self):
        self.pipeline = FoodDatabaseImportPipeline()
    
    def start_scheduler(self):
        """Start the scheduled import jobs"""
        # Schedule daily USDA import at 2 AM
        schedule.every().day.at("02:00").do(self._run_usda_import)
        
        # Schedule weekly Open Food Facts import on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self._run_off_import)
        
        # Schedule monthly full import on the 1st at 4 AM
        schedule.every().month.do(self._run_full_import)
        
        logger.info("Food database import scheduler started")
        
        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_usda_import(self):
        """Run USDA import"""
        logger.info("Running scheduled USDA import...")
        asyncio.run(self.pipeline.run_import_pipeline(['usda']))
    
    def _run_off_import(self):
        """Run Open Food Facts import"""
        logger.info("Running scheduled Open Food Facts import...")
        asyncio.run(self.pipeline.run_import_pipeline(['openfoodfacts']))
    
    def _run_full_import(self):
        """Run full import from all sources"""
        logger.info("Running scheduled full import...")
        asyncio.run(self.pipeline.run_import_pipeline())


async def main():
    """Main function for running imports"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Food Database Import Pipeline")
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['usda', 'openfoodfacts'],
        help='Sources to import from'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run as scheduled service'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run a test import with limited data'
    )
    
    args = parser.parse_args()
    
    if args.schedule:
        # Run as scheduled service
        scheduler = FoodDatabaseScheduler()
        scheduler.start_scheduler()
    else:
        # Run one-time import
        pipeline = FoodDatabaseImportPipeline()
        
        if args.test:
            # Limit batch size for testing
            pipeline.batch_size = 10
            logger.info("Running test import with limited data...")
        
        results = await pipeline.run_import_pipeline(args.sources)
        
        # Print results
        print(f"\n📊 Import Results:")
        print(f"   ✅ Imported: {results['success']} items")
        print(f"   ⏭️  Skipped: {results['skipped']} items (already up-to-date)")
        print(f"   ❌ Failed: {results['failed']} items")
        
        if results['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")


if __name__ == "__main__":
    asyncio.run(main())