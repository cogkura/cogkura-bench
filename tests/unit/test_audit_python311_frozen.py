"""The historical audit reports differences without accepting them."""

from __future__ import annotations

import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "scripts/audit_python311_frozen.py"
spec = importlib.util.spec_from_file_location("audit_python311_frozen", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_audit_preserves_metric_and_fingerprint_differences() -> None:
    gold = {"runs": {"dataset/profile": {"metrics": {"score": 0.1}, "queries": {"q": "old"}}}}
    old = {"runs": {"dataset/profile": {"metrics": {"score": 0.2}, "queries": {"q": "new"}}}}
    current = {"runs": {"dataset/profile": {"metrics": {"score": 0.2}, "queries": {"q": "new"}}}}
    report = module.audit(gold, old, current)
    assert len(report["differences"]) == 2
    metric, query = report["differences"]
    assert metric["type"] == "numeric metric"
    assert metric["gold"] == 0.1 and metric["current"] == 0.2
    assert metric["matches_previous_core"]
    assert query["type"] == "query fingerprint" and query["gold"] == "old"
    assert query["current"] == "new" and query["explanation"] == "requires investigation"
