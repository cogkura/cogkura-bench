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
