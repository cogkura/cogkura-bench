"""Raw fingerprint detail comparison verifies identity and preserves differences."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[2] / "scripts/compare_frozen_query_details.py"
spec = importlib.util.spec_from_file_location("compare_frozen_query_details", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_compare_checks_fingerprints_and_reports_exact_fields() -> None:
    left = {"score": 0.1, "events": ["a", "b"]}
    right = {"score": 0.2, "events": ["b", "a"]}
    gold = {"runs": {"x": {"queries": {"q": module.digest(left)}}}}
    report = {
        "unapproved_frozen_mismatches": ["x"],
        "runs": {"x": {"queries": {"q": module.digest(right)}}},
    }
    rows = module.compare(
        gold, report, {"x": {"queries": {"q": left}}}, {"x": {"queries": {"q": right}}}
    )
    assert {r["field"] for r in rows[0]["fields"]} == {".score", ".events[0]", ".events[1]"}
    report["runs"]["x"]["queries"]["q"] = "wrong"
    with pytest.raises(ValueError, match="do not match fingerprints"):
        module.compare(
            gold, report, {"x": {"queries": {"q": left}}}, {"x": {"queries": {"q": right}}}
        )
