"""Exact numerical-review proposals fail closed on identity and drift."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "review_frozen_exact_differences", ROOT / "scripts/review_frozen_exact_differences.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    gold = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    report = json.loads(
        (ROOT / "docs/findings/data/embedded-core-0.19.5-linux-312-frozen.json").read_text()
    )
    report["python"] = "3.12.16 test"
    report["platform"] = "Linux-test"
    proposal = json.loads((ROOT / "docs/proposed-0195-linux-exact-differences.json").read_text())
    return gold, report, proposal


def test_proposal_needs_approval_and_exact_identity() -> None:
    gold, report, approval = fixture()
    with pytest.raises(ValueError, match="dated approval"):
        module.review(gold, report, approval)
    approval["approved_on"] = "2026-11-16"
    assert module.review(gold, report, approval)["reviewed_comparison_passed"]
    for field, value in (("commit", "wrong"), ("version", "0.19.6"), ("installed_module", False)):
        changed = copy.deepcopy(report)
        changed["core_distribution"][field] = value
        with pytest.raises(ValueError, match="exact approved candidate"):
            module.review(gold, changed, approval)


def test_unapproved_drift_and_environment_fail_closed() -> None:
    gold, report, approval = fixture()
    approval["approved_on"] = "2026-11-16"
    changed = copy.deepcopy(report)
    changed["runs"]["mini/cogkura"]["queries"]["extra"] = "wrong"
    with pytest.raises(ValueError, match="field population"):
        module.review(gold, changed, approval)
    changed = copy.deepcopy(report)
    changed["runs"]["mini/cogkura"]["queries"][
        next(iter(changed["runs"]["mini/cogkura"]["queries"]))
    ] = "wrong"
    with pytest.raises(ValueError, match="field differences"):
        module.review(gold, changed, approval)
    report["python"] = "3.12.17 test"
    with pytest.raises(ValueError, match="outside the approved"):
        module.review(gold, report, approval)
