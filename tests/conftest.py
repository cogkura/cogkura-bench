"""Optional database setup; absence remains a visible skipped parity gate."""

from __future__ import annotations

import os

import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def prepare_postgres_schema() -> None:
    url = os.environ.get("COGKURA_POSTGRES_MEMORY_URL")
    if not url:
        return
    from cogkura.migrations import apply_migrations
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url)
    try:
        await apply_migrations(engine)
    finally:
        await engine.dispose()
