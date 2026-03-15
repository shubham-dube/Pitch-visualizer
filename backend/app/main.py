"""
FastAPI application factory.

Wires together:
  - CORS middleware
  - Static file serving for generated images
  - In-memory store (shared across all requests)
  - All API routers
  - Error handlers
  - Startup/shutdown lifecycle events
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import exports, panels, projects, styles
from app.config import get_settings
from app.store.memory_store import InMemoryStore
from app.utils.errors import PitchVisualizerError
from app.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)

_START_TIME = time.monotonic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)

    # Ensure storage directory exists
    storage = Path(settings.storage_path)
    storage.mkdir(parents=True, exist_ok=True)

    # Initialise in-memory store
    app.state.store = InMemoryStore()

    logger.info(
        "Pitch Visualizer API started",
        version=settings.app_version,
        environment=settings.environment,
        storage_path=str(storage.resolve()),
    )

    yield

    logger.info("Pitch Visualizer API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static image serving ──────────────────────────────────────
    storage_path = Path(settings.storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.static_url_prefix,
        StaticFiles(directory=str(storage_path), html=False),
        name="images",
    )

    # ── Routers ───────────────────────────────────────────────────
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(panels.router,   prefix="/api/v1")
    app.include_router(exports.router,  prefix="/api/v1")
    app.include_router(styles.router,   prefix="/api/v1")

    # ── Error Handlers ────────────────────────────────────────────
    @app.exception_handler(PitchVisualizerError)
    async def app_error_handler(request: Request, exc: PitchVisualizerError):
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": exc.code,
                "message": exc.message,
                "detail": exc.detail,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "detail": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # ── Health check ──────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health(request: Request):
        store: InMemoryStore = request.app.state.store
        count = await store.count()
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "project_count": count,
            "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        }

    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": "Pitch Visualizer API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# ── Entry point ───────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,      # debug / auto reload
        log_level="debug"
    )