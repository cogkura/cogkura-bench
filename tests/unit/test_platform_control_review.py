"""Control comparison validates evidence and never turns diagnosis into approval."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BASE = "b30433c9577fe2493072e442b0f4ea307f342fcf"
_CANDIDATE = "7f945cdf5e5e1a8ec4854fda7acc734a959356e7"


def _module():
    path = _ROOT / "scripts" / "compare_platform_controls.py"
    spec = importlib.util.spec_from_file_location("compare_platform_controls", path)
    assert spec and spec.loader
    sys.path.insert(0, str(path.parent))
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _inputs():
    def sample(commit: str, score: float):
        import json
        from hashlib import sha256

        def digest(value):
            return sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

        details = {
            "fixture/profile": {"queries": {"query": {"score": score}}, "uses": [], "metrics": {}}
        }
        report = {
            "core_distribution": {
                "commit": commit,
                "url": "https://github.com/cogkura/cogkura.git",
                "vcs": "git",
                "installed_module": True,
                "version": "0.20.1",
                "distribution_version": "0.20.1",
            },
            "core_version": "0.20.1",
            "diagnostic_mismatches": [],
            "postgres": {"status": "PASS"},
            "source_metrics": {"source_assessment_accuracy": 1},
            "python": "3.12",
            "sqlite_version": "3",
            "seed": 183,
            "hash_seed": 0,
            "platform": "Linux-test",
            "runs": {
                "fixture/profile": {
                    "queries": {"query": digest(details["fixture/profile"]["queries"]["query"])},
                    "uses": digest([]),
                    "metrics": {},
                }
            },
        }
        return report, details

    left, left_details = sample(_BASE, 0.25)
    right, right_details = sample(_CANDIDATE, 0.5)
    return left, right, left_details, right_details


def test_platform_control_retains_exact_unapproved_differences() -> None:
    module = _module()
    result = module.compare(*_inputs(), baseline_commit=_BASE, candidate_commit=_CANDIDATE)
    assert result["diagnostic_only"] and not result["approved"]
    assert result["queries"][0]["fields"][0]["left"] == 0.25
    assert result["queries"][0]["fields"][0]["right"] == 0.5
    assert not result["nonquery"]


def test_platform_control_rejects_tampering_and_different_interpreter() -> None:
    module = _module()
    left, right, left_details, right_details = _inputs()
    right_details["fixture/profile"]["queries"]["query"]["score"] = 99
    with pytest.raises(ValueError, match="fingerprints"):
        module.compare(
            left,
            right,
            left_details,
            right_details,
            baseline_commit=_BASE,
            candidate_commit=_CANDIDATE,
        )
    left, right, left_details, right_details = _inputs()
    right["python"] = "different runtime"
    with pytest.raises(ValueError, match="python"):
        module.compare(
            left,
            right,
            left_details,
            right_details,
            baseline_commit=_BASE,
            candidate_commit=_CANDIDATE,
        )


def test_paired_provenance_requires_matching_clean_checkout_and_platform() -> None:
    module = _module()
    left, right, left_details, right_details = _inputs()
    kwargs = {
        "baseline_commit": _BASE,
        "candidate_commit": _CANDIDATE,
        "require_paired_provenance": True,
    }
    with pytest.raises(ValueError, match="provenance"):
        module.compare(left, right, left_details, right_details, **kwargs)
    provenance = {"commit": "a" * 40, "clean": True, "module_in_checkout": True}
    left["bench_provenance"] = provenance
    right["bench_provenance"] = dict(provenance)
    result = module.compare(left, right, left_details, right_details, **kwargs)
    assert result["paired_provenance_checked"] and not result["approved"]
    right["platform"] = "other-platform"
    with pytest.raises(ValueError, match="same platform"):
        module.compare(left, right, left_details, right_details, **kwargs)
    right["platform"] = left["platform"]
    right["bench_provenance"]["clean"] = False
    with pytest.raises(ValueError, match="provenance"):
        module.compare(left, right, left_details, right_details, **kwargs)
    right["bench_provenance"]["clean"] = True
    right["postgres"]["status"] = "FAIL"
    with pytest.raises(ValueError, match="PostgreSQL"):
        module.compare(left, right, left_details, right_details, **kwargs)
