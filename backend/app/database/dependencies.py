"""
Database dependency injection providers for FastAPI routes and services.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from app.database import connection


async def get_db_session() -> AsyncGenerator[Optional[object], None]:
    """
    Yields an active SQLAlchemy AsyncSession if configured.
    """
    if connection.AsyncSessionLocal is not None:
        async with connection.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        yield None


def get_supabase_client():
    """
    Provides access to the Supabase client instance.
    """
    return connection.supabase_client
