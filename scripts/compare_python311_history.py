#!/usr/bin/env python3
"""Compare unchanged Python 3.11 benchmark signatures with historical Core 0.18.4.

This is an additional same-runtime comparison. It does not approve or change
any raw mismatch with the original frozen gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HISTORICAL_COMMIT = "93cb7f6a6daae30333008600f3556e6af4f99b3d"
CANDIDATE_COMMIT = "f289035351e3c101fd932f4d6d9e9cd56583ace0"
RELEASE_COMMIT = "13ad7336de1e8be4eba95fbd673ccb448c612d03"
HISTORICAL_SHA256 = "2c840aedcf9bd1b1515565dc324a0a7082630b4df621d8708437fb5b452e317f"
APPROVED_CORRECTION = {
    "run": "authoritative_corrections_v1/cogkura-correction",
    "query": "ac-q-c20",
    "before": "79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80",
    "after": "9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe",
}


def compare(
    historical: dict[str, Any], candidate: dict[str, Any], *, public_release: bool = False
) -> dict[str, Any]:
    candidate_commit = RELEASE_COMMIT if public_release else CANDIDATE_COMMIT
    candidate_version = "0.19.5" if public_release else "0.18.4"
    for report, commit, version in (
        (historical, HISTORICAL_COMMIT, "0.18.4"),
        (candidate, candidate_commit, candidate_version),
    ):
        identity = report["core_distribution"]
        if (
            identity.get("commit") != commit
            or identity.get("installed_module") is not True
            or identity.get("vcs") != "git"
            or identity.get("url") != "https://github.com/cogkura/cogkura.git"
            or identity.get("version") != version
            or identity.get("distribution_version") != version
        ):
            raise ValueError("historical or candidate Core identity does not match")
        if (
            report.get("seed") != 183
            or report.get("hash_seed") != 0
            or report.get("diagnostic_mismatches") != []
            or report.get("postgres", {}).get("status") != "PASS"
            or report.get("source_metrics", {}).get("source_assessment_accuracy") != 1
        ):
            raise ValueError("diagnostics or PostgreSQL parity did not pass")
        if report.get("raw_frozen_comparison_passed") is not False:
            raise ValueError("historical raw frozen mismatch is absent")
        if report.get("approval_errors") or report.get("approved_frozen_corrections") != [
            APPROVED_CORRECTION
        ]:
            raise ValueError("the explicitly approved correction did not match")
    old, new = historical["runs"], candidate["runs"]
    if len(old) != 22 or set(old) != set(new):
        raise ValueError("the complete historical run population is required")
    mismatches = sorted(name for name in old if old[name] != new[name])
    return {
        "python": "3.11",
        "historical_commit": HISTORICAL_COMMIT,
        "candidate_commit": candidate_commit,
        "historical_raw_frozen_passed": historical["raw_frozen_comparison_passed"],
        "candidate_raw_frozen_passed": candidate["raw_frozen_comparison_passed"],
        "historical_unapproved_frozen_mismatches": historical["unapproved_frozen_mismatches"],
        "candidate_unapproved_frozen_mismatches": candidate["unapproved_frozen_mismatches"],
        "run_count": len(old),
        "same_runtime_mismatches": mismatches,
        "same_runtime_comparison_passed": not mismatches,
    }


def main() -> int:
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--public-release",
        action="store_true",
        help="compare the separately approved Core 0.19.5 release",
    )
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error("this historical comparison is specific to Python 3.11")
    try:
        historical_bytes = args.historical.read_bytes()
        if hashlib.sha256(historical_bytes).hexdigest() != HISTORICAL_SHA256:
            raise ValueError("historical report digest changed")
        result = compare(
            json.loads(historical_bytes),
            json.loads(args.candidate.read_text()),
            public_release=args.public_release,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["same_runtime_comparison_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
