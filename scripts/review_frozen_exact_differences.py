#!/usr/bin/env python3
"""Review only explicitly approved exact frozen differences; never alter the raw report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from run_source_metamemory_validation import validate_approval


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            result.update(flatten(item, f"{prefix}.{key}" if prefix else key))
        return result
    return {prefix: value}


def review(gold_bytes: bytes, report: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    if approval.get("schema_version") != 1 or not approval.get("approved_on"):
        raise ValueError("an explicit dated approval is required")
    identity = report["core_distribution"]
    candidate = approval["candidate"]
    if (
        report.get("core_version") != candidate["version"]
        or identity.get("commit") != candidate["commit"]
        or identity.get("version") != candidate["version"]
        or identity.get("distribution_version") != candidate["version"]
        or identity.get("installed_module") is not True
        or identity.get("vcs") != "git"
        or identity.get("url") != "https://github.com/cogkura/cogkura.git"
    ):
        raise ValueError("installed distribution does not match the exact approved candidate")
    if hashlib.sha256(gold_bytes).hexdigest() != approval["baseline_sha256"]:
        raise ValueError("original gold digest differs from the approved baseline")
    if not report.get("platform", "").startswith(approval["platform_prefix"]):
        raise ValueError("platform is outside the approved environment")
    version = report.get("python", "").split(" ", 1)[0]
    if version not in approval["environments"]:
        raise ValueError("Python version is outside the approved environment")
    if (
        report.get("raw_frozen_comparison_passed") is not False
        or report.get("seed") != 183
        or report.get("hash_seed") != 0
        or report.get("diagnostic_mismatches") != []
        or report.get("postgres", {}).get("status") != "PASS"
        or report.get("source_metrics", {}).get("source_assessment_accuracy") != 1
    ):
        raise ValueError("required diagnostic, PostgreSQL or source checks did not pass")
    correction = report.get("reviewed_correction_manifest")
    validate_approval(correction, gold_bytes, identity)
    if (
        report.get("approval_errors")
        or report.get("approved_frozen_corrections") != correction["corrections"]
    ):
        raise ValueError("separately approved frozen correction did not match")
    gold = json.loads(gold_bytes)
    if set(gold["runs"]) != set(report["runs"]):
        raise ValueError("frozen run population differs")
    observed = []
    approved_correction = correction["corrections"][0]
    for run, baseline in gold["runs"].items():
        before, after = flatten(baseline), flatten(report["runs"][run])
        if before.keys() != after.keys():
            raise ValueError(f"frozen field population differs in {run}")
        for path in sorted(before):
            if before[path] == after[path] and type(before[path]) is type(after[path]):
                continue
            if (
                run == approved_correction["run"]
                and path == "queries." + approved_correction["query"]
                and before[path] == approved_correction["before"]
                and after[path] == approved_correction["after"]
            ):
                continue
            observed.append(
                {"run": run, "field": path, "before": before[path], "after": after[path]}
            )
    expected = approval["environments"][version]
    if observed != expected:
        raise ValueError("one or more exact approved field differences changed")
    return {
        "candidate": candidate,
        "python": version,
        "platform": report["platform"],
        "raw_frozen_comparison_passed": report["raw_frozen_comparison_passed"],
        "exact_approved_field_count": len(observed),
        "reviewed_comparison_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(
            args.gold.read_bytes(),
            json.loads(args.report.read_text()),
            json.loads(args.approval.read_text()),
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
