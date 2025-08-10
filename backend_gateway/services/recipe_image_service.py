"""
Recipe Image Service for PrepSense backup recipe system.
Handles serving, caching, and fallback for recipe images.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import FileResponse
from PIL import Image

logger = logging.getLogger(__name__)


class RecipeImageService:
    """Service for handling recipe images with optimization and fallback."""

    def __init__(self):
        self.base_image_path = Path(
            "/Users/danielkim/_Capstone/PrepSense/Food Data/kaggle-recipes-with-images/Food Images/Food Images/"
        )
        self.cache_dir = Path("/tmp/prepsense_recipe_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Supported image formats
        self.supported_formats = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

        # Default fallback image (you can create this)
        self.fallback_image_path = Path(__file__).parent.parent / "static" / "default_recipe.jpg"

        # Cache settings
        self.cache_max_age = 86400  # 24 hours
        self.enable_optimization = True

    def _get_cache_path(self, image_name: str, size: Optional[str] = None) -> Path:
        """Generate cache file path for an image."""
        cache_key = f"{image_name}_{size}" if size else image_name
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{cache_hash}_{image_name}"

    def _validate_image_name(self, image_name: str) -> str:
        """Validate and sanitize image name."""
        if not image_name:
            raise HTTPException(status_code=400, detail="Image name cannot be empty")

        # Remove any path traversal attempts
        clean_name = os.path.basename(image_name)

        # Check if extension is supported
        ext = Path(clean_name).suffix.lower()
        if ext not in self.supported_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}")

        return clean_name

    async def _optimize_image(
        self, source_path: Path, target_path: Path, max_size: tuple = (800, 600)
    ) -> bool:
        """Optimize image size and quality."""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if too large
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save with optimization
                img.save(target_path, "JPEG", quality=85, optimize=True)
                return True
        except Exception as e:
            logger.error(f"Failed to optimize image {source_path}: {e}")
            return False

    async def get_image_path(self, image_name: str, optimize: bool = True) -> Path:
        """Get the path to a recipe image, with caching and optimization."""
        clean_name = self._validate_image_name(image_name)

        # Check cache first
        cache_path = self._get_cache_path(clean_name, "optimized" if optimize else None)
        if cache_path.exists():
            return cache_path

        # Look for original image
        original_path = self.base_image_path / clean_name

        if not original_path.exists():
            # Try different extensions
            base_name = Path(clean_name).stem
            for ext in self.supported_formats:
                alt_path = self.base_image_path / f"{base_name}{ext}"
                if alt_path.exists():
                    original_path = alt_path
                    break

        if original_path.exists():
            if optimize and self.enable_optimization:
                # Create optimized version
                if await self._optimize_image(original_path, cache_path):
                    return cache_path
                else:
                    # Fall back to original if optimization fails
                    return original_path
            else:
                return original_path

        # Return fallback if available
        if self.fallback_image_path.exists():
            return self.fallback_image_path

        # No image found
        raise HTTPException(status_code=404, detail=f"Recipe image not found: {image_name}")

    async def serve_image(self, image_name: str, optimize: bool = True) -> FileResponse:
        """Serve a recipe image with appropriate headers."""
        try:
            image_path = await self.get_image_path(image_name, optimize)

            # Determine media type
            ext = image_path.suffix.lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }
            media_type = media_type_map.get(ext, "image/jpeg")

            # Return file response with caching headers
            return FileResponse(
                path=str(image_path),
                media_type=media_type,
                headers={
                    "Cache-Control": f"public, max-age={self.cache_max_age}",
                    "ETag": f'"{image_name}_{image_path.stat().st_mtime}"',
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving image {image_name}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def get_image_info(self, image_name: str) -> dict[str, Any]:
        """Get information about a recipe image."""
        try:
            image_path = await self.get_image_path(image_name, optimize=False)
            stat = image_path.stat()

            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format

            return {
                "name": image_name,
                "path": str(image_path),
                "size": stat.st_size,
                "width": width,
                "height": height,
                "format": format_name,
                "modified": stat.st_mtime,
                "cached": self._get_cache_path(image_name).exists(),
            }

        except Exception as e:
            logger.error(f"Error getting image info for {image_name}: {e}")
            raise HTTPException(status_code=404, detail="Image not found") from e

    async def clear_cache(self, image_name: Optional[str] = None) -> dict[str, Any]:
        """Clear image cache."""
        try:
            if image_name:
                # Clear specific image cache
                cache_path = self._get_cache_path(image_name)
                if cache_path.exists():
                    cache_path.unlink()
                    return {"cleared": 1, "message": f"Cache cleared for {image_name}"}
                else:
                    return {"cleared": 0, "message": f"No cache found for {image_name}"}
            else:
                # Clear all cache
                cleared = 0
                for cache_file in self.cache_dir.glob("*"):
                    if cache_file.is_file():
                        cache_file.unlink()
                        cleared += 1
                return {"cleared": cleared, "message": f"Cleared {cleared} cached images"}

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise HTTPException(status_code=500, detail="Failed to clear cache") from e

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

            return {
                "cache_dir": str(self.cache_dir),
                "cached_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
