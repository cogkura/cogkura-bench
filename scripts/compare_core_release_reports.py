"""Compare two same-environment independent Core frozen reports and details.

This comparison is independent of the frozen-gold reviewer. It preserves raw
runs and does not approve changes against gold or claim latency equivalence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compare(
    baseline: dict[str, Any],
    current: dict[str, Any],
    baseline_details: dict[str, Any],
    current_details: dict[str, Any],
) -> dict[str, Any]:
    """Compare the same Bench workload and execution environment exactly."""
    for name in ("python", "platform", "sqlite_version", "seed", "hash_seed", "source_fixture"):
        if baseline.get(name) != current.get(name):
            raise ValueError(f"environment or fixture differs: {name}")
    old_provenance, new_provenance = (
        baseline.get("bench_provenance"),
        current.get("bench_provenance"),
    )
    if not old_provenance or old_provenance != new_provenance or not old_provenance.get("clean"):
        raise ValueError("same clean Bench provenance is required")
    old, new = baseline["runs"], current["runs"]
    if (
        set(old) != set(new)
        or set(old) != set(baseline_details)
        or set(old) != set(current_details)
    ):
        raise ValueError("run populations differ")
    metric_changes = []
    changed_queries = []
    changed_uses = []
    for run in sorted(old):
        before, after = old[run], new[run]
        if set(before["queries"]) != set(after["queries"]):
            raise ValueError(f"query populations differ in {run}")
        changed_queries.extend(
            {"run": run, "query": query, "before": fingerprint, "after": after["queries"][query]}
            for query, fingerprint in before["queries"].items()
            if fingerprint != after["queries"][query]
        )
        if before["uses"] != after["uses"]:
            changed_uses.append(run)
        if set(before["metrics"]) != set(after["metrics"]):
            raise ValueError(f"metric capability populations differ in {run}")
        for capability, metrics in before["metrics"].items():
            later = after["metrics"][capability]
            if set(metrics) != set(later):
                raise ValueError(f"metric populations differ in {run}/{capability}")
            for metric, value in metrics.items():
                next_value = later[metric]
                if value != next_value or type(value) is not type(next_value):
                    delta = (
                        next_value - value
                        if isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and isinstance(next_value, (int, float))
                        and not isinstance(next_value, bool)
                        else None
                    )
                    metric_changes.append(
                        {
                            "run": run,
                            "capability": capability,
                            "metric": metric,
                            "before": value,
                            "after": next_value,
                            "delta": delta,
                        }
                    )
    changed_details = [run for run in sorted(old) if baseline_details[run] != current_details[run]]
    return {
        "baseline_core": baseline["core_distribution"],
        "current_core": current["core_distribution"],
        "environment": {
            k: current.get(k)
            for k in ("python", "platform", "sqlite_version", "seed", "hash_seed", "source_fixture")
        },
        "bench_provenance": new_provenance,
        "run_count": len(old),
        "query_fingerprint_count": sum(len(v["queries"]) for v in old.values()),
        "identical_run_count": sum(old[k] == new[k] for k in old),
        "changed_query_fingerprints": changed_queries,
        "changed_use_runs": changed_uses,
        "metric_changes": metric_changes,
        "changed_detail_runs": changed_details,
        "latency_included": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("baseline", "current", "baseline-details", "current-details", "output"):
        parser.add_argument(f"--{argument}", type=Path, required=True)
    args = parser.parse_args()
    result = compare(
        *(
            json.loads(path.read_text())
            for path in (args.baseline, args.current, args.baseline_details, args.current_details)
        )
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "run_count",
                    "query_fingerprint_count",
                    "identical_run_count",
                    "changed_detail_runs",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
