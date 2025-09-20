"""Main FastAPI application."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .api.routes import analyze
from .api.routes import health
from .core.config import Settings
from .core.exceptions import setup_exception_handlers

settings = Settings(OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""))

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.api_title,
    description="AI-powered code analysis and summarization service",
    version=settings.api_version,
)

# Add rate limiting to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Security middleware temporarily disabled for testing

# Configure CORS with environment-based whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=settings.security.cors_allow_methods.split(","),
    allow_headers=(
        settings.security.cors_allow_headers.split(",")
        if settings.security.cors_allow_headers != "*"
        else ["*"]
    ),
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": "Code Summarizer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }
