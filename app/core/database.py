from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Lazily-created async engine and session factory to avoid creating DB connections at import time
_engine: Optional[AsyncEngine] = None
_async_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    pass


def get_engine() -> AsyncEngine:
    """Create and return the AsyncEngine (created once)."""
    global _engine, _async_sessionmaker
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            future=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.APP_ENV != "production",
        )
        _async_sessionmaker = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the async sessionmaker, creating the engine if necessary."""
    if _async_sessionmaker is None:
        get_engine()
    return _async_sessionmaker  # type: ignore[return-value]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an `AsyncSession`.

    Use in FastAPI endpoints as `async def endpoint(db: AsyncSession = Depends(get_db)):`
    """
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
