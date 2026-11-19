#!/usr/bin/env python3
"""Check the reviewed successor reference without discarding original results."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ORIGINAL_SHA = "927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c"
RUN = "authoritative_corrections_v1/cogkura-correction"
QUERY = "ac-q-c20"
BEFORE = "79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80"
AFTER = "9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe"


def review(
    report: dict[str, Any], original: bytes, successor: dict[str, Any], *, version: str, commit: str
) -> dict[str, Any]:
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("original gold digest changed")
    baseline = json.loads(original)
    if baseline["runs"][RUN]["queries"][QUERY] != BEFORE:
        raise ValueError("original fingerprint changed")
    expected = copy.deepcopy(baseline)
    expected["runs"][RUN]["queries"][QUERY] = AFTER
    actual = {key: value for key, value in successor.items() if key != "successor"}
    if actual != expected or successor.get("successor", {}).get("original_sha256") != ORIGINAL_SHA:
        raise ValueError("successor must differ by precisely the reviewed fingerprint")
    runs = report["runs"]
    keys = runs.keys() | expected["runs"].keys()
    mismatches = sorted(key for key in keys if runs.get(key) != expected["runs"].get(key))
    original_mismatches = sorted(key for key in keys if runs.get(key) != baseline["runs"].get(key))
    identity = report.get("core_distribution", {})
    identity_verified = (
        identity.get("version") == version
        and identity.get("distribution_version") == version
        and identity.get("commit") == commit
        and identity.get("vcs") == "git"
        and identity.get("url") == "https://github.com/cogkura/cogkura.git"
        and identity.get("installed_module") is True
    )
    other_checks = (
        report.get("core_version") == version
        and report.get("diagnostic_mismatches") == []
        and report.get("postgres", {}).get("status") == "PASS"
        and report.get("source_metrics", {}).get("source_assessment_accuracy") == 1
    )
    return {
        "candidate_commit": commit,
        "original_mismatches": original_mismatches,
        "successor_mismatches": mismatches,
        "successor_comparison_passed": not mismatches,
        "other_checks_passed": other_checks,
        "official_identity_verified": identity_verified,
        "release_comparison_passed": not mismatches and other_checks and identity_verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--successor", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(
            json.loads(args.report.read_text()),
            args.original.read_bytes(),
            json.loads(args.successor.read_text()),
            version=args.version,
            commit=args.commit,
        )
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["release_comparison_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
