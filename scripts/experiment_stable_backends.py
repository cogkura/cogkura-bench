#!/usr/bin/env python3
"""Exercise the existing IDF-off configuration across storage implementations.

Diagnostic only; this does not modify the benchmark's default or approve scores.
Use a dedicated disposable PostgreSQL database: fixture tenants are cleared.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from run_embedded_freeze_validation import (
    CASES,
    TENANT_ID,
    PostgresBenchBackend,
    SQLiteBenchBackend,
    _fixture_uuid,
    execute,
)
from run_source_metamemory_validation import core_identity

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.dataset import load_dataset


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-url", required=True, help="disposable database only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use a fresh process with PYTHONHASHSEED=0")
    uuid.uuid4 = _fixture_uuid
    import cogkura

    original_init = cogkura.Memory.__init__

    def init_with_idf_off(self: Any, **kwargs: Any) -> None:
        config = kwargs.get("activation_config") or cogkura.ActivationConfig()
        kwargs["activation_config"] = replace(config, enable_candidate_idf=False)
        original_init(self, **kwargs)

    cogkura.Memory.__init__ = init_with_idf_off
    output: dict[str, Any] = {
        "diagnostic_only": True,
        "policy": "idf-off",
        "core_distribution": core_identity(cogkura),
        "cases": {},
    }
    with tempfile.TemporaryDirectory(prefix="idf-off-backends-") as folder:
        for dataset, options in CASES:
            entry: dict[str, Any] = {
                "memory": await execute(dataset, CogKuraBackend(**options), details=True)
            }
            for name, reopen in (("sqlite", False), ("sqlite_reopen", True)):
                backend = SQLiteBenchBackend(
                    Path(folder) / f"{dataset}-{name}.db", reopen=reopen, **options
                )
                entry[name] = await execute(dataset, backend, details=True)
                entry[name + "_reopen_count"] = backend.reopen_count
            tenants = {event.tenant_id or TENANT_ID for event in load_dataset(dataset).events}
            entry["postgres"] = await execute(
                dataset, PostgresBenchBackend(args.postgres_url, tenants, **options), details=True
            )
            output["cases"][dataset] = entry
            print(dataset, flush=True)
        options = next(options for dataset, options in CASES if dataset == "mini")
        tenants = {event.tenant_id or TENANT_ID for event in load_dataset("mini").events}
        output["cases"]["mini"]["postgres_repeat"] = await execute(
            "mini", PostgresBenchBackend(args.postgres_url, tenants, **options), details=True
        )
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
