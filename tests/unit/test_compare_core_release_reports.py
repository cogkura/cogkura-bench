"""Paired release comparisons must expose changes and reject mismatched runs."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_core_release_reports import compare  # noqa: E402


def _report() -> dict:
    return {
        "python": "3.11.15",
        "platform": "reference",
        "sqlite_version": "3.53.1",
        "seed": 183,
        "hash_seed": 0,
        "source_fixture": "v2",
        "bench_provenance": {"commit": "abc", "clean": True},
        "core_distribution": {"version": "0.20.2"},
        "runs": {
            "case/profile": {
                "metrics": {"recall": {"recall@10": 1.0}},
                "queries": {"q1": "abc"},
                "uses": "use-hash",
            }
        },
    }


def test_compares_query_fingerprints_metrics_uses_and_details() -> None:
    before = _report()
    after = copy.deepcopy(before)
    after["core_distribution"]["version"] = "0.20.3"
    after["runs"]["case/profile"]["queries"]["q1"] = "different"
    after["runs"]["case/profile"]["metrics"]["recall"]["recall@10"] = 0.5
    after["runs"]["case/profile"]["uses"] = "different-use"
    out = compare(before, after, {"case/profile": {"result": 1}}, {"case/profile": {"result": 2}})
    assert out["run_count"] == out["query_fingerprint_count"] == 1
    assert out["identical_run_count"] == 0
    assert out["changed_query_fingerprints"][0]["query"] == "q1"
    assert out["metric_changes"][0]["delta"] == -0.5
    assert out["changed_use_runs"] == out["changed_detail_runs"] == ["case/profile"]
    assert out["latency_included"] is False


def test_rejects_different_environment_or_bench_commit() -> None:
    before = _report()
    after = copy.deepcopy(before)
    after["platform"] = "different"
    with pytest.raises(ValueError, match="platform"):
        compare(before, after, {"case/profile": {}}, {"case/profile": {}})
    after = copy.deepcopy(before)
    after["bench_provenance"]["commit"] = "different"
    with pytest.raises(ValueError, match="Bench provenance"):
        compare(before, after, {"case/profile": {}}, {"case/profile": {}})
