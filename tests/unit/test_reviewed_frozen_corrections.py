"""The release exception accepts one reviewed result, never a new baseline."""

from __future__ import annotations

import copy
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = runpy.run_path(str(ROOT / "scripts/run_source_metamemory_validation.py"))
validate_approval = VALIDATOR["validate_approval"]
compare_frozen = VALIDATOR["compare_frozen"]


@pytest.fixture
def comparison():
    manifest = json.loads((ROOT / "tests/reviewed_corrections/cogkura_0184.json").read_text())
    gold = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    baseline = json.loads(gold)
    runs = copy.deepcopy(baseline["runs"])
    entry = manifest["corrections"][0]
    runs[entry["run"]]["queries"][entry["query"]] = entry["after"]
    identity = {
        "version": "0.18.4",
        "distribution_version": "0.18.4",
        "commit": manifest["candidate"]["commit"],
        "vcs": "git",
        "url": "https://github.com/cogkura/cogkura.git",
        "installed_module": True,
    }
    return manifest, gold, baseline, runs, identity


def test_explicit_approval_retains_raw_failure(comparison):
    manifest, gold, baseline, runs, identity = comparison
    validate_approval(manifest, gold, identity)
    before = copy.deepcopy(runs)
    result = compare_frozen(runs, baseline, manifest)
    assert result == {
        "frozen_mismatches": [manifest["corrections"][0]["run"]],
        "raw_frozen_comparison_passed": False,
        "approved_frozen_corrections": manifest["corrections"],
        "unapproved_frozen_mismatches": [],
        "approval_errors": [],
    }
    assert runs == before
    assert json.loads(gold) == baseline


def test_without_explicit_approval_the_same_difference_fails(comparison):
    _, _, baseline, runs, _ = comparison
    result = compare_frozen(runs, baseline)
    assert result["unapproved_frozen_mismatches"] == result["frozen_mismatches"]
    assert result["approved_frozen_corrections"] == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", "0.18.5"),
        ("distribution_version", "0.18.3"),
        ("commit", "a" * 40),
        ("commit", None),
        ("vcs", None),
        ("url", "https://example.invalid/fork.git"),
        ("installed_module", False),
    ],
)
def test_wrong_or_unverifiable_installed_candidate_is_rejected(comparison, field, value):
    manifest, gold, _, _, identity = comparison
    identity[field] = value
    with pytest.raises(ValueError, match="installed Core"):
        validate_approval(manifest, gold, identity)


@pytest.mark.parametrize(
    "change",
    ["gold", "digest", "before", "same_hash", "empty", "duplicate", "malformed", "unknown_key"],
)
def test_invalid_review_does_not_authorise_comparison(comparison, change):
    manifest, gold, _, _, identity = comparison
    entry = manifest["corrections"][0]
    if change == "gold":
        gold += b"\n"
    elif change == "digest":
        manifest["baseline_sha256"] = "0" * 64
    elif change == "before":
        entry["before"] = "0" * 64
    elif change == "same_hash":
        entry["after"] = entry["before"]
    elif change == "empty":
        manifest["corrections"] = []
    elif change == "duplicate":
        manifest["corrections"].append(dict(entry))
    elif change == "malformed":
        entry["after"] = "wildcard"
    else:
        manifest["accept_any_future_version"] = True
    with pytest.raises(ValueError):
        validate_approval(manifest, gold, identity)


@pytest.mark.parametrize(
    "change",
    [
        "reverted",
        "after",
        "missing_query",
        "missing_run",
        "extra_query",
        "extra_run",
        "other_query",
        "metrics",
        "uses",
        "extra_field",
    ],
)
def test_other_drift_or_absent_fix_always_fails(comparison, change):
    manifest, _, baseline, runs, _ = comparison
    entry = manifest["corrections"][0]
    run = runs[entry["run"]]
    if change == "reverted":
        run["queries"][entry["query"]] = entry["before"]
    elif change == "after":
        run["queries"][entry["query"]] = "f" * 64
    elif change == "missing_query":
        del run["queries"][entry["query"]]
    elif change == "missing_run":
        del runs[entry["run"]]
    elif change == "extra_query":
        run["queries"]["new-query"] = "f" * 64
    elif change == "extra_run":
        runs["new-run"] = copy.deepcopy(run)
    elif change == "other_query":
        other = next(k for k in run["queries"] if k != entry["query"])
        run["queries"][other] = "f" * 64
    elif change == "metrics":
        run["metrics"] = {"changed": True}
    elif change == "uses":
        run["uses"] = "f" * 64
    else:
        run["unreviewed"] = True
    result = compare_frozen(runs, baseline, manifest)
    assert result["unapproved_frozen_mismatches"] or result["approval_errors"]
    if change == "reverted":
        assert result["raw_frozen_comparison_passed"] is True
        assert result["approval_errors"]  # Raw equality cannot excuse a reverted fix.


def test_manifest_after_hash_is_required_exactly(comparison):
    manifest, gold, baseline, runs, identity = comparison
    manifest["corrections"][0]["after"] = "e" * 64
    validate_approval(manifest, gold, identity)
    result = compare_frozen(runs, baseline, manifest)
    assert result["approval_errors"]
    assert result["unapproved_frozen_mismatches"]
