"""
Database connection and pool management for PrepSense.
"""

import asyncpg
from typing import Optional
import logging
from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)

# Global database pool
_db_pool: Optional[asyncpg.Pool] = None


async def create_db_pool() -> asyncpg.Pool:
    """Create a database connection pool."""
    global _db_pool
    
    if _db_pool is None:
        db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
        
        _db_pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database pool created")
    
    return _db_pool


async def get_db_pool() -> asyncpg.Pool:
    """Get the database connection pool."""
    global _db_pool
    
    if _db_pool is None:
        _db_pool = await create_db_pool()
    
    return _db_pool


async def close_db_pool():
    """Close the database connection pool."""
    global _db_pool
    
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logger.info("Database pool closed")