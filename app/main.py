#!/usr/bin/env python3
"""FastAPI Code Summarizer Web API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import Settings
from .core.exceptions import setup_exception_handlers

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    # Startup
    print("Starting Code Summarizer API...")

    yield

    # Shutdown
    print("Shutting down Code Summarizer API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = Settings()

    app = FastAPI(
        title="Code Summarizer API",
        description="AI-powered code analysis and summarization tool",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    from .api.routes.analyze import router as analyze_router
    from .api.routes.health import router as health_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(analyze_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Code Summarizer API",
            "version": "1.0.0",
            "docs_url": "/docs",
        }

    return app


# Create the FastAPI application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
