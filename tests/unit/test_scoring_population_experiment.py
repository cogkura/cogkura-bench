"""Scope of population independence in the existing IDF-off option."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cogkura.algorithms.activation import _scaled_idf_weights, _text_match_metrics
from cogkura.models import ActivationConfig, RetrievalCue


def test_idf_off_stabilizes_text_scores_not_default_idf() -> None:
    cue = RetrievalCue(text="migration strategy")
    before = [
        SimpleNamespace(text="migration deployment"),
        SimpleNamespace(text="strategy archive"),
    ]
    after = [*before, SimpleNamespace(text="strategy service")]
    dynamic = ActivationConfig(enable_candidate_idf=True)
    stable = ActivationConfig(enable_candidate_idf=False)

    def score(candidates, config):
        weights = _scaled_idf_weights(candidates, cue, config)
        return _text_match_metrics(
            cue.text, before[0].text, idf_weights=weights, precision_enabled=True
        )

    assert score(before, dynamic) != score(after, dynamic)
    assert score(before, stable) == score(after, stable)


def _boundary_module():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "scripts" / "experiment_temporal_scoring.py"
    spec = importlib.util.spec_from_file_location("experiment_temporal_scoring", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_tenant_and_valid_time_boundaries_for_both_scoring_modes(tmp_path) -> None:
    module = _boundary_module()
    for backend in ("memory", "sqlite"):
        for idf in (True, False):
            result = await module.execute(backend, idf, tmp_path / f"{backend}-{idf}.db", None)
            assert result["initial"]["status"] == "ok"
            assert result["initial"] == result["foreign_tenant"]
            assert result["initial"] == result["future_with_valid_at"]


def test_experiment_comparison_rejects_different_candidate() -> None:
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "scripts" / "compare_scoring_experiments.py"
    spec = importlib.util.spec_from_file_location("compare_scoring_experiments", path)
    assert spec and spec.loader
    # The command-line script imports its neighboring helper from the script directory.
    import sys

    sys.path.insert(0, str(path.parent))
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    left = {
        "policy": "default",
        "core_distribution": {"commit": "a"},
        "python": "3.12",
        "seed": 183,
        "hash_seed": 0,
        "runs": {},
    }
    right = {**left, "policy": "idf-off", "core_distribution": {"commit": "b"}}
    with pytest.raises(ValueError, match="exact candidate"):
        module.compare(left, right)


def test_backend_review_rejects_tampered_query_details() -> None:
    import gzip
    import importlib.util
    import json
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "compare_scoring_experiment_backends.py"
    spec = importlib.util.spec_from_file_location("compare_scoring_experiment_backends", path)
    assert spec and spec.loader
    sys.path.insert(0, str(path.parent))
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    report_path = root / "docs" / "findings" / "data" / "scoring-0201-idf-off-backends.json.gz"
    report = json.loads(gzip.decompress(report_path.read_bytes()))
    result = module.compare(report)
    assert result["comparison_passed"] and not result["approved"]
    assert len(result["support_order_only"]) == 9
    details = report["cases"]["mini"]["sqlite"]["query_details"]
    details[next(iter(details))]["unexpected_test_field"] = True
    with pytest.raises(ValueError, match="do not match hashes"):
        module.compare(report)
