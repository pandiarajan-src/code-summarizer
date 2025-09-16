"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import analyze, health
from .core.config import Settings
from .core.exceptions import setup_exception_handlers

settings = Settings()

app = FastAPI(
    title="Code Summarizer API",
    description="AI-powered code analysis and summarization service",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Code Summarizer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }
