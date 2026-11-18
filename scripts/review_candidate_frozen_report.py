#!/usr/bin/env python3
"""Review an immutable raw frozen report using explicit candidate-scoped approvals."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from review_frozen_exact_differences import review as review_exact
from run_source_metamemory_validation import compare_frozen, source_checks_pass, validate_approval


def review(
    gold_bytes: bytes,
    raw: dict[str, Any],
    correction: dict[str, Any],
    exact: dict[str, Any] | None = None,
    *,
    allow_source_history_v2: bool = False,
) -> dict[str, Any]:
    """Validate the raw report first and write a distinct, reviewed result."""
    identity = raw["core_distribution"]
    validate_approval(correction, gold_bytes, identity)
    gold = json.loads(gold_bytes)
    raw_comparison = compare_frozen(raw["runs"], gold)
    for key, value in raw_comparison.items():
        if raw.get(key) != value:
            raise ValueError(f"raw report comparison field changed: {key}")
    if (
        raw.get("core_version") != identity.get("version")
        or raw.get("seed") != 183
        or raw.get("hash_seed") != 0
        or raw.get("diagnostic_mismatches") != []
        or raw.get("postgres", {}).get("status") != "PASS"
        or not source_checks_pass(raw, allow_history_v2=allow_source_history_v2)
    ):
        raise ValueError("candidate identity or required diagnostics did not pass")
    compared = compare_frozen(raw["runs"], gold, correction)
    if (
        compared["approval_errors"]
        or compared["approved_frozen_corrections"] != correction["corrections"]
    ):
        raise ValueError("the approved correction is absent or changed")
    reviewed = copy.deepcopy(raw)
    reviewed.update(compared)
    reviewed["reviewed_correction_manifest"] = correction
    exact_result = (
        review_exact(gold_bytes, reviewed, exact, allow_source_history_v2=allow_source_history_v2)
        if exact is not None
        else None
    )
    passed = not compared["unapproved_frozen_mismatches"] or exact_result is not None
    return {
        "candidate": correction["candidate"],
        "python": raw.get("python"),
        "platform": raw.get("platform"),
        "raw_frozen_comparison_passed": raw_comparison["raw_frozen_comparison_passed"],
        "source_fixture": "source_aware_metamemory_v2"
        if allow_source_history_v2
        else "source_aware_metamemory_v1",
        "raw_source_v1_accuracy": raw.get("source_metrics", {}).get("source_assessment_accuracy"),
        "raw_source_v1_mismatch_count": raw.get("source_metrics", {}).get(
            "source_assessment_mismatch_count"
        ),
        "source_v2_accuracy": raw.get("source_history_v2", {})
        .get("metrics", {})
        .get("source_assessment_accuracy")
        if allow_source_history_v2
        else None,
        "correction": compared,
        "exact_review": exact_result,
        "reviewed_comparison_passed": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--correction", required=True, type=Path)
    parser.add_argument("--exact", type=Path)
    parser.add_argument("--source-history-v2", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = review(
            args.gold.read_bytes(),
            json.loads(args.raw.read_text()),
            json.loads(args.correction.read_text()),
            json.loads(args.exact.read_text()) if args.exact else None,
            allow_source_history_v2=args.source_history_v2,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not result["reviewed_comparison_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
