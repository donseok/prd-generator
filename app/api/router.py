"""Main API router combining all endpoint routers."""

from fastapi import APIRouter

from app.api.endpoints import health, documents, processing, prd, review

api_router = APIRouter()

# Health check endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Document management endpoints
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# Processing pipeline endpoints
api_router.include_router(
    processing.router,
    prefix="/processing",
    tags=["processing"]
)

# PRD document endpoints
api_router.include_router(
    prd.router,
    prefix="/prd",
    tags=["prd"]
)

# PM review endpoints
api_router.include_router(
    review.router,
    prefix="/review",
    tags=["review"]
)
