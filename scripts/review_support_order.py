#!/usr/bin/env python3
"""Compare detailed backend evidence with support-ID order normalized only."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

CASES = {
    "mini",
    "authoritative_corrections_v1",
    "persistent_inhibition_v1",
    "source_aware_metamemory_v1",
}
MODES = ("memory", "sqlite", "sqlite_reopen", "postgres")
SUPPORT_FIELDS = ("authoritative_correction_observations", "source_authority_observations")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _normalize(detail: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(detail)
    for field in SUPPORT_FIELDS:
        observations = result[field]
        if not isinstance(observations, list):
            raise ValueError(f"{field} must be a list")
        for observation in observations:
            ids = observation["supporting_event_ids"]
            if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
                raise ValueError("supporting event IDs must be a list of strings")
            observation["supporting_event_ids"] = sorted(ids)
    return result


def review(report: dict[str, Any], *, version: str, commit: str) -> dict[str, Any]:
    if report.get("core_source_dirty") is not False:
        raise ValueError("a clean Core source is required")
    if report.get("core_commit") != commit or report.get("core_version") != version:
        raise ValueError("report does not identify the selected candidate")
    cases = report["cases"]
    if set(cases) != CASES:
        raise ValueError("all four controlled workloads are required")
    mismatches: list[str] = []
    normalized_only: list[str] = []
    for dataset, case in cases.items():
        if case["sqlite_reopen_reopen_count"] <= 0:
            mismatches.append(f"{dataset}/no_reopen")
        for mode in (*MODES, *(("postgres_repeat",) if dataset == "mini" else ())):
            data = case[mode]
            details = data["query_details"]
            if not isinstance(details, dict) or not details:
                raise ValueError(f"query details required: {dataset}/{mode}")
            if {key: _digest(value) for key, value in details.items()} != data["queries"]:
                raise ValueError(f"query details do not match fingerprints: {dataset}/{mode}")
        ref = case["memory"]
        for mode in (*MODES[1:], *(("postgres_repeat",) if dataset == "mini" else ())):
            actual = case[mode]
            if {
                k: v
                for k, v in ref.items()
                if k not in ("queries", "query_details", "observation_id_map")
            } != {
                k: v
                for k, v in actual.items()
                if k not in ("queries", "query_details", "observation_id_map")
            }:
                mismatches.append(f"{dataset}/{mode}/other")
            expected_details, actual_details = ref["query_details"], actual["query_details"]
            if set(expected_details) != set(actual_details):
                mismatches.append(f"{dataset}/{mode}/population")
                continue
            for query, expected in expected_details.items():
                observed = actual_details[query]
                if _normalize(expected) != _normalize(observed):
                    mismatches.append(f"{dataset}/{mode}/{query}")
                elif expected != observed:
                    normalized_only.append(f"{dataset}/{mode}/{query}")
    identity = report.get("core_distribution", {})
    identity_verified = (
        identity.get("version") == version
        and identity.get("distribution_version") == version
        and identity.get("commit") == commit
        and identity.get("vcs") == "git"
        and identity.get("url") == "https://github.com/cogkura/cogkura.git"
        and identity.get("installed_module") is True
    )
    return {
        "core_commit": commit,
        "core_version": version,
        "raw_passed": report["passed"],
        "normalized_only": normalized_only,
        "mismatches": mismatches,
        "semantic_comparison_passed": not mismatches,
        "official_identity_verified": identity_verified,
        "release_comparison_passed": not mismatches and identity_verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(
            json.loads(args.report.read_text()), version=args.version, commit=args.commit
        )
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["release_comparison_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
