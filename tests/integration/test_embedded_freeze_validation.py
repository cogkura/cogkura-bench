"""Exercise the standalone embedded comparison against its controlled mini workload."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(importlib.util.find_spec("cogkura") is None, reason="Core is not installed")
def test_embedded_validation_compares_reopened_storage(tmp_path: Path) -> None:
    import cogkura

    if not hasattr(cogkura, "EmbeddedMemory"):
        pytest.skip("embedded runtime is not available in this Core version")
    output = tmp_path / "embedded.json"
    script = Path(__file__).resolve().parents[2] / "scripts" / "run_embedded_freeze_validation.py"
    env = dict(os.environ, PYTHONHASHSEED="0")
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--allow-dirty-source",
            "--dataset",
            "mini",
            "--output",
            str(output),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(output.read_text())
    mini = report["cases"]["mini"]
    assert report["passed"] is True
    assert mini["sqlite_matches"] is True
    assert mini["sqlite_reopen_matches"] is True
    assert mini["sqlite_reopen_reopen_count"] > 0
    assert len(mini["memory"]["queries"]) == 12


@pytest.mark.skipif(importlib.util.find_spec("cogkura") is None, reason="Core is not installed")
def test_embedded_memory_survives_fresh_process(tmp_path: Path) -> None:
    """Compare persisted retrieval and reinforcement across independent interpreters."""
    program = r"""
import asyncio, json, sys
from datetime import UTC, datetime, timedelta
from cogkura import ActivationConfig, EmbeddedMemory, ObservationInput

async def main():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    async with await EmbeddedMemory.open(
        sys.argv[1], activation_config=ActivationConfig(retrieval_threshold=-10)
    ) as memory:
        if sys.argv[2] == "write":
            await memory.observe(ObservationInput(
                tenant_id="bench-restart", source_namespace="bench", source_record_id="one",
                content="Deployment service uses a database.", observed_at=now,
            ))
            await memory.process(tenant_id="bench-restart", as_of=now)
            result = await memory.recall(
                "deployment service database", tenant_id="bench-restart", as_of=now
            )
            assert result
            await memory.record_access(
                result, tenant_id="bench-restart", referenced_at=now, request_id="restart-use"
            )
        result = await memory.recall(
            "deployment service database", tenant_id="bench-restart", as_of=now + timedelta(days=1)
        )
        print(json.dumps([
            (r.memory_kind.value, r.memory.memory_key, r.memory.statement, r.score) for r in result
        ]))

asyncio.run(main())
"""
    database = str(tmp_path / "fresh-process.db")
    outputs = []
    for mode in ("write", "read"):
        completed = subprocess.run(
            [sys.executable, "-c", program, database, mode],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        outputs.append(json.loads(completed.stdout))
    assert outputs[0]
    assert outputs[0] == outputs[1]
