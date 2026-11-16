#!/usr/bin/env python3
"""Account for explicitly reviewed exact query fingerprints without changing raw results."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASES = {
    "mini",
    "authoritative_corrections_v1",
    "persistent_inhibition_v1",
    "source_aware_metamemory_v1",
}
EXPECTED_MODES = ("sqlite", "sqlite_reopen")


def review(report: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    if report.get("core_source_dirty"):
        raise ValueError("a dirty source run cannot use a candidate approval")
    if approval.get("schema_version") != 1 or report.get("core_commit") != approval.get(
        "core_commit"
    ):
        raise ValueError("approval does not identify this exact candidate")
    modes = tuple(approval.get("modes", EXPECTED_MODES))
    if modes not in (EXPECTED_MODES, (*EXPECTED_MODES, "postgres")):
        raise ValueError("approval names an unsupported set of backend modes")
    cases = report["cases"]
    if set(cases) != EXPECTED_CASES:
        raise ValueError("all four controlled workloads are required")
    for dataset, case in cases.items():
        detail_modes = ("memory", *modes)
        if "postgres_repeat" in case:
            detail_modes += ("postgres_repeat",)
        for mode in detail_modes:
            details = case[mode].get("query_details")
            if details is not None:
                hashes = {
                    key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                    for key, value in details.items()
                }
                if hashes != case[mode]["queries"]:
                    raise ValueError(f"query details do not match fingerprints: {dataset}/{mode}")
    if not approval.get("differences"):
        raise ValueError("approval must name the reviewed differences")
    adjusted = copy.deepcopy(cases)
    accounted = []
    for difference in approval["differences"]:
        dataset, query = difference["dataset"], difference["query"]
        case = adjusted[dataset]
        if case["memory"]["queries"].get(query) != difference["memory"]:
            raise ValueError(f"reviewed memory fingerprint changed: {dataset}/{query}")
        for mode in modes:
            if case[mode]["queries"].get(query) != difference[mode]:
                raise ValueError(f"reviewed {mode} fingerprint changed: {dataset}/{query}")
            case[mode]["queries"][query] = difference["memory"]
        accounted.append(f"{dataset}/{query}")
    if len(accounted) != len(set(accounted)):
        raise ValueError("duplicate reviewed query")
    mismatches = []
    for dataset, case in adjusted.items():
        reference = {
            key: value
            for key, value in case["memory"].items()
            if key not in ("query_details", "observation_id_map")
        }
        for mode in modes:
            compared = {
                key: value
                for key, value in case[mode].items()
                if key not in ("query_details", "observation_id_map")
            }
            if compared != reference:
                mismatches.append(f"{dataset}/{mode}")
        if case["sqlite_reopen_reopen_count"] <= 0:
            mismatches.append(f"{dataset}/no_reopen")
        if "postgres_repeat" in case:
            repeated = {
                key: value
                for key, value in case["postgres_repeat"].items()
                if key not in ("query_details", "observation_id_map")
            }
            if "postgres" not in modes or repeated != reference:
                mismatches.append(f"{dataset}/postgres_repeat")
    return {
        "core_commit": report["core_commit"],
        "raw_passed": report["passed"],
        "approved_queries": accounted,
        "reviewed_modes": modes,
        "unapproved_mismatches": mismatches,
        "reviewed_comparison_passed": not mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(json.loads(args.report.read_text()), json.loads(args.approval.read_text()))
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["reviewed_comparison_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
