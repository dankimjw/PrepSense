"""Collection of API routers used by the FastAPI app."""

# Import all routers
from backend_gateway.routers.images_router import router as images_router
from backend_gateway.routers.ocr_router import router as ocr_router
from backend_gateway.routers.health_router import router as health_router
from backend_gateway.routers.admin_router import router as admin_router
from backend_gateway.routers.semantic_search_router import router as semantic_search_router

# Expose routers for use in the app
__all__ = [
    "health_router",
    "images_router",
    "ocr_router",
    "admin_router",
    "semantic_search_router",
]

