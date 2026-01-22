"""FastAPI application entry point for PRD generation system."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup: Initialize services
    settings = get_settings()
    print(f"PRD Generator starting on {settings.host}:{settings.port}")
    print("Using Claude Code CLI for AI processing")

    yield

    # Shutdown: Cleanup resources
    print("PRD Generator shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="PRD 자동 생성 시스템",
        description="다양한 입력 형식을 표준 PRD로 변환하는 4단계 AI 파이프라인",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "PRD 자동 생성 시스템",
        "version": "1.0.0",
        "description": "다양한 입력 형식을 표준 PRD로 변환",
        "docs": "/docs",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
