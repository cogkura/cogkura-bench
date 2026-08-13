"""Expanded benchmark reporting."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from cogkurabench.evaluation.evaluator import aggregate_capability_results
from cogkurabench.evaluation.result import BenchmarkResult, CapabilityResult
from cogkurabench.models import Capability

_CAPABILITY_METRIC_KEYS: dict[Capability, tuple[str, ...]] = {
    Capability.DIRECT_RECALL: ("recall@5", "mrr"),
    Capability.EPISODIC_RECALL: ("recall@5", "mrr"),
    Capability.ASSOCIATIVE_RECALL: ("recall@5", "mrr"),
    Capability.TEMPORAL_RECALL: (
        "temporal_current_accuracy",
        "temporal_historical_accuracy",
        "recall@5",
    ),
    Capability.KNOWLEDGE_UPDATE: (
        "updated_evidence_recall",
        "stale_intrusion_rate",
        "current_state_ranking",
    ),
    Capability.FORGETTING: (
        "stale_suppression_rate",
        "relevant_long_term_retention",
        "noise_intrusion_rate",
    ),
    Capability.WORKING_MEMORY: (
        "evidence_coverage_at_budget",
        "context_precision",
        "token_efficiency",
    ),
    Capability.LEARNING: ("delta_recall@5", "delta_mrr", "delta_first_relevant_rank"),
    Capability.METAMEMORY: ("missing_knowledge_f1", "conflict_f1", "recall@5"),
}


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


def _primary_metric_name(capability: Capability) -> str:
    keys = _CAPABILITY_METRIC_KEYS.get(capability, ("recall@5",))
    return keys[0]


def _secondary_metric_name(capability: Capability) -> str | None:
    if capability is Capability.TEMPORAL_RECALL:
        return "temporal_historical_accuracy"
    return None


def format_capability_table(
    capability_results: Mapping[str, CapabilityResult],
    *,
    title: str | None = None,
) -> str:
    """Render a capability comparison table."""
    lines: list[str] = []
    if title:
        lines.extend([title, ""])
    header = "| Capability | Queries | Primary | Value | Secondary | Value |"
    separator = "| --- | ---: | --- | ---: | --- | ---: |"
    lines.extend([header, separator])
    for capability_name, capability_result in sorted(capability_results.items()):
        primary = _primary_metric_name(capability_result.capability)
        secondary = _secondary_metric_name(capability_result.capability)
        primary_value = capability_result.metrics.get(primary, 0.0)
        if secondary is not None:
            secondary_value = capability_result.metrics.get(secondary, 0.0)
            lines.append(
                f"| {capability_name} | {capability_result.query_count} | {primary} | "
                f"{primary_value:.3f} | {secondary} | {secondary_value:.3f} |"
            )
        else:
            lines.append(
                f"| {capability_name} | {capability_result.query_count} | {primary} | "
                f"{primary_value:.3f} | | |"
            )
    return "\n".join(lines)


def format_result_tables(result: BenchmarkResult) -> str:
    """Render full and core capability tables for a benchmark result."""
    sections = [
        format_capability_table(result.capability_results, title="## All queries"),
    ]
    core_results = aggregate_capability_results(result.query_results, tags={"core"})
    if core_results:
        sections.append("")
        sections.append(format_capability_table(core_results, title="## Core queries"))
    return "\n".join(sections)


def write_summary_markdown(result: BenchmarkResult, path: Path) -> None:
    """Write a human-readable summary."""
    lines = [
        "# CogKuraBench summary",
        "",
        f"- Benchmark: {result.benchmark_version}",
        f"- Dataset: {result.dataset_version}",
        f"- Backend: {result.backend_name}",
        f"- Backend version: {result.backend_version}",
        f"- Duration: {result.duration_ms:.1f} ms",
        f"- Python: {result.environment.python_version}",
        f"- Platform: {result.environment.platform}",
    ]
    if result.environment.git_commit:
        lines.append(f"- Git commit: {result.environment.git_commit}")
    if result.environment.backend_configuration:
        for key, value in result.environment.backend_configuration.items():
            lines.append(f"- {key}: {value}")
    lines.extend(["", format_result_tables(result), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
