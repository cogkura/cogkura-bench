"""The same-runtime diagnostic preserves and checks both historical reports."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "compare_python311_history", ROOT / "scripts/compare_python311_history.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def reports():
    folder = ROOT / "docs/findings/data"
    historical = json.loads(
        (folder / "embedded-core-0.18.4-frozen-311-historical.json").read_text()
    )
    candidate = json.loads((folder / "embedded-core-0.19.5-frozen-311.json").read_text())
    return historical, candidate


def test_same_runtime_comparison_keeps_original_failed_gate() -> None:
    historical, candidate = reports()
    original = copy.deepcopy(candidate)
    result = module.compare(historical, candidate)
    assert result["same_runtime_comparison_passed"] is True
    assert result["candidate_raw_frozen_passed"] is False
    assert result["candidate_unapproved_frozen_mismatches"]
    assert candidate == original


def test_same_runtime_comparison_detects_drift_and_wrong_identity() -> None:
    historical, candidate = reports()
    candidate["runs"]["mini/cogkura"]["queries"]["injected"] = "changed"
    assert module.compare(historical, candidate)["same_runtime_mismatches"] == ["mini/cogkura"]
    candidate["core_distribution"]["commit"] = "wrong"
    with pytest.raises(ValueError, match="identity"):
        module.compare(historical, candidate)


def test_same_runtime_comparison_requires_the_exact_approved_correction() -> None:
    historical, candidate = reports()
    candidate["approved_frozen_corrections"] = []
    with pytest.raises(ValueError, match="approved correction"):
        module.compare(historical, candidate)


def test_public_release_comparison_requires_explicit_release_identity() -> None:
    historical, candidate = reports()
    candidate["core_distribution"].update(
        commit=module.RELEASE_COMMIT, version="0.19.5", distribution_version="0.19.5"
    )
    assert module.compare(historical, candidate, public_release=True)[
        "same_runtime_comparison_passed"
    ]
    with pytest.raises(ValueError, match="identity"):
        module.compare(historical, candidate)
    candidate["core_distribution"]["version"] = "0.19.6"
    with pytest.raises(ValueError, match="identity"):
        module.compare(historical, candidate, public_release=True)
