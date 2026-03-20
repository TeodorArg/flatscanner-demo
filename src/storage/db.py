"""SQLAlchemy async database engine and session helpers.

Usage::

    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    async with session_factory() as session:
        # perform queries
        ...

    # On application shutdown:
    await engine.dispose()

On first deploy (or in development), call ``create_tables(engine)`` once to
materialise all ORM-declared tables.  The function is idempotent — it uses
SQLAlchemy's ``checkfirst=True`` default, so running it against an already-
initialised schema is safe.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.storage.models import Base


def _async_database_url(database_url: str) -> str:
    """Return an asyncpg-compatible URL for the given *database_url*.

    Converts ``postgresql://`` (or ``postgres://``) to
    ``postgresql+asyncpg://`` so that the same URL format used in config and
    in standard tooling (psql, Alembic sync URLs) can be passed in without
    modification by callers.
    """
    for prefix in ("postgresql://", "postgres://"):
        if database_url.startswith(prefix):
            return "postgresql+asyncpg://" + database_url[len(prefix):]
    return database_url


def make_engine(database_url: str, **kwargs) -> AsyncEngine:
    """Create and return an ``AsyncEngine`` for *database_url*.

    Any extra *kwargs* are forwarded to ``create_async_engine`` (e.g.
    ``echo=True`` for debugging).
    """
    return create_async_engine(_async_database_url(database_url), **kwargs)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return an ``async_sessionmaker`` bound to *engine*.

    ``expire_on_commit=False`` keeps ORM objects accessible after ``commit``
    without requiring an extra SELECT, which is the correct default for async
    code where the session is typically closed immediately after commit.
    """
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(engine: AsyncEngine) -> None:
    """Create all tables declared on ``Base.metadata`` if they do not exist.

    This is a lightweight alternative to Alembic migrations for development
    and initial deploys.  The design is migration-friendly: switching to
    Alembic later requires only adding ``alembic init`` and pointing the env
    at ``Base.metadata``; this helper can then be retired.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
