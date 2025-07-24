"""Collection of API routers used by the FastAPI app."""

# Import all routers
from backend_gateway.routers.images_router import router as images_router
from backend_gateway.routers.ocr_router import router as ocr_router
from backend_gateway.routers.health_router import router as health_router

# Expose routers for use in the app
__all__ = [
    "health_router",
    "images_router",
    "ocr_router",
]

# Include all routers in the main app
def include_routers(app):
    # Health without prefix so it's /health (used by test scripts and probes)
    app.include_router(health_router)
    app.include_router(images_router, prefix="/v1/images")
    app.include_router(ocr_router, prefix="/v1/ocr")
    # Add any additional routers here
    # app.include_router(other_router, prefix="/v1/other")
