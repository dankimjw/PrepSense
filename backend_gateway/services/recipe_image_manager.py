"""
Comprehensive Recipe Image Management Service

Handles:
- Database tracking of recipe images
- Local image backup storage 
- GCS signed URL management
- Proactive image generation and caching
- Startup health checks for expiring URLs
"""

import os
import re
import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backend_gateway.core.config import settings
from backend_gateway.config.database import db_config
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.gcs_service import GCSService
from backend_gateway.services.recipe_image_service import RecipeImageService

logger = logging.getLogger(__name__)


class RecipeImageManager:
    """Manages recipe images with database tracking, GCS storage, and local backups"""
    
    def __init__(self):
        # Initialize with proper connection parameters
        self.postgres_service = PostgresService(db_config.postgres_config)
        self.gcs_service = GCSService()
        self.recipe_image_service = RecipeImageService()
        self.local_images_dir = Path("Recipe Images")
        self.local_images_dir.mkdir(exist_ok=True)
        
    def sanitize_filename(self, recipe_title: str) -> str:
        """Create a safe filename from recipe title"""
        # Remove special characters, keep alphanumeric and basic punctuation
        safe_title = re.sub(r'[^\w\s-]', '', recipe_title)
        # Replace spaces with underscores and limit length
        safe_title = safe_title.replace(' ', '_').lower()
        return safe_title[:50]  # Limit length
    
    def get_local_image_path(self, recipe_id: str, recipe_title: str) -> str:
        """Generate standardized local image path"""
        safe_title = self.sanitize_filename(recipe_title)
        filename = f"recipe_{recipe_id}_{safe_title}.png"
        return str(self.local_images_dir / filename)
    
    async def ensure_table_exists(self):
        """Create recipe_images table if it doesn't exist"""
        try:
            migration_file = Path("backend_gateway/migrations/create_recipe_images_table.sql")
            if migration_file.exists():
                with open(migration_file, 'r') as f:
                    sql = f.read()
                await self.postgres_service.execute_query(sql)
                logger.info("✅ Recipe images table ready")
            else:
                logger.warning("Migration file not found, creating table manually")
                await self._create_table_manually()
        except Exception as e:
            logger.error(f"Error creating recipe_images table: {e}")
            raise
    
    async def _create_table_manually(self):
        """Fallback table creation"""
        sql = """
        CREATE TABLE IF NOT EXISTS recipe_images (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL UNIQUE,
            recipe_title VARCHAR(500),
            gcs_signed_url TEXT,
            gcs_blob_path VARCHAR(500),
            local_file_path VARCHAR(500),
            url_expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_recipe_images_expires_at ON recipe_images(url_expires_at);
        """
        await self.postgres_service.execute_query(sql)
    
    async def get_image_record(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get image record from database"""
        try:
            sql = "SELECT * FROM recipe_images WHERE recipe_id = $1"
            result = await self.postgres_service.fetch_one(sql, int(recipe_id))
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting image record for recipe {recipe_id}: {e}")
            return None
    
    async def upsert_image_record(self, recipe_id: str, recipe_title: str, 
                                gcs_signed_url: str, gcs_blob_path: str, 
                                local_file_path: str, url_expires_at: datetime):
        """Insert or update image record in database"""
        try:
            sql = """
            INSERT INTO recipe_images (recipe_id, recipe_title, gcs_signed_url, gcs_blob_path, 
                                     local_file_path, url_expires_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (recipe_id) 
            DO UPDATE SET 
                recipe_title = EXCLUDED.recipe_title,
                gcs_signed_url = EXCLUDED.gcs_signed_url,
                gcs_blob_path = EXCLUDED.gcs_blob_path,
                local_file_path = EXCLUDED.local_file_path,
                url_expires_at = EXCLUDED.url_expires_at,
                updated_at = NOW()
            """
            await self.postgres_service.execute_query(
                sql, int(recipe_id), recipe_title, gcs_signed_url, 
                gcs_blob_path, local_file_path, url_expires_at
            )
            logger.info(f"✅ Updated database record for recipe {recipe_id}")
        except Exception as e:
            logger.error(f"Error upserting image record for recipe {recipe_id}: {e}")
    
    async def download_image_locally(self, image_url: str, local_path: str) -> bool:
        """Download image from URL to local path"""
        try:
            # Handle both signed URLs and regular URLs
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Save image
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Downloaded image to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading image to {local_path}: {e}")
            return False
    
    async def get_recipe_image_url(self, recipe_id: str, recipe_title: str = None, 
                                  spoonacular_image_url: str = None, 
                                  use_dalle: bool = False) -> Optional[str]:
        """
        Get recipe image URL with full fallback hierarchy:
        1. Valid GCS signed URL from database
        2. Regenerate signed URL from existing GCS blob  
        3. Local backup image
        4. Download Spoonacular image (if provided)
        5. Generate new DALL-E image (only if use_dalle=True, for chat recipes)
        """
        try:
            # Check database first
            record = await self.get_image_record(recipe_id)
            
            if record:
                # Check if signed URL is still valid (not expiring in next 24 hours)
                expires_at = record.get('url_expires_at')
                if expires_at and expires_at > datetime.now(timezone.utc) + timedelta(hours=24):
                    logger.info(f"✅ Using cached signed URL for recipe {recipe_id}")
                    return record['gcs_signed_url']
                
                # Try to regenerate signed URL from existing blob
                if record.get('gcs_blob_path'):
                    logger.info(f"🔄 Regenerating signed URL for recipe {recipe_id}")
                    new_signed_url = await self._regenerate_signed_url(record['gcs_blob_path'])
                    if new_signed_url:
                        # Update database with new URL
                        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                        await self.upsert_image_record(
                            recipe_id, record['recipe_title'], new_signed_url,
                            record['gcs_blob_path'], record['local_file_path'], expires_at
                        )
                        return new_signed_url
                
                # Check for local backup
                local_path = record.get('local_file_path')
                if local_path and os.path.exists(local_path):
                    logger.info(f"📁 Using local backup for recipe {recipe_id}")
                    return f"file://{os.path.abspath(local_path)}"
            
            # Try Spoonacular image if provided
            if spoonacular_image_url:
                logger.info(f"📥 Downloading Spoonacular image for recipe {recipe_id}")
                return await self.download_and_store_spoonacular_image(
                    recipe_id, recipe_title or f"Recipe {recipe_id}", spoonacular_image_url
                )
            
            # Only use DALL-E for chat-generated recipes
            if use_dalle:
                logger.info(f"🎨 Generating DALL-E image for chat recipe {recipe_id}")
                return await self.generate_and_store_recipe_image(recipe_id, recipe_title)
            
            # No image available
            logger.warning(f"No image available for recipe {recipe_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting recipe image URL for {recipe_id}: {e}")
            return None
    
    async def download_and_store_spoonacular_image(self, recipe_id: str, recipe_title: str, 
                                                  spoonacular_url: str) -> Optional[str]:
        """Download Spoonacular image and store in GCS with local backup"""
        try:
            # Download image from Spoonacular
            response = requests.get(spoonacular_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # Generate filename
            filename = self.gcs_service.generate_image_filename(recipe_id, recipe_title)
            
            # Upload to GCS
            blob = self.gcs_service.bucket.blob(filename)
            blob.upload_from_string(image_data, content_type='image/jpeg')
            
            # Generate signed URL
            from datetime import datetime, timezone, timedelta
            expiration_date = datetime.now(timezone.utc) + timedelta(days=7)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=expiration_date,
                method="GET"
            )
            
            # Save local backup
            local_path = self.get_local_image_path(recipe_id, recipe_title)
            await self.download_image_locally(spoonacular_url, local_path)
            
            # Update database
            await self.upsert_image_record(
                recipe_id, recipe_title, signed_url,
                filename, local_path, expiration_date
            )
            
            logger.info(f"✅ Downloaded and stored Spoonacular image for recipe {recipe_id}")
            return signed_url
            
        except Exception as e:
            logger.error(f"Error downloading Spoonacular image for recipe {recipe_id}: {e}")
            # Return original Spoonacular URL as fallback
            return spoonacular_url
    
    async def _regenerate_signed_url(self, gcs_blob_path: str) -> Optional[str]:
        """Regenerate signed URL from existing GCS blob"""
        try:
            blob = self.gcs_service.bucket.blob(gcs_blob_path)
            if blob.exists():
                expiration_date = datetime.now(timezone.utc) + timedelta(days=7)
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration_date,
                    method="GET"
                )
                return signed_url
            return None
        except Exception as e:
            logger.error(f"Error regenerating signed URL for {gcs_blob_path}: {e}")
            return None
    
    async def generate_and_store_recipe_image(self, recipe_id: str, recipe_title: str = None,
                                            ingredients: list = None, cuisine: str = None) -> Optional[str]:
        """Generate new recipe image and store with full tracking"""
        try:
            # Use the existing service to generate and upload
            gcs_signed_url = await self.recipe_image_service.generate_and_store_recipe_image(
                recipe_id, recipe_title or f"Recipe {recipe_id}", ingredients, cuisine
            )
            
            if not gcs_signed_url:
                return None
            
            # Parse GCS blob path from signed URL
            gcs_blob_path = f"Recipe_Images/{recipe_id}/{self.sanitize_filename(recipe_title or 'recipe')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Set up local storage
            local_path = self.get_local_image_path(recipe_id, recipe_title or f"Recipe {recipe_id}")
            
            # Download to local backup
            await self.download_image_locally(gcs_signed_url, local_path)
            
            # Update database
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            await self.upsert_image_record(
                recipe_id, recipe_title, gcs_signed_url, 
                gcs_blob_path, local_path, expires_at
            )
            
            return gcs_signed_url
            
        except Exception as e:
            logger.error(f"Error generating and storing recipe image for {recipe_id}: {e}")
            return None
    
    async def check_and_refresh_expiring_urls(self) -> Dict[str, int]:
        """Check for expiring URLs and refresh them"""
        try:
            # Find URLs expiring in next 24 hours
            sql = """
            SELECT recipe_id, recipe_title, gcs_blob_path, local_file_path
            FROM recipe_images 
            WHERE url_expires_at < $1 
            ORDER BY url_expires_at ASC
            """
            expiring_threshold = datetime.now(timezone.utc) + timedelta(hours=24)
            expiring_records = await self.postgres_service.fetch_all(sql, expiring_threshold)
            
            stats = {
                "total_checked": len(expiring_records),
                "refreshed": 0,
                "failed": 0,
                "local_fallbacks": 0
            }
            
            for record in expiring_records:
                recipe_id = str(record['recipe_id'])
                logger.info(f"🔄 Refreshing expiring URL for recipe {recipe_id}")
                
                # Try to regenerate signed URL
                if record['gcs_blob_path']:
                    new_signed_url = await self._regenerate_signed_url(record['gcs_blob_path'])
                    if new_signed_url:
                        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                        await self.upsert_image_record(
                            recipe_id, record['recipe_title'], new_signed_url,
                            record['gcs_blob_path'], record['local_file_path'], expires_at
                        )
                        stats["refreshed"] += 1
                        continue
                
                # Check if local backup exists
                if record['local_file_path'] and os.path.exists(record['local_file_path']):
                    logger.info(f"📁 Local backup available for recipe {recipe_id}")
                    stats["local_fallbacks"] += 1
                else:
                    stats["failed"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error checking expiring URLs: {e}")
            return {"error": str(e)}
    
    async def get_image_statistics(self) -> Dict[str, Any]:
        """Get comprehensive image statistics"""
        try:
            sql = """
            SELECT 
                COUNT(*) as total_images,
                COUNT(CASE WHEN url_expires_at > NOW() THEN 1 END) as valid_urls,
                COUNT(CASE WHEN url_expires_at <= NOW() + INTERVAL '24 hours' THEN 1 END) as expiring_soon,
                COUNT(CASE WHEN local_file_path IS NOT NULL THEN 1 END) as with_local_backup
            FROM recipe_images
            """
            result = await self.postgres_service.fetch_one(sql)
            
            # Add local directory info
            local_files = list(self.local_images_dir.glob("*.png")) if self.local_images_dir.exists() else []
            
            return {
                "database": dict(result) if result else {},
                "local_directory": {
                    "path": str(self.local_images_dir),
                    "files_count": len(local_files),
                    "total_size_mb": sum(f.stat().st_size for f in local_files) / (1024 * 1024)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting image statistics: {e}")
            return {"error": str(e)}