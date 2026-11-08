"""
Centralised database connection and client management for TrustGuard AI.

Follows the database architecture approved in docs/architecture/DATABASE_DESIGN.md:
- Supabase PostgreSQL is the primary database.
- Provides:
  1. Supabase Client (via supabase-py) with service-role privileges for server-side auth & tables.
  2. SQLAlchemy 2.x Async Engine and sessionmaker for direct async PostgreSQL operations / ORM.
  3. Graceful degradation: If credentials are not yet configured (e.g. initial setup),
     the application continues to run without crashing, logging status clearly.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
except ImportError:
    AsyncEngine = None  # type: ignore
    AsyncSession = None  # type: ignore
    async_sessionmaker = None  # type: ignore
    create_async_engine = None  # type: ignore

try:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
except ImportError:
    Base = object  # type: ignore

from app.core.config import settings

logger = logging.getLogger("trustguard.database")

# Global connection singletons
supabase_client = None
supabase_auth_client = None
async_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None

# PostgREST Schema Cache & Table Registry (prevents PGRST205 table-not-found errors)
_available_tables_cache: Optional[set[str]] = None
_cache_timestamp: float = 0.0
_CORE_TABLES = {"users", "scan_history", "scan_results", "community_reports", "threat_reports"}


def get_available_tables(force_refresh: bool = False) -> set[str]:
    """
    Inspects and caches the set of tables actively registered in the Supabase PostgREST schema cache.
    Guarantees that TrustGuard AI never queries an unmapped table, preventing PGRST205 errors.
    """
    global _available_tables_cache, _cache_timestamp
    import time
    now = time.time()

    if not force_refresh and _available_tables_cache is not None and (now - _cache_timestamp) < 60.0:
        return _available_tables_cache

    if not settings.supabase_configured:
        return _CORE_TABLES.copy()

    url = (settings.SUPABASE_URL or "").rstrip("/")
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not url or not key:
        return _CORE_TABLES.copy()

    try:
        import httpx
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{url}/rest/v1/", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                defs = data.get("definitions", {})
                if defs:
                    _available_tables_cache = set(defs.keys())
                    _cache_timestamp = now
                    logger.debug("Refreshed PostgREST schema cache tables: %s", _available_tables_cache)
                    return _available_tables_cache
    except Exception as e:
        logger.debug("PostgREST schema cache inspection non-critical error: %s", e)

    if _available_tables_cache is None:
        _available_tables_cache = _CORE_TABLES.copy()
    _cache_timestamp = now
    return _available_tables_cache


def is_table_available(table_name: str) -> bool:
    """
    Check if a table exists in the active Supabase PostgREST schema cache.
    """
    return table_name in get_available_tables()


def refresh_schema_cache() -> set[str]:
    """
    Explicitly force-refreshes the PostgREST schema cache table list.
    """
    return get_available_tables(force_refresh=True)


def get_supabase_service_client():
    """
    Returns the Supabase service-role client guaranteed to have administrative bypass privileges.
    Guarantees the PostgREST Authorization header is not overridden by user auth sessions.
    """
    global supabase_client
    if supabase_client is not None and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            supabase_client.postgrest.auth(settings.SUPABASE_SERVICE_ROLE_KEY)
        except Exception:
            pass
    return supabase_client


def get_postgres_async_url() -> Optional[str]:
    """
    Derives an asyncpg PostgreSQL connection string from Supabase settings if provided,
    or returns None if running without direct PostgreSQL connection string.
    """
    # If SUPABASE_URL is provided, we can construct the direct DB connection if a DB password is provided,
    # or if a custom DATABASE_URL env var exists.
    import os

    custom_db_url = os.environ.get("DATABASE_URL")
    if custom_db_url:
        if custom_db_url.startswith("postgresql://"):
            return custom_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return custom_db_url
    return None


def init_database() -> None:
    """
    Initialise the Supabase client and SQLAlchemy async engine.
    Ensures safe, graceful handling if remote credentials are not yet populated.
    """
    global supabase_client, supabase_auth_client, async_engine, AsyncSessionLocal

    # 1. Supabase Client Initialization
    if settings.supabase_configured:
        try:
            from supabase import create_client

            supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            supabase_client.postgrest.auth(settings.SUPABASE_SERVICE_ROLE_KEY)
            
            # Isolated client for user authentication operations (avoids mutating service client headers)
            supabase_auth_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY,
            )
            logger.info("Supabase Python SDK client initialized successfully.")
        except Exception as e:
            logger.warning("Could not initialize Supabase client: %s", e)
            supabase_client = None
            supabase_auth_client = None
    else:
        logger.info(
            "Supabase credentials not configured or set to placeholder. Operating in local decoupled mode."
        )

    # 2. SQLAlchemy Async Engine Initialization (if direct DB URL is provided)
    db_url = get_postgres_async_url()
    if db_url and create_async_engine is not None:
        try:
            async_engine = create_async_engine(
                db_url,
                echo=settings.APP_DEBUG,
                future=True,
                pool_pre_ping=True,
            )
            AsyncSessionLocal = async_sessionmaker(
                bind=async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info("SQLAlchemy 2.x async engine initialized.")
        except Exception as e:
            logger.warning("Could not initialize SQLAlchemy async engine: %s", e)
            async_engine = None
            AsyncSessionLocal = None


def check_db_health() -> str:
    """
    Reports database readiness status for health endpoints.
    """
    if settings.supabase_configured and supabase_client is not None:
        return "connected"
    if settings.supabase_configured and supabase_client is None:
        return "degraded"
    return "unconfigured"


async def close_database() -> None:
    """
    Disposes active database engines on application shutdown.
    """
    global async_engine
    if async_engine is not None:
        await async_engine.dispose()
        logger.info("SQLAlchemy async engine disposed.")
