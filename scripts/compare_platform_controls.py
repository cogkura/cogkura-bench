#!/usr/bin/env python3
"""Compare two exact hosted Core commits without changing any release gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from compare_frozen_query_details import differences, digest, read_json


def _validate(report: dict[str, Any], details: dict[str, Any], commit: str) -> None:
    identity = report["core_distribution"]
    if (
        identity.get("commit") != commit
        or identity.get("url") != "https://github.com/cogkura/cogkura.git"
        or identity.get("vcs") != "git"
        or identity.get("installed_module") is not True
    ):
        raise ValueError("report does not identify the exact official Core commit")
    if set(report["runs"]) != set(details):
        raise ValueError("detail population does not match the report")
    for name, run in report["runs"].items():
        detail = details[name]
        if (
            run["queries"] != {key: digest(value) for key, value in detail["queries"].items()}
            or run["uses"] != digest(detail["uses"])
            or run["metrics"] != detail["metrics"]
        ):
            raise ValueError(f"details do not match captured fingerprints: {name}")


def compare(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    baseline_details: dict[str, Any],
    candidate_details: dict[str, Any],
    *,
    baseline_commit: str,
    candidate_commit: str,
) -> dict[str, Any]:
    """Return exact differences; no rounding, acceptance or baseline changes."""
    _validate(baseline, baseline_details, baseline_commit)
    _validate(candidate, candidate_details, candidate_commit)
    for key in ("python", "sqlite_version", "seed", "hash_seed"):
        if baseline[key] != candidate[key]:
            raise ValueError(f"control and candidate differ in {key}")
    if set(baseline_details) != set(candidate_details):
        raise ValueError("run populations differ")
    queries = []
    nonquery = []
    for name in sorted(baseline_details):
        left, right = baseline_details[name], candidate_details[name]
        if set(left["queries"]) != set(right["queries"]):
            raise ValueError(f"query populations differ: {name}")
        for query, before in sorted(left["queries"].items()):
            diff = differences(before, right["queries"][query])
            if diff:
                queries.append({"run": name, "query": query, "fields": diff})
        for key in ("metrics", "uses"):
            diff = differences(left[key], right[key])
            if diff:
                nonquery.append({"run": name, "section": key, "fields": diff})
    return {
        "diagnostic_only": True,
        "approved": False,
        "baseline": baseline["core_distribution"],
        "candidate": candidate["core_distribution"],
        "python": baseline["python"],
        "sqlite_version": baseline["sqlite_version"],
        "baseline_platform": baseline["platform"],
        "candidate_platform": candidate["platform"],
        "seed": baseline["seed"],
        "hash_seed": baseline["hash_seed"],
        "queries": queries,
        "nonquery": nonquery,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "candidate", "baseline-details", "candidate-details", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--candidate-commit", required=True)
    args = parser.parse_args()
    try:
        result = compare(
            read_json(args.baseline),
            read_json(args.candidate),
            read_json(args.baseline_details),
            read_json(args.candidate_details),
            baseline_commit=args.baseline_commit,
            candidate_commit=args.candidate_commit,
        )
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"queries": len(result["queries"]), "nonquery": len(result["nonquery"])}))


if __name__ == "__main__":
    main()
