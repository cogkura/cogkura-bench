"""Benchmark result models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

from cogkurabench.models import Capability, RetrievedItem


@dataclass(frozen=True, slots=True)
class EnvironmentInfo:
    """Reproducibility metadata for a benchmark run."""

    python_version: str
    platform: str
    git_commit: str | None
    backend_configuration: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "backend_configuration",
            MappingProxyType(dict(self.backend_configuration)),
        )


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Per-query benchmark outcome."""

    query_id: str
    capability: Capability
    retrieved_event_ids: tuple[str, ...]
    expected_event_ids: tuple[str, ...]
    metrics: Mapping[str, float]
    latency_ms: float
    context_tokens: int | None
    retrieved_items: tuple[RetrievedItem, ...] = ()
    context_event_ids: tuple[str, ...] = ()
    context_items: tuple[RetrievedItem, ...] = ()
    indicates_missing_knowledge: bool | None = None
    indicates_conflict: bool | None = None
    assessment_flags: tuple[str, ...] = ()
    assessment_signals: Mapping[str, float | None] = field(default_factory=dict)
    backend_metadata: Mapping[str, Any] = field(default_factory=dict)
    should_abstain: bool = False
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(
            self,
            "assessment_signals",
            MappingProxyType(dict(self.assessment_signals)),
        )
        object.__setattr__(self, "backend_metadata", MappingProxyType(dict(self.backend_metadata)))


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """Aggregated metrics for one capability."""

    capability: Capability
    query_count: int
    metrics: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Complete benchmark run result."""

    benchmark_version: str
    dataset_version: str
    backend_name: str
    backend_version: str | None
    started_at: datetime
    duration_ms: float
    capability_results: Mapping[str, CapabilityResult]
    query_results: tuple[QueryResult, ...]
    environment: EnvironmentInfo

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability_results",
            MappingProxyType(dict(self.capability_results)),
        )
