"""The reviewed-order gate remains exact and fails closed on other changes."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[2] / "scripts" / "review_embedded_freeze.py"
spec = importlib.util.spec_from_file_location("review_embedded_freeze", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inputs():
    cases = {}
    for dataset in module.EXPECTED_CASES:
        memory = {"queries": {"q": "old"}, "uses": "same", "metrics": {}, "source_assessments": {}}
        sqlite = {**memory, "queries": {"q": "new" if dataset == "mini" else "old"}}
        cases[dataset] = {
            "memory": memory,
            "sqlite": sqlite,
            "sqlite_reopen": copy.deepcopy(sqlite),
            "sqlite_reopen_reopen_count": 1,
        }
    report = {"core_commit": "candidate", "cases": cases, "passed": False}
    approval = {
        "schema_version": 1,
        "core_commit": "candidate",
        "differences": [
            {
                "dataset": "mini",
                "query": "q",
                "memory": "old",
                "sqlite": "new",
                "sqlite_reopen": "new",
            }
        ],
    }
    return report, approval


def test_review_accounts_for_only_exact_approved_fingerprints() -> None:
    report, approval = inputs()
    result = module.review(report, approval)
    assert result["reviewed_comparison_passed"] is True
    assert result["raw_passed"] is False
    assert report["cases"]["mini"]["sqlite"]["queries"]["q"] == "new"
    report["cases"]["mini"]["sqlite"]["uses"] = "changed"
    assert module.review(report, approval)["unapproved_mismatches"] == ["mini/sqlite"]


def test_review_rejects_wrong_candidate_or_changed_fingerprints() -> None:
    report, approval = inputs()
    report["core_commit"] = "other"
    with pytest.raises(ValueError, match="exact candidate"):
        module.review(report, approval)
    report["core_commit"] = "candidate"
    approval["differences"][0]["sqlite"] = "wrong"
    with pytest.raises(ValueError, match="fingerprint changed"):
        module.review(report, approval)


def test_review_rejects_dirty_source_even_with_the_approved_commit() -> None:
    report, approval = inputs()
    report["core_source_dirty"] = True
    with pytest.raises(ValueError, match="dirty source"):
        module.review(report, approval)


def test_review_rejects_details_that_do_not_match_their_fingerprints() -> None:
    report, approval = inputs()
    report["cases"]["mini"]["sqlite"]["query_details"] = {"q": {"unexpected": True}}
    with pytest.raises(ValueError, match="do not match fingerprints"):
        module.review(report, approval)


def test_review_checks_postgres_only_when_explicitly_in_approval() -> None:
    report, approval = inputs()
    for case in report["cases"].values():
        case["postgres"] = copy.deepcopy(case["memory"])
    report["cases"]["mini"]["postgres"]["queries"]["q"] = "pg-new"
    approval["modes"] = ["sqlite", "sqlite_reopen", "postgres"]
    approval["differences"][0]["postgres"] = "pg-new"
    assert module.review(report, approval)["reviewed_comparison_passed"] is True
    report["cases"]["mini"]["postgres_repeat"] = copy.deepcopy(report["cases"]["mini"]["memory"])
    assert module.review(report, approval)["reviewed_comparison_passed"] is True
    report["cases"]["mini"]["postgres_repeat"]["uses"] = "leaked state"
    assert "mini/postgres_repeat" in module.review(report, approval)["unapproved_mismatches"]
    report["cases"]["mini"]["postgres"]["uses"] = "changed"
    assert "mini/postgres" in module.review(report, approval)["unapproved_mismatches"]


def test_version_scoped_approval_requires_exact_installed_git_identity() -> None:
    report, approval = inputs()
    approval.update(schema_version=2, core_version="0.19.5")
    report.update(
        core_version="0.19.5",
        core_distribution={
            "version": "0.19.5",
            "distribution_version": "0.19.5",
            "commit": "candidate",
            "vcs": "git",
            "url": "https://github.com/cogkura/cogkura.git",
            "installed_module": True,
        },
    )
    assert module.review(report, approval)["reviewed_comparison_passed"]
    report["core_distribution"]["installed_module"] = False
    with pytest.raises(ValueError, match="identity"):
        module.review(report, approval)
