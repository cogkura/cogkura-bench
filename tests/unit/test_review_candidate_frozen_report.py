"""Review raw candidate comparisons without changing their evidence."""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "review_candidate_frozen_report", ROOT / "scripts/review_candidate_frozen_report.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(minor: str):
    gold = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    path = (
        ROOT / f"docs/findings/data/embedded-core-0.19.6-788444d-linux-3{minor}-frozen-raw.json.gz"
    )
    report = json.loads(gzip.decompress(path.read_bytes()))
    directory = ROOT / "tests/reviewed_corrections"
    correction = json.loads((directory / "cogkura_0196_788444d.json").read_text())
    exact = json.loads((directory / "cogkura_0196_788444d_linux_exact.json").read_text())
    return gold, report, correction, exact


@pytest.mark.parametrize("minor", ["11", "12", "13", "14", "15"])
def test_review_preserves_raw_and_requires_both_approvals(minor: str) -> None:
    gold, report, correction, exact = fixture(minor)
    original = copy.deepcopy(report)
    assert not module.review(gold, report, correction)["reviewed_comparison_passed"]
    result = module.review(gold, report, correction, exact)
    assert result["reviewed_comparison_passed"]
    assert result["raw_frozen_comparison_passed"] is False
    assert report == original


def test_review_rejects_tampered_raw_or_wrong_candidate() -> None:
    gold, report, correction, exact = fixture("12")
    report["runs"]["mini/cogkura"]["queries"]["q01"] = "unexpected"
    with pytest.raises(ValueError):
        module.review(gold, report, correction, exact)
    gold, report, correction, exact = fixture("12")
    correction["candidate"]["commit"] = "0" * 40
    with pytest.raises(ValueError):
        module.review(gold, report, correction, exact)


def test_0201_approval_does_not_authorize_0202() -> None:
    gold = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    manifest = json.loads(
        (ROOT / "tests/reviewed_corrections/cogkura_0201_4c53eb6.json").read_text()
    )
    identity = {
        "version": "0.20.2",
        "distribution_version": "0.20.2",
        "commit": manifest["candidate"]["commit"],
        "vcs": "git",
        "url": "https://github.com/cogkura/cogkura.git",
        "installed_module": True,
    }
    with pytest.raises(ValueError, match="does not match approval"):
        module.validate_approval(manifest, gold, identity)


def test_v2_review_requires_explicit_selection_and_only_the_known_difference() -> None:
    gold, report, correction, exact = fixture("12")
    report["source_fixture"] = "source_aware_metamemory_v2"
    report["source_metrics"] = {
        "source_assessment_accuracy": 190 / 191,
        "source_assessment_check_count": 191,
        "source_assessment_match_count": 190,
        "source_assessment_mismatch_count": 1,
    }
    report["source_history_v2"] = {
        "metrics": {
            "source_assessment_accuracy": 1,
            "source_assessment_check_count": 191,
            "source_assessment_match_count": 191,
            "source_assessment_mismatch_count": 0,
        },
        "v1_withdrawn_metrics": {"source_assessment_mismatch_count": 1},
        "transition_event_ids": ["sm-chain-replace", "sm-chain-withdraw"],
        "outputs_match_v1": True,
        "postgres": {"status": "PASS"},
    }
    with pytest.raises(ValueError):
        module.review(gold, report, correction, exact)
    reviewed = module.review(gold, report, correction, exact, allow_source_history_v2=True)
    assert reviewed["reviewed_comparison_passed"]
    assert reviewed["raw_source_v1_accuracy"] == 190 / 191
    assert reviewed["source_v2_accuracy"] == 1
    for key, value in (
        ("outputs_match_v1", False),
        ("transition_event_ids", ["sm-chain-withdraw"]),
        ("postgres", {"status": "FAIL"}),
        ("v1_withdrawn_metrics", {"source_assessment_mismatch_count": 0}),
        ("metrics", {"source_assessment_accuracy": 1}),
    ):
        bad = copy.deepcopy(report)
        bad["source_history_v2"][key] = value
        with pytest.raises(ValueError):
            module.review(gold, bad, correction, exact, allow_source_history_v2=True)
    bad = copy.deepcopy(report)
    bad["source_metrics"]["source_assessment_mismatch_count"] = 2
    with pytest.raises(ValueError):
        module.review(gold, bad, correction, exact, allow_source_history_v2=True)
    bad = copy.deepcopy(report)
    bad["runs"]["mini/cogkura"]["queries"]["q01"] = "unexpected"
    with pytest.raises(ValueError):
        module.review(gold, bad, correction, exact, allow_source_history_v2=True)


@pytest.mark.parametrize(
    ("name", "raw", "manifest", "field_count"),
    [
        (
            "macos",
            "docs/findings/core-0203-a31f71e-frozen-raw.json.gz",
            "cogkura_0203_a31f71e_macos311_exact.json",
            82,
        ),
        *(
            (
                f"linux-{version}",
                f"docs/findings/data/core-0203-a31f71e-linux-v2/python-{version}-frozen-raw.json.gz",
                "cogkura_0203_a31f71e_linux_exact.json",
                87 if version == "3.11" else 17,
            )
            for version in ("3.11", "3.12", "3.13", "3.14", "3.15")
        ),
    ],
)
def test_0203_review_is_exact_and_preserves_raw(
    name: str, raw: str, manifest: str, field_count: int
) -> None:
    gold = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    report = json.loads(gzip.decompress((ROOT / raw).read_bytes()))
    original = copy.deepcopy(report)
    directory = ROOT / "tests/reviewed_corrections"
    correction = json.loads((directory / "cogkura_0203_a31f71e.json").read_text())
    exact = json.loads((directory / manifest).read_text())
    result = module.review(gold, report, correction, exact, allow_source_history_v2=True)
    assert result["reviewed_comparison_passed"], name
    assert result["raw_frozen_comparison_passed"] is False
    assert result["exact_review"]["exact_approved_field_count"] == field_count
    assert report == original
    report["core_distribution"]["commit"] = "0" * 40
    with pytest.raises(ValueError):
        module.review(gold, report, correction, exact, allow_source_history_v2=True)
