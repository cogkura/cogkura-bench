#!/usr/bin/env python3
"""Compare frozen Bench workloads with SQLite, including ordinary reopenings.

Run in a fresh process with PYTHONHASHSEED=0 against the exact candidate source.
No dataset, baseline, score or cognitive configuration is changed.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from run_source_metamemory_validation import (
    canonical_source,
    core_identity,
    fingerprints,
    run_signature,
)

from cogkurabench.backends.cogkura import TENANT_ID, CogKuraBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.report import result_to_dict
from cogkurabench.runner import BenchmarkRunner


class SQLiteBenchBackend(CogKuraBackend):
    """Existing adapter with the public Core storage interfaces injected."""

    def __init__(self, path: Path, *, reopen: bool, **options: Any) -> None:
        super().__init__(**options)
        self._path = path
        self._reopen = reopen
        self._sqlite: Any = None
        self.reopen_count = 0

    async def _open_stores(self) -> None:
        import cogkura
        from cogkura.storage.sqlite import (
            SQLiteCheckpointStore,
            SQLiteObservationStore,
            SQLiteStorage,
        )
        from cogkura.storage.sqlite_cognitive import (
            SQLiteActivationStore,
            SQLiteEntityRelationshipStore,
            SQLiteInhibitionStore,
            SQLiteLearningStore,
            SQLiteMemoryDynamicsStore,
        )
        from cogkura.storage.sqlite_episode import SQLiteEpisodeStore
        from cogkura.storage.sqlite_semantic import SQLiteSemanticMemoryStore

        self._sqlite = await SQLiteStorage.open(self._path)
        self._observation_store = SQLiteObservationStore(self._sqlite)
        semantic = SQLiteSemanticMemoryStore(self._sqlite)
        self._memory = cogkura.Memory(
            observation_store=self._observation_store,
            checkpoint_store=SQLiteCheckpointStore(self._sqlite),
            episode_store=SQLiteEpisodeStore(self._sqlite),
            semantic_store=semantic,
            semantic_inspection_store=semantic,
            activation_store=SQLiteActivationStore(self._sqlite),
            dynamics_store=SQLiteMemoryDynamicsStore(self._sqlite),
            learning_store=SQLiteLearningStore(self._sqlite),
            inhibition_store=SQLiteInhibitionStore(self._sqlite),
            entity_relationship_store=SQLiteEntityRelationshipStore(self._sqlite),
            **self._memory_options(),
        )

    def _memory_options(self) -> dict[str, Any]:
        import cogkura
        from cogkura.algorithms.semantic import ComplementaryLearningSemanticConsolidator
        from cogkura.models import CompetitionConfig, InhibitionConfig, SemanticCorrectionConfig

        return dict(
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                minimum_supporting_episodes=self._minimum_supporting_episodes,
                allow_authoritative_single_episode=self._allow_authoritative_single_episode,
            ),
            competition_config=CompetitionConfig(
                enabled=self._competition_enabled, apply_interference=self._apply_interference
            ),
            inhibition_config=InhibitionConfig(
                enabled=self._inhibition_enabled, apply_to_recall=self._apply_inhibition
            ),
            semantic_diagnostics_config=cogkura.SemanticDiagnosticsConfig(enabled=True)
            if self._semantic_diagnostics
            else None,
            semantic_correction_config=SemanticCorrectionConfig(enabled=self._corrections_enabled)
            if self._corrections_enabled is not None
            else None,
        )

    async def reset(self) -> None:
        await super().reset()
        await self._open_stores()

    async def prepare(self, *, as_of: Any, encode_episodes: bool = True) -> None:
        await super().prepare(as_of=as_of, encode_episodes=encode_episodes)
        if self._reopen:
            await self._sqlite.close()
            await self._open_stores()
            self.reopen_count += 1

    async def close(self) -> None:
        if self._sqlite is not None:
            await self._sqlite.close()
            self._sqlite = None
        await super().close()


class PostgresBenchBackend(SQLiteBenchBackend):
    """Inject the complete PostgreSQL bundle into the same Bench adapter."""

    def __init__(self, url: str, tenants: set[str], **options: Any) -> None:
        super().__init__(Path("unused"), reopen=False, **options)
        self._url = url
        self._fixture_tenants = tenants
        self._engine: Any = None

    async def _open_stores(self) -> None:
        import cogkura
        from cogkura.migrations import apply_migrations
        from cogkura.storage.postgres import (
            PostgresActivationStore,
            PostgresCheckpointStore,
            PostgresEntityRelationshipStore,
            PostgresEpisodeStore,
            PostgresInhibitionStore,
            PostgresLearningStore,
            PostgresMemoryDynamicsStore,
            PostgresObservationStore,
            PostgresSemanticMemoryStore,
        )
        from sqlalchemy.ext.asyncio import create_async_engine

        self._engine = create_async_engine(self._url)
        await apply_migrations(self._engine)
        self._observation_store = PostgresObservationStore(self._engine)
        semantic = PostgresSemanticMemoryStore(self._engine)
        self._memory = cogkura.Memory(
            observation_store=self._observation_store,
            checkpoint_store=PostgresCheckpointStore(self._engine),
            episode_store=PostgresEpisodeStore(self._engine),
            semantic_store=semantic,
            semantic_inspection_store=semantic,
            activation_store=PostgresActivationStore(self._engine),
            dynamics_store=PostgresMemoryDynamicsStore(self._engine),
            learning_store=PostgresLearningStore(self._engine),
            inhibition_store=PostgresInhibitionStore(self._engine),
            entity_relationship_store=PostgresEntityRelationshipStore(self._engine),
            **self._memory_options(),
        )
        for tenant in sorted(self._fixture_tenants):
            await self._memory.clear(tenant_id=tenant)

    async def close(self) -> None:
        if self._engine is not None:
            try:
                if self._memory is not None:
                    for tenant in sorted(self._fixture_tenants):
                        await self._memory.clear(tenant_id=tenant)
            finally:
                await self._engine.dispose()
                self._engine = None
        await super().close()


CASES: list[tuple[str, dict[str, Any]]] = [
    ("mini", {"name": "cogkura"}),
    (
        "authoritative_corrections_v1",
        {
            "name": "cogkura-correction",
            "minimum_supporting_episodes": 2,
            "allow_authoritative_single_episode": True,
            "corrections_enabled": True,
        },
    ),
    (
        "persistent_inhibition_v1",
        {"name": "cogkura-inhibition", "inhibition_enabled": True, "apply_inhibition": True},
    ),
    (
        "source_aware_metamemory_v1",
        {
            "name": "cogkura-source",
            "minimum_supporting_episodes": 2,
            "allow_authoritative_single_episode": True,
            "corrections_enabled": True,
            "source_assessment": True,
            "semantic_diagnostics": True,
        },
    ),
]


_RNG = random.Random(183)


def _fixture_uuid() -> uuid.UUID:
    return uuid.UUID(int=_RNG.getrandbits(128), version=4)


def seed_ids() -> None:
    _RNG.seed(183)


async def execute(
    dataset_name: str, backend: CogKuraBackend, *, details: bool = False
) -> dict[str, Any]:
    seed_ids()
    try:
        result = await BenchmarkRunner().run(
            load_dataset(dataset_name), backend, write_results=False
        )
        report = result_to_dict(result)
        logical = run_signature(report)
        signature = fingerprints(logical)
        if details:
            signature["query_details"] = logical["queries"]
            signature["observation_id_map"] = dict(backend._observation_id_to_event_id)
        signature["source_assessments"] = {
            query["query_id"]: canonical_source(query["source_assessment"])
            for query in report["query_results"]
            if query.get("source_assessment") is not None
        }
        return signature
    finally:
        await backend.close()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", choices=[name for name, _ in CASES])
    parser.add_argument("--details", action="store_true", help="retain complete query signatures")
    parser.add_argument(
        "--allow-dirty-source",
        action="store_true",
        help="allow an exploratory source run; never use it for a candidate approval",
    )
    parser.add_argument(
        "--postgres-url", help="disposable PostgreSQL database; fixture tenants are cleared"
    )
    parser.add_argument(
        "--verify-postgres-repeat",
        action="store_true",
        help="rerun mini against the same PostgreSQL database to verify cleanup",
    )
    args = parser.parse_args()
    if args.verify_postgres_repeat and (
        not args.postgres_url or args.dataset not in (None, "mini")
    ):
        parser.error("PostgreSQL repeat requires --postgres-url and the mini workload")
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use PYTHONHASHSEED=0 in a fresh process before importing Core")
    # Core imports uuid4 into individual storage modules, so install one stable
    # allocator before importing Core and reseed that same allocator per run.
    uuid.uuid4 = _fixture_uuid
    import cogkura

    module = Path(cogkura.__file__).resolve()
    identity = core_identity(cogkura)
    source_dirty = False
    source_patch_sha256 = None
    if identity["installed_module"] and identity["commit"]:
        commit = identity["commit"]
    else:
        core_root = module.parents[2]
        if module.parent != core_root / "src" / "cogkura":
            parser.error("use an exact Git-installed Core candidate or a Core source checkout")
        try:
            commit = subprocess.check_output(
                ["git", "-C", str(core_root), "rev-parse", "HEAD"], text=True
            ).strip()
            source_changes = subprocess.check_output(
                ["git", "-C", str(core_root), "status", "--porcelain", "--", "src/cogkura"],
                text=True,
            )
        except subprocess.CalledProcessError:
            parser.error("Core source checkout has no identifiable Git commit")
        if source_changes and not args.allow_dirty_source:
            parser.error("Core source has uncommitted changes; identify a clean candidate")
        if source_changes:
            source_dirty = True
            if any(line.startswith("??") for line in source_changes.splitlines()):
                parser.error("untracked Core source cannot be identified by the patch digest")
            patch = subprocess.check_output(
                ["git", "-C", str(core_root), "diff", "--binary", "HEAD", "--", "src/cogkura"]
            )
            source_patch_sha256 = hashlib.sha256(patch).hexdigest()
    output: dict[str, Any] = {
        "cases": {},
        "seed": 183,
        "hash_seed": 0,
        "core_commit": commit,
        "core_module": str(module),
        "core_version": cogkura.__version__,
        "core_distribution": identity,
        "core_source_dirty": source_dirty,
        "core_patch_sha256": source_patch_sha256,
        "python": sys.version,
        "sqlite_version": sqlite3.sqlite_version,
    }
    with tempfile.TemporaryDirectory(prefix="cogkura-bench-sqlite-") as folder:
        for dataset, options in CASES:
            if args.dataset and dataset != args.dataset:
                continue
            memory = await execute(dataset, CogKuraBackend(**options), details=args.details)
            entry: dict[str, Any] = {"memory": memory}
            for mode, reopen in (("sqlite", False), ("sqlite_reopen", True)):
                backend = SQLiteBenchBackend(
                    Path(folder) / f"{dataset}-{mode}.db", reopen=reopen, **options
                )
                entry[mode] = await execute(dataset, backend, details=args.details)
                entry[mode + "_matches"] = {
                    k: v for k, v in entry[mode].items() if k != "observation_id_map"
                } == {k: v for k, v in memory.items() if k != "observation_id_map"}
                entry[mode + "_reopen_count"] = backend.reopen_count
            if args.postgres_url:
                tenants = {event.tenant_id or TENANT_ID for event in load_dataset(dataset).events}
                backend_pg = PostgresBenchBackend(args.postgres_url, tenants, **options)
                entry["postgres"] = await execute(dataset, backend_pg, details=args.details)
                entry["postgres_matches"] = {
                    k: v for k, v in entry["postgres"].items() if k != "observation_id_map"
                } == {k: v for k, v in memory.items() if k != "observation_id_map"}
            output["cases"][dataset] = entry
            print(
                dataset,
                "sqlite=",
                entry["sqlite_matches"],
                "sqlite_reopen=",
                entry["sqlite_reopen_matches"],
                "postgres=",
                entry.get("postgres_matches", "not run"),
                flush=True,
            )
        if args.verify_postgres_repeat:
            dataset = "mini"
            options = next(config for name, config in CASES if name == dataset)
            tenants = {event.tenant_id or TENANT_ID for event in load_dataset(dataset).events}
            backend_pg = PostgresBenchBackend(args.postgres_url, tenants, **options)
            repeat = await execute(dataset, backend_pg, details=args.details)
            output["cases"][dataset]["postgres_repeat"] = repeat
            expected = output["cases"][dataset]["memory"]
            output["cases"][dataset]["postgres_repeat_matches"] = {
                k: v for k, v in repeat.items() if k != "observation_id_map"
            } == {k: v for k, v in expected.items() if k != "observation_id_map"}
            print(
                "mini postgres_repeat=",
                output["cases"][dataset]["postgres_repeat_matches"],
                flush=True,
            )
    output["passed"] = all(
        v["sqlite_matches"]
        and v["sqlite_reopen_matches"]
        and v["sqlite_reopen_reopen_count"] > 0
        and (not args.postgres_url or v["postgres_matches"])
        and v.get("postgres_repeat_matches", True)
        for v in output["cases"].values()
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
