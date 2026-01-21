"""Health check endpoints."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/detail")
async def health_check_detail():
    """Detailed health check with configuration info."""
    settings = get_settings()
    return {
        "status": "healthy",
        "config": {
            "claude_model": settings.claude_model,
            "auto_approve_threshold": settings.auto_approve_threshold,
            "api_key_configured": bool(settings.anthropic_api_key),
        }
    }
