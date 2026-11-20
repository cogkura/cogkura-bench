#!/usr/bin/env python3
"""Compare two diagnostic scoring runs without changing frozen expectations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from compare_frozen_query_details import differences


def item_identity(items: list[dict[str, Any]]) -> list[tuple[Any, Any, tuple[Any, ...]]]:
    return [(item["memory_type"], item["text"], tuple(item["source_event_ids"])) for item in items]


def compare(default: dict[str, Any], alternative: dict[str, Any]) -> dict[str, Any]:
    if (
        default["policy"] != "default"
        or alternative["policy"] != "idf-off"
        or default["core_distribution"] != alternative["core_distribution"]
        or default["python"] != alternative["python"]
        or default["seed"] != alternative["seed"]
        or default["hash_seed"] != alternative["hash_seed"]
        or set(default["runs"]) != set(alternative["runs"])
    ):
        raise ValueError("scoring runs do not share an exact candidate and fixture")
    rows = []
    totals = {
        key: 0
        for key in (
            "queries",
            "changed_signatures",
            "retrieved_item_sequences",
            "retrieved_event_sequences",
            "context_item_sequences",
            "query_metric_changes",
            "aggregate_metric_runs",
            "use_runs",
        )
    }
    for name, before in sorted(default["runs"].items()):
        after = alternative["runs"][name]
        if set(before["queries"]) != set(after["queries"]):
            raise ValueError(f"query population differs: {name}")
        changed = []
        retrieval = []
        events = []
        context = []
        metric_diffs = []
        for query, left in sorted(before["queries"].items()):
            right = after["queries"][query]
            if left != right:
                changed.append(query)
            if item_identity(left["retrieved_items"]) != item_identity(right["retrieved_items"]):
                retrieval.append(query)
            if left["retrieved_event_ids"] != right["retrieved_event_ids"]:
                events.append(query)
            if item_identity(left["context_items"]) != item_identity(right["context_items"]):
                context.append(query)
            if left["metrics"] != right["metrics"]:
                metric_diffs.append(
                    {"query": query, "fields": differences(left["metrics"], right["metrics"])}
                )
        aggregate_diffs = differences(before["metrics"], after["metrics"])
        use_diffs = differences(before["uses"], after["uses"])
        rows.append(
            {
                "run": name,
                "query_count": len(before["queries"]),
                "changed_queries": changed,
                "retrieved_item_sequence_changes": retrieval,
                "retrieved_event_sequence_changes": events,
                "context_item_sequence_changes": context,
                "query_metric_differences": metric_diffs,
                "aggregate_metric_differences": aggregate_diffs,
                "use_differences": use_diffs,
            }
        )
        totals["queries"] += len(before["queries"])
        totals["changed_signatures"] += len(changed)
        totals["retrieved_item_sequences"] += len(retrieval)
        totals["retrieved_event_sequences"] += len(events)
        totals["context_item_sequences"] += len(context)
        totals["query_metric_changes"] += len(metric_diffs)
        totals["aggregate_metric_runs"] += bool(aggregate_diffs)
        totals["use_runs"] += bool(use_diffs)
    return {
        "diagnostic_only": True,
        "approved": False,
        "candidate": default["core_distribution"],
        "python": default["python"],
        "totals": totals,
        "runs": rows,
        "source_v2_metrics_differences": differences(
            default["source_v2"]["metrics"], alternative["source_v2"]["metrics"]
        ),
        "source_v2_query_differences": differences(
            default["source_v2"]["queries"], alternative["source_v2"]["queries"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("default", "alternative", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    output = compare(json.loads(args.default.read_text()), json.loads(args.alternative.read_text()))
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output["totals"], indent=2))


if __name__ == "__main__":
    main()
