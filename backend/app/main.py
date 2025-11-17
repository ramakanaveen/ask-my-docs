"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")

    # Initialize services
    # TODO: Initialize vector database connection
    # TODO: Initialize Redis connection
    # TODO: Verify database connection

    yield

    # Shutdown
    print("👋 Shutting down application...")
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup resources


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic document intelligence system with Deep Agents",
    version=settings.VERSION,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS.split(","),
    allow_headers=settings.ALLOWED_HEADERS.split(",") if settings.ALLOWED_HEADERS != "*" else ["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs" if settings.ENABLE_DOCS else None,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# API v1 router (to be added)
# from app.api.v1.router import api_router
# app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred" if not settings.DEBUG else str(exc),
            "type": exc.__class__.__name__ if settings.DEBUG else None,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
