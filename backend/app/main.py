"""
Main FastAPI Application Entrypoint for TrustGuard AI.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    TrustGuardBaseError,
    generic_server_error_handler,
    not_found_handler,
    trustguard_exception_handler,
    validation_exception_handler,
)
from app.database.connection import check_db_health, init_database
from app.schemas.health import HealthResponse

# Setup structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trustguard")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown routines.
    """
    logger.info(
        "Starting up %s v%s in %s mode...",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    # Initialize database connection layer
    init_database()
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


def create_application() -> FastAPI:
    """
    Application factory creating and configuring the FastAPI instance.
    """
    app = FastAPI(
        title="TrustGuard AI API",
        description=(
            "AI-Powered Web Threat Detection & Digital Trust Intelligence API. "
            "Provides multi-layer URL analysis via VirusTotal, Machine Learning, "
            "SSL/TLS validation, URL heuristics, and Digital Trust Scoring."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$|^https://.*\.onrender\.com$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Server-side Maintenance Mode Enforcement Middleware
    @app.middleware("http")
    async def maintenance_mode_middleware(request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow documentation, root health, maintenance status, and admin endpoints unconditionally
        if (
            path in ("/docs", "/redoc", "/openapi.json", "/", "/health")
            or path.startswith(f"{settings.API_V1_PREFIX}/health")
            or path.startswith(f"{settings.API_V1_PREFIX}/maintenance")
            or path.startswith(f"{settings.API_V1_PREFIX}/admin")
        ):
            return await call_next(request)

        # Allow authenticated administrators through maintenance barrier
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            try:
                from app.core.admin_security import decode_admin_access_token
                decode_admin_access_token(token)
                return await call_next(request)
            except Exception:
                pass

        # Check persistent maintenance configuration
        try:
            from app.database.repositories.admin_repo import get_admin_repository
            repo = get_admin_repository()
            cfg = await repo.get_maintenance_config()
            if cfg.maintenance_enabled:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "SERVICE_UNAVAILABLE",
                        "maintenance": True,
                        "message": cfg.maintenance_message or "TrustGuard AI is temporarily undergoing scheduled maintenance.",
                        "estimated_restore_time": cfg.estimated_restore_time,
                    },
                )
        except Exception:
            pass

        return await call_next(request)

    # Register centralized exception handlers
    app.add_exception_handler(TrustGuardBaseError, trustguard_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(404, not_found_handler)
    app.add_exception_handler(Exception, generic_server_error_handler)

    # Include API v1 Router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root Level Endpoints
    @app.get(
        "/",
        summary="API Root",
        description="Root endpoint returning API overview and links to documentation.",
        tags=["General"],
    )
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "documentation": "/docs",
            "v1_base": settings.API_V1_PREFIX,
        }

    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Root Health Check",
        description="Returns system status, version, and environment information.",
        tags=["Health"],
    )
    async def root_health() -> HealthResponse:
        return HealthResponse(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            status="healthy",
            environment=settings.APP_ENV,
            database=check_db_health(),
        )

    return app


app = create_application()
