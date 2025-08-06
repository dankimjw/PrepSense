"""Simple health check router for readiness/liveness probes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check", include_in_schema=False)
async def health_check():
    """Return service status for health probes."""
    return {"status": "ok"}
