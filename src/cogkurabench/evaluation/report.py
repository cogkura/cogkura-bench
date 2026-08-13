"""Benchmark result persistence and reporting."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from cogkurabench.evaluation.result import BenchmarkResult


class _JsonEncoder(json.JSONEncoder):
    def default(self, o: object) -> object:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, StrEnum):
            return o.value
        if isinstance(o, MappingProxyType):
            return dict(o)
        if isinstance(o, Mapping):
            return dict(o)
        if is_dataclass(o):
            return {field.name: _to_jsonable(getattr(o, field.name)) for field in fields(o)}
        if isinstance(o, tuple):
            return [_to_jsonable(item) for item in o]
        return super().default(o)


def _to_jsonable(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if is_dataclass(value):
        return {field.name: _to_jsonable(getattr(value, field.name)) for field in fields(value)}
    return value


def result_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    """Convert a benchmark result to a JSON-serializable dict."""
    payload = json.dumps(_to_jsonable(result), cls=_JsonEncoder)
    return cast(dict[str, Any], json.loads(payload))


def write_result_json(result: BenchmarkResult, path: Path) -> None:
    """Write canonical JSON results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result_to_dict(result), handle, indent=2, cls=_JsonEncoder)
        handle.write("\n")


def write_summary_markdown(result: BenchmarkResult, path: Path) -> None:
    """Write a short human-readable summary."""
    lines = [
        "# CogKuraBench summary",
        "",
        f"- Benchmark: {result.benchmark_version}",
        f"- Dataset: {result.dataset_version}",
        f"- Backend: {result.backend_name}",
        f"- Duration: {result.duration_ms:.1f} ms",
        "",
        "## Capability scores",
        "",
        "| Capability | Queries | Recall@5 | MRR |",
        "| --- | ---: | ---: | ---: |",
    ]
    for capability_name, capability_result in sorted(result.capability_results.items()):
        recall = capability_result.metrics.get("recall@5", 0.0)
        mrr = capability_result.metrics.get("mrr", 0.0)
        lines.append(
            f"| {capability_name} | {capability_result.query_count} | {recall:.3f} | {mrr:.3f} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
