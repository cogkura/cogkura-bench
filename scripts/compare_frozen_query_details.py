#!/usr/bin/env python3
"""Explain fingerprint differences without changing the strict frozen comparison."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return json.loads(data)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def differences(left: Any, right: Any, path: str = "") -> list[dict[str, Any]]:
    if isinstance(left, dict) and isinstance(right, dict):
        rows = []
        for key in sorted(left.keys() | right.keys()):
            if key not in left or key not in right:
                rows.append(
                    {
                        "field": f"{path}.{key}",
                        "left_present": key in left,
                        "right_present": key in right,
                    }
                )
            else:
                rows.extend(differences(left[key], right[key], f"{path}.{key}"))
        return rows
    if isinstance(left, list) and isinstance(right, list):
        rows = []
        for index in range(max(len(left), len(right))):
            if index >= len(left) or index >= len(right):
                rows.append(
                    {
                        "field": f"{path}[{index}]",
                        "left_present": index < len(left),
                        "right_present": index < len(right),
                    }
                )
            else:
                rows.extend(differences(left[index], right[index], f"{path}[{index}]"))
        return rows
    if type(left) is type(right) and left == right:
        return []
    numeric = type(left) in (int, float) and type(right) in (int, float)
    return [
        {
            "field": path,
            "left": left,
            "right": right,
            "absolute_delta": abs(left - right) if numeric else None,
        }
    ]


def compare(
    gold: dict[str, Any], report: dict[str, Any], left: dict[str, Any], right: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for run in report["unapproved_frozen_mismatches"]:
        for query, fingerprint in report["runs"][run]["queries"].items():
            gold_hash = gold["runs"][run]["queries"][query]
            if fingerprint == gold_hash:
                continue
            a, b = left[run]["queries"][query], right[run]["queries"][query]
            if digest(a) != gold_hash or digest(b) != fingerprint:
                raise ValueError(f"captured details do not match fingerprints: {run}/{query}")
            rows.append(
                {
                    "run": run,
                    "query": query,
                    "gold_hash": gold_hash,
                    "actual_hash": fingerprint,
                    "fields": differences(a, b),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("gold", "report", "gold-details", "actual-details", "output"):
        parser.add_argument(f"--{arg}", type=Path, required=True)
    args = parser.parse_args()
    rows = compare(
        read_json(args.gold),
        read_json(args.report),
        read_json(args.gold_details),
        read_json(args.actual_details),
    )
    args.output.write_text(
        json.dumps({"approved": False, "queries": rows}, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
