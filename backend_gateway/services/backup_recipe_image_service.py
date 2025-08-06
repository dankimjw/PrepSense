"""
Image serving service for backup recipe images.
Handles static file serving, optimization, and fallback logic.

🟡 PARTIAL - Image service implementation (requires FastAPI integration)
"""

import asyncio
import hashlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

# Configuration
IMAGES_BASE_DIR = "/Users/danielkim/_Capstone/PrepSense/Food Data/kaggle-recipes-with-images/Food Images/Food Images"
CACHE_DIR = "/tmp/prepsense_image_cache"
DEFAULT_IMAGE = "default-recipe.jpg"  # Fallback image name

# Supported image formats
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = (800, 600)  # Max dimensions for optimization
CACHE_QUALITY = 85  # JPEG quality for cached images


class BackupRecipeImageService:
    """Service for managing backup recipe images."""

    def __init__(self):
        self.images_dir = Path(IMAGES_BASE_DIR)
        self.cache_dir = Path(CACHE_DIR)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Verify images directory exists
        if not self.images_dir.exists():
            logger.error(f"Images directory not found: {self.images_dir}")

    def get_image_path(self, image_name: Optional[str]) -> Optional[Path]:
        """Get the full path to an image file."""
        if not image_name:
            return None

        # Clean the image name
        clean_name = self._clean_image_name(image_name)
        if not clean_name:
            return None

        image_path = self.images_dir / clean_name

        # Check if file exists
        if image_path.exists() and image_path.is_file():
            return image_path

        logger.warning(f"Image not found: {image_path}")
        return None

    def _clean_image_name(self, image_name: str) -> Optional[str]:
        """Clean and validate image name."""
        if not image_name:
            return None

        # Remove any path traversal attempts
        clean_name = os.path.basename(image_name)

        # Check file extension
        if not any(clean_name.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
            logger.warning(f"Unsupported image format: {clean_name}")
            return None

        return clean_name

    async def get_optimized_image_path(self, image_name: Optional[str]) -> Optional[Path]:
        """Get optimized version of image, creating cache if needed."""
        if not image_name:
            return None

        original_path = self.get_image_path(image_name)
        if not original_path:
            return None

        # Generate cache key
        cache_key = self._generate_cache_key(image_name)
        cached_path = self.cache_dir / f"{cache_key}.jpg"

        # Return cached version if exists and is newer than original
        if cached_path.exists() and cached_path.stat().st_mtime > original_path.stat().st_mtime:
            return cached_path

        # Create optimized version asynchronously
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor, self._create_optimized_image, original_path, cached_path
            )
            return cached_path
        except Exception as e:
            logger.error(f"Failed to optimize image {image_name}: {e}")
            return original_path  # Return original if optimization fails

    def _generate_cache_key(self, image_name: str) -> str:
        """Generate a cache key for an image."""
        return hashlib.md5(image_name.encode()).hexdigest()

    def _create_optimized_image(self, source_path: Path, target_path: Path) -> None:
        """Create an optimized version of the image."""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Resize if too large
                if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                    img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

                # Save optimized version
                img.save(target_path, "JPEG", quality=CACHE_QUALITY, optimize=True)

        except Exception as e:
            logger.error(f"Error optimizing image {source_path}: {e}")
            raise

    def get_image_metadata(self, image_name: Optional[str]) -> dict:
        """Get metadata about an image."""
        if not image_name:
            return {"exists": False, "error": "No image name provided"}

        image_path = self.get_image_path(image_name)
        if not image_path:
            return {"exists": False, "error": "Image not found"}

        try:
            stat = image_path.stat()

            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format

            return {
                "exists": True,
                "file_path": str(image_path),
                "file_size": stat.st_size,
                "width": width,
                "height": height,
                "format": format_name,
                "modified_time": stat.st_mtime,
            }
        except Exception as e:
            return {"exists": False, "error": f"Error reading image: {str(e)}"}

    def list_available_images(self, limit: int = 100) -> list:
        """List available images in the directory."""
        try:
            images = []
            for image_path in self.images_dir.iterdir():
                if image_path.is_file() and any(
                    image_path.name.lower().endswith(ext) for ext in SUPPORTED_FORMATS
                ):
                    images.append({"name": image_path.name, "size": image_path.stat().st_size})

                    if len(images) >= limit:
                        break

            return sorted(images, key=lambda x: x["name"])
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []

    def cleanup_cache(self, max_age_days: int = 7) -> int:
        """Clean up old cached images."""
        import time

        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        cleaned_count = 0

        try:
            for cache_file in self.cache_dir.iterdir():
                if cache_file.is_file() and cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} old cached images")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
            return 0


# Global service instance
backup_image_service = BackupRecipeImageService()


# Utility functions for FastAPI integration
def get_backup_image_service() -> BackupRecipeImageService:
    """Get the backup image service instance."""
    return backup_image_service


async def serve_backup_recipe_image(
    image_name: str, optimized: bool = True
) -> Tuple[Optional[Path], dict]:
    """
    Serve a backup recipe image.

    Returns:
        Tuple of (image_path, metadata) where image_path is None if not found
    """
    service = get_backup_image_service()

    if optimized:
        image_path = await service.get_optimized_image_path(image_name)
    else:
        image_path = service.get_image_path(image_name)

    metadata = service.get_image_metadata(image_name)

    return image_path, metadata
