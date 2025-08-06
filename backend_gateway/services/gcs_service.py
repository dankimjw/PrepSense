"""Google Cloud Storage service for handling image uploads and storage"""

import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

import requests
from google.cloud import storage
from google.cloud.exceptions import NotFound

from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)


class GCSService:
    """Service for interacting with Google Cloud Storage"""

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        # Use the existing bucket
        self.bucket_name = self.project_id  # "adsp-34002-on02-prep-sense"
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy load storage client"""
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client

    @property
    def bucket(self):
        """Get the existing storage bucket"""
        if self._bucket is None:
            try:
                self._bucket = self.client.bucket(self.bucket_name)
                # Just verify it exists
                if not self._bucket.exists():
                    logger.error(f"Bucket {self.bucket_name} does not exist")
                    raise ValueError(f"Bucket {self.bucket_name} not found")
                logger.info(f"Using existing bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Error accessing bucket: {str(e)}")
                raise
        return self._bucket

    def generate_image_filename(self, recipe_id: str, recipe_title: str) -> str:
        """Generate a unique filename for recipe image"""
        # Create a clean filename from recipe title
        clean_title = "".join(
            c for c in recipe_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        clean_title = clean_title.replace(" ", "_").lower()[:50]

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Store in Recipe_Images folder as requested by user
        return f"Recipe_Images/{recipe_id}/{clean_title}_{timestamp}.png"

    async def upload_image_from_url(
        self, image_url: str, recipe_id: str, recipe_title: str
    ) -> Optional[str]:
        """
        Download image from URL and upload to GCS

        Args:
            image_url: URL of the image to download
            recipe_id: ID of the recipe
            recipe_title: Title of the recipe

        Returns:
            Public URL of the uploaded image or None if failed
        """
        try:
            # Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content

            # Generate filename
            filename = self.generate_image_filename(recipe_id, recipe_title)

            # Upload to GCS
            blob = self.bucket.blob(filename)
            blob.upload_from_string(image_data, content_type="image/png")

            # Generate signed URL for uniform bucket-level access
            # Signed URL valid for maximum allowed 7 days
            from datetime import datetime, timedelta, timezone

            expiration_date = datetime.now(timezone.utc) + timedelta(days=7)
            signed_url = blob.generate_signed_url(
                version="v4", expiration=expiration_date, method="GET"
            )
            logger.info(f"Uploaded image for recipe {recipe_id} with signed URL")

            return signed_url

        except Exception as e:
            logger.error(f"Error uploading image for recipe {recipe_id}: {str(e)}")
            return None

    def get_recipe_image_url(self, recipe_id: str) -> Optional[str]:
        """
        Get the stored image URL for a recipe if it exists

        Args:
            recipe_id: ID of the recipe

        Returns:
            Public URL of the image or None if not found
        """
        try:
            # List all blobs with the recipe_id prefix in Recipe_Images folder
            blobs = self.bucket.list_blobs(prefix=f"Recipe_Images/{recipe_id}/")

            # Get the most recent image
            latest_blob = None
            for blob in blobs:
                if latest_blob is None or blob.time_created > latest_blob.time_created:
                    latest_blob = blob

            if latest_blob:
                # Generate signed URL for uniform bucket-level access
                from datetime import datetime, timedelta, timezone

                expiration_date = datetime.now(timezone.utc) + timedelta(days=7)
                signed_url = latest_blob.generate_signed_url(
                    version="v4", expiration=expiration_date, method="GET"
                )
                return signed_url

            return None

        except Exception as e:
            logger.error(f"Error retrieving image for recipe {recipe_id}: {str(e)}")
            return None

    def delete_recipe_images(self, recipe_id: str) -> bool:
        """
        Delete all images for a recipe

        Args:
            recipe_id: ID of the recipe

        Returns:
            True if successful, False otherwise
        """
        try:
            blobs = self.bucket.list_blobs(prefix=f"Recipe_Images/{recipe_id}/")
            for blob in blobs:
                blob.delete()
                logger.info(f"Deleted image: {blob.name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting images for recipe {recipe_id}: {str(e)}")
            return False
