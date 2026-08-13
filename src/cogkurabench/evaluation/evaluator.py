"""Benchmark evaluation and aggregation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from cogkurabench.evaluation.result import CapabilityResult, QueryResult
from cogkurabench.metrics.efficiency import compute_efficiency_metrics
from cogkurabench.metrics.forgetting import compute_forgetting_metrics
from cogkurabench.metrics.learning import compute_learning_deltas
from cogkurabench.metrics.metamemory import (
    aggregate_binary_metrics,
    conflict_detection,
    missing_knowledge_detection,
)
from cogkurabench.metrics.retrieval import compute_retrieval_metrics
from cogkurabench.metrics.temporal import compute_temporal_metrics
from cogkurabench.metrics.updating import compute_update_metrics
from cogkurabench.metrics.working_memory import compute_working_memory_metrics
from cogkurabench.models import (
    AssessmentResponse,
    BenchmarkQuery,
    Capability,
    ContextResponse,
    ProjectEvent,
)


def aggregate_capability_results(
    query_results: Sequence[QueryResult],
) -> dict[str, CapabilityResult]:
    """Average per-query metrics grouped by capability."""
    grouped: dict[Capability, list[QueryResult]] = defaultdict(list)
    for result in query_results:
        grouped[result.capability].append(result)

    capability_results: dict[str, CapabilityResult] = {}
    for capability, results in grouped.items():
        if not results:
            continue
        metric_names = sorted({name for result in results for name in result.metrics})
        averaged: dict[str, float] = {}
        for name in metric_names:
            values = [result.metrics[name] for result in results if name in result.metrics]
            if values:
                averaged[name] = sum(values) / len(values)
        capability_results[capability.value] = CapabilityResult(
            capability=capability,
            query_count=len(results),
            metrics=averaged,
        )
    return capability_results


def evaluate_query(
    query: BenchmarkQuery,
    ranked_event_ids: Sequence[str],
    *,
    latency_ms: float,
    events_by_id: Mapping[str, ProjectEvent] | None = None,
    context_response: ContextResponse | None = None,
    assessment_response: AssessmentResponse | None = None,
    backend_metadata: dict[str, object] | None = None,
) -> QueryResult:
    """Score one query against retrieved event IDs and optional backend signals."""
    metrics = dict(compute_retrieval_metrics(ranked_event_ids, query))
    metrics.update(compute_temporal_metrics(ranked_event_ids, query))
    metrics.update(compute_update_metrics(ranked_event_ids, query))
    if events_by_id is not None:
        metrics.update(
            compute_forgetting_metrics(ranked_event_ids, query, events_by_id=events_by_id)
        )

    context_event_ids: tuple[str, ...] = ()
    context_tokens: int | None = None
    context_latency_ms: float | None = None
    if context_response is not None:
        context_event_ids = tuple(
            event_id for item in context_response.items for event_id in item.source_event_ids
        )
        context_tokens = context_response.estimated_tokens
        context_latency_ms = context_response.latency_ms
        if events_by_id is not None:
            metrics.update(
                compute_working_memory_metrics(
                    context_event_ids,
                    query,
                    estimated_tokens=context_response.estimated_tokens,
                    events_text={
                        event_id: event.content for event_id, event in events_by_id.items()
                    },
                )
            )

    metrics.update(
        compute_efficiency_metrics(
            retrieval_latency_ms=latency_ms,
            context_latency_ms=context_latency_ms,
            retrieved_count=len(ranked_event_ids),
            selected_count=len(context_event_ids),
            context_tokens=context_tokens,
        )
    )

    indicates_missing: bool | None = None
    indicates_conflict: bool | None = None
    assessment_flags: tuple[str, ...] = ()
    assessment_signals: dict[str, float | None] = {}
    if assessment_response is not None:
        indicates_missing = assessment_response.indicates_missing_knowledge
        indicates_conflict = assessment_response.indicates_conflict
        assessment_flags = assessment_response.flags
        assessment_signals = dict(assessment_response.signals)
        has_conflict_evidence = bool(query.forbidden_evidence_ids) or bool(
            query.acceptable_evidence_ids and query.expected_evidence_ids
        )
        metrics.update(
            missing_knowledge_detection(
                should_abstain=query.should_abstain,
                indicates_missing_knowledge=indicates_missing,
            )
        )
        metrics.update(
            conflict_detection(
                has_conflict_evidence=has_conflict_evidence,
                indicates_conflict=indicates_conflict,
            )
        )

    return QueryResult(
        query_id=query.id,
        capability=query.capability,
        retrieved_event_ids=tuple(ranked_event_ids),
        expected_event_ids=query.expected_evidence_ids,
        metrics=metrics,
        latency_ms=latency_ms,
        context_tokens=context_tokens,
        context_event_ids=context_event_ids,
        indicates_missing_knowledge=indicates_missing,
        indicates_conflict=indicates_conflict,
        assessment_flags=assessment_flags,
        assessment_signals=assessment_signals,
        backend_metadata=backend_metadata or {},
    )


def apply_learning_deltas(
    query_results: list[QueryResult],
    queries_by_id: Mapping[str, BenchmarkQuery],
) -> list[QueryResult]:
    """Return query results with learning delta metrics attached to post queries."""
    results_by_id = {result.query_id: result for result in query_results}
    updated: list[QueryResult] = []
    for result in query_results:
        query = queries_by_id.get(result.query_id)
        if query is None or query.related_query_id is None:
            updated.append(result)
            continue
        pre = results_by_id.get(query.related_query_id)
        if pre is None:
            updated.append(result)
            continue
        deltas = compute_learning_deltas(pre, result, k=query.retrieval_limit)
        updated.append(
            QueryResult(
                query_id=result.query_id,
                capability=result.capability,
                retrieved_event_ids=result.retrieved_event_ids,
                expected_event_ids=result.expected_event_ids,
                metrics={**dict(result.metrics), **deltas},
                latency_ms=result.latency_ms,
                context_tokens=result.context_tokens,
                context_event_ids=result.context_event_ids,
                indicates_missing_knowledge=result.indicates_missing_knowledge,
                indicates_conflict=result.indicates_conflict,
                assessment_flags=result.assessment_flags,
                assessment_signals=dict(result.assessment_signals),
                backend_metadata=dict(result.backend_metadata),
            )
        )
    return updated


def finalize_metamemory_metrics(query_results: Sequence[QueryResult]) -> dict[str, float]:
    """Aggregate metamemory counts across all queries."""
    counts: dict[str, float] = defaultdict(float)
    for result in query_results:
        for key, value in result.metrics.items():
            if key.startswith(("missing_knowledge_", "conflict_")) and key.endswith(
                ("_tp", "_fp", "_fn", "_tn")
            ):
                counts[key] += value
    metrics: dict[str, float] = {}
    metrics.update(aggregate_binary_metrics(counts, "missing_knowledge"))
    metrics.update(aggregate_binary_metrics(counts, "conflict"))
    return metrics
