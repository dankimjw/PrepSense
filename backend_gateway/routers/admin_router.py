"""
Admin router for database migrations and management tasks.
WARNING: This should be secured in production!
"""

import logging
from pathlib import Path
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from backend_gateway.core.database import get_db_pool

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/run-migration")
async def run_migration(
    migration_name: str, db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> dict[str, Any]:
    """
    Run a SQL migration file.

    WARNING: This endpoint should be secured in production!
    Only allow authorized administrators to run migrations.
    """

    # Validate migration name (prevent directory traversal)
    if "/" in migration_name or "\\" in migration_name or ".." in migration_name:
        raise HTTPException(status_code=400, detail="Invalid migration name")

    # Check if migration file exists
    migration_path = Path(__file__).parent.parent / "migrations" / migration_name
    if not migration_path.exists() or not migration_path.suffix == ".sql":
        raise HTTPException(status_code=404, detail=f"Migration file not found: {migration_name}")

    try:
        # Read migration file
        with open(migration_path) as f:
            sql_content = f.read()

        # Execute migration
        async with db_pool.acquire() as conn:
            # Run in a transaction
            async with conn.transaction():
                await conn.execute(sql_content)

        logger.info(f"Successfully ran migration: {migration_name}")

        return {
            "status": "success",
            "message": f"Migration {migration_name} completed successfully",
        }

    except Exception as e:
        logger.error(f"Failed to run migration {migration_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}") from e


@router.get("/check-tables")
async def check_tables(
    table_prefix: str = "usda", db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> dict[str, Any]:
    """Check if tables exist and get row counts."""

    try:
        async with db_pool.acquire() as conn:
            # Get tables matching prefix
            tables = await conn.fetch(
                """
                SELECT
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns
                     WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                AND table_name LIKE $1 || '_%'
                ORDER BY table_name
            """,
                table_prefix,
            )

            table_info = []
            for table in tables:
                # Get row count
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
                table_info.append(
                    {"name": table["table_name"], "columns": table["column_count"], "rows": count}
                )

            return {"status": "success", "tables": table_info, "total_tables": len(table_info)}

    except Exception as e:
        logger.error(f"Failed to check tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check tables: {str(e)}") from e
