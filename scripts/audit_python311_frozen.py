#!/usr/bin/env python3
"""Enumerate raw frozen differences; do not approve or normalise them."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def leaves(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            result.update(leaves(item, f"{prefix}.{key}" if prefix else key))
        return result
    return {prefix: value}


def audit(gold: dict[str, Any], old: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for run, baseline in gold["runs"].items():
        before, now = leaves(baseline), leaves(current["runs"][run])
        previous = leaves(old["runs"][run])
        for path in sorted(before.keys() | now.keys()):
            if before.get(path) == now.get(path) and (path in before) == (path in now):
                continue
            a, b = before.get(path), now.get(path)
            field_type = "query fingerprint" if path.startswith("queries.") else "other"
            if (
                path.startswith("metrics.")
                and isinstance(a, (int, float))
                and isinstance(b, (int, float))
            ):
                field_type = "numeric metric"
            results.append(
                {
                    "run": run,
                    "field": path,
                    "type": field_type,
                    "gold": a,
                    "current": b,
                    "previous_core": previous.get(path),
                    "matches_previous_core": path in previous and previous[path] == b,
                    "absolute_delta": abs(a - b) if field_type == "numeric metric" else None,
                    "explanation": "requires investigation",
                }
            )
    return {
        "gold_core_commit": gold.get("core_commit"),
        "previous_core": old.get("core_distribution"),
        "current_core": current.get("core_distribution"),
        "differences": results,
        "note": (
            "Fingerprints do not reveal underlying fields; no difference is approved by this audit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = (args.gold, args.previous, args.current)
    inputs = [p.read_bytes() for p in paths]
    report = audit(*(json.loads(data) for data in inputs))
    report["input_sha256"] = {
        str(p): hashlib.sha256(b).hexdigest() for p, b in zip(paths, inputs, strict=True)
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
