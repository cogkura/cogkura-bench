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
