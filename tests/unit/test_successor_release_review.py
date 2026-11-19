"""Exercise the successor and the limited order-insensitive comparison."""

from __future__ import annotations

import copy
import gzip
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "b30433c9577fe2493072e442b0f4ea307f342fcf"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report(name):
    with gzip.open(ROOT / "docs/findings/data" / name, "rt") as stream:
        return json.load(stream)


def test_successor_preserves_original_and_fails_on_other_change():
    mod = load("review_successor_frozen")
    raw = report("core-0200-b30433c-frozen.json.gz")
    original = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    successor = json.loads((ROOT / "tests/golden/cogkura_0200_successor.json").read_text())
    result = mod.review(raw, original, successor, version="0.20.0", commit=COMMIT)
    assert result["successor_comparison_passed"]
    assert result["original_mismatches"] == [mod.RUN]
    assert not result["release_comparison_passed"]  # local provenance
    bad = copy.deepcopy(successor)
    bad["runs"][mod.RUN]["queries"]["ac-q-c01"] = "different"
    with pytest.raises(ValueError, match="precisely"):
        mod.review(raw, original, bad, version="0.20.0", commit=COMMIT)
    raw["runs"][mod.RUN]["queries"]["ac-q-c01"] = "different"
    assert not mod.review(raw, original, successor, version="0.20.0", commit=COMMIT)[
        "successor_comparison_passed"
    ]


def test_support_order_review_only_normalizes_support_order():
    mod = load("review_support_order")
    raw = report("core-0200-b30433c-backends.json.gz")
    result = mod.review(raw, version="0.20.0", commit=COMMIT)
    assert result["semantic_comparison_passed"]
    assert len(result["normalized_only"]) == 9
    assert not result["release_comparison_passed"]
    case = raw["cases"]["authoritative_corrections_v1"]["sqlite"]
    query = case["query_details"]["ac-q-c03"]
    ids = query["authoritative_correction_observations"][0]["supporting_event_ids"]
    ids.append(ids[0])  # multiplicity is retained
    case["queries"]["ac-q-c03"] = mod._digest(query)
    assert not mod.review(raw, version="0.20.0", commit=COMMIT)["semantic_comparison_passed"]
    ids.pop()
    query["rendered"] = "changed"
    case["queries"]["ac-q-c03"] = mod._digest(query)
    assert not mod.review(raw, version="0.20.0", commit=COMMIT)["semantic_comparison_passed"]
    case["queries"]["ac-q-c03"] = "forged"
    with pytest.raises(ValueError, match="fingerprints"):
        mod.review(raw, version="0.20.0", commit=COMMIT)


def test_support_review_requires_postgres_repeat_and_reopen():
    mod = load("review_support_order")
    raw = report("core-0200-b30433c-backends.json.gz")
    del raw["cases"]["mini"]["postgres_repeat"]
    with pytest.raises(KeyError):
        mod.review(raw, version="0.20.0", commit=COMMIT)
    raw = report("core-0200-b30433c-backends.json.gz")
    raw["cases"]["mini"]["sqlite_reopen_reopen_count"] = 0
    assert not mod.review(raw, version="0.20.0", commit=COMMIT)["semantic_comparison_passed"]


def test_release_reviews_require_matching_official_identity():
    frozen_mod = load("review_successor_frozen")
    order_mod = load("review_support_order")
    frozen = report("core-0200-b30433c-frozen.json.gz")
    order = report("core-0200-b30433c-backends.json.gz")
    original = (ROOT / "tests/golden/cogkura_0182_frozen.json").read_bytes()
    successor = json.loads((ROOT / "tests/golden/cogkura_0200_successor.json").read_text())
    for data in (frozen, order):
        data["core_distribution"]["url"] = "https://github.com/cogkura/cogkura.git"
    assert frozen_mod.review(frozen, original, successor, version="0.20.0", commit=COMMIT)[
        "release_comparison_passed"
    ]
    assert order_mod.review(order, version="0.20.0", commit=COMMIT)["release_comparison_passed"]
    frozen["core_distribution"]["commit"] = "wrong"
    order["core_distribution"]["installed_module"] = False
    assert not frozen_mod.review(frozen, original, successor, version="0.20.0", commit=COMMIT)[
        "release_comparison_passed"
    ]
    assert not order_mod.review(order, version="0.20.0", commit=COMMIT)["release_comparison_passed"]
