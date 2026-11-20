#!/usr/bin/env python3
"""Compare diagnostic IDF-off backends, retaining support-order differences."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from review_support_order import _normalize


def compare(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("policy") != "idf-off" or report.get("diagnostic_only") is not True:
        raise ValueError("expected an explicitly diagnostic IDF-off report")
    expected = {
        "mini",
        "authoritative_corrections_v1",
        "persistent_inhibition_v1",
        "source_aware_metamemory_v1",
    }
    if set(report["cases"]) != expected:
        raise ValueError("all four controlled workloads are required")
    mismatches: list[str] = []
    order_only: list[str] = []
    for dataset, case in report["cases"].items():
        modes = ["memory", "sqlite", "sqlite_reopen", "postgres"]
        if dataset == "mini":
            modes.append("postgres_repeat")
        if case["sqlite_reopen_reopen_count"] <= 0:
            mismatches.append(f"{dataset}/no_reopen")
        for mode in modes:
            data = case[mode]
            details = data["query_details"]
            hashes = {
                key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                for key, value in details.items()
            }
            if not details or hashes != data["queries"]:
                raise ValueError(f"query details do not match hashes: {dataset}/{mode}")
        ref = case["memory"]
        for mode in modes[1:]:
            actual = case[mode]
            ignored = ("queries", "query_details", "observation_id_map")
            if {k: v for k, v in ref.items() if k not in ignored} != {
                k: v for k, v in actual.items() if k not in ignored
            }:
                mismatches.append(f"{dataset}/{mode}/other")
            if set(ref["query_details"]) != set(actual["query_details"]):
                mismatches.append(f"{dataset}/{mode}/population")
                continue
            for query, left in ref["query_details"].items():
                right = actual["query_details"][query]
                if _normalize(left) != _normalize(right):
                    mismatches.append(f"{dataset}/{mode}/{query}")
                elif left != right:
                    order_only.append(f"{dataset}/{mode}/{query}")
    return {
        "diagnostic_only": True,
        "approved": False,
        "candidate": report["core_distribution"],
        "mismatches": mismatches,
        "support_order_only": order_only,
        "comparison_passed": not mismatches,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.report.read_text()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not result["comparison_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
