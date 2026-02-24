from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Load project .env so DATABASE_URL is available to Alembic when run from the shell
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Import all models so Alembic metadata is populated
from app.models import *  # noqa: F401, F403
from app.core.database import Base

# Alembic Config object
config = context.config

# Interpret logging config from ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # Prefer explicit DATABASE_URL env; fall back to alembic.ini; finally try app settings
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        try:
            # Import settings lazily (avoid import-time DB side-effects)
            from app.core.config import settings

            url = settings.DATABASE_URL
        except Exception:
            url = None

    if url is None:
        raise RuntimeError("DATABASE_URL not set")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection required)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = create_async_engine(get_url(), future=True)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
