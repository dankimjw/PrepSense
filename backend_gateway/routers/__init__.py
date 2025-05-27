"""Collection of API routers used by the FastAPI app."""

# Import all routers
from backend_gateway.routers.images_router import router as images_router

# Expose routers for use in the app
__all__ = [
    "images_router",
]
# Include all routers in the main app
def include_routers(app):
    app.include_router(images_router, prefix="/v1/images")
    # Add any additional routers here
    # app.include_router(other_router, prefix="/v1/other")
