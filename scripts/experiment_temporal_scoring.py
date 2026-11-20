#!/usr/bin/env python3
"""Probe candidate weighting across tenant, factual-time and cognitive-time boundaries."""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import platform
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import cogkura
from cogkura import ActivationConfig, EmbeddedMemory, Memory, ObservationInput


async def execute(backend: str, idf: bool, path: Path, postgres_url: str | None) -> dict[str, Any]:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    before = t0 + timedelta(days=1)
    later = t0 + timedelta(days=2)
    config = ActivationConfig(retrieval_threshold=-10, enable_candidate_idf=idf)
    owner = (
        await EmbeddedMemory.open(path, activation_config=config) if backend == "sqlite" else None
    )
    engine = None
    if backend == "postgres":
        from cogkura.migrations import apply_migrations
        from cogkura.storage.postgres import (
            PostgresEpisodeStore,
            PostgresObservationStore,
            PostgresSemanticMemoryStore,
        )
        from sqlalchemy.ext.asyncio import create_async_engine

        assert postgres_url is not None
        engine = create_async_engine(postgres_url)
        await apply_migrations(engine)
        memory = Memory(
            observation_store=PostgresObservationStore(engine),
            episode_store=PostgresEpisodeStore(engine),
            semantic_store=PostgresSemanticMemoryStore(engine),
            activation_config=config,
        )
        for tenant in ("a", "b"):
            await memory.clear(tenant_id=tenant)
    else:
        memory = owner.memory if owner else Memory(activation_config=config)

    async def add(tenant: str, record: str, text: str, when: datetime) -> None:
        await memory.observe(
            ObservationInput(
                tenant_id=tenant,
                subject_id="service",
                source_namespace="scoring-boundary-experiment",
                source_record_id=record,
                content=text,
                observed_at=when,
            )
        )
        await memory.encode_episodes(tenant_id=tenant, as_of=when)

    async def query(*, valid_at: datetime | None) -> dict[str, Any]:
        try:
            result = await memory.recall(
                "migration strategy", tenant_id="a", as_of=before, valid_at=valid_at, limit=20
            )
            return {
                "status": "ok",
                "items": [{"text": item.memory.statement, "score": item.score} for item in result],
            }
        except Exception as exc:
            return {"status": "error", "type": type(exc).__name__, "message": str(exc)}

    try:
        await add("a", "early", "migration deployment", t0)
        initial = await query(valid_at=before)
        await add("b", "foreign", "strategy confidential", t0)
        foreign = await query(valid_at=before)
        await add("a", "future", "strategy future", later)
        future_valid = await query(valid_at=before)
        future_no_valid = await query(valid_at=None)
        return {
            "backend": backend,
            "candidate_idf": idf,
            "initial": initial,
            "foreign_tenant": foreign,
            "future_with_valid_at": future_valid,
            "future_without_valid_at": future_no_valid,
        }
    finally:
        if owner:
            await owner.close()
        if engine is not None:
            try:
                for tenant in ("a", "b"):
                    await memory.clear(tenant_id=tenant)
            finally:
                await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--postgres-url", help="disposable database; clears tenants a and b")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="scoring-boundary-") as directory:
        backends = ("memory", "sqlite", "postgres") if args.postgres_url else ("memory", "sqlite")
        cases = [
            await execute(backend, idf, Path(directory) / f"{backend}-{idf}.db", args.postgres_url)
            for backend in backends
            for idf in (True, False)
        ]
    args.output.write_text(
        json.dumps(
            {
                "core_version": importlib.metadata.version("cogkura"),
                "core_module": str(Path(cogkura.__file__).resolve()),
                "core_direct_url": json.loads(
                    importlib.metadata.distribution("cogkura").read_text("direct_url.json") or "{}"
                ),
                "python": platform.python_version(),
                "sqlite": sqlite3.sqlite_version,
                "cases": cases,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
