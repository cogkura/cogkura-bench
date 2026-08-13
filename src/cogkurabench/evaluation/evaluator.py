"""Benchmark evaluation and aggregation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from cogkurabench.evaluation.result import CapabilityResult, QueryResult
from cogkurabench.models import BenchmarkQuery, Capability


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
        averaged = {
            name: sum(result.metrics[name] for result in results) / len(results)
            for name in metric_names
        }
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
    context_tokens: int | None = None,
    backend_metadata: dict[str, object] | None = None,
) -> QueryResult:
    """Score one query against retrieved event IDs."""
    from cogkurabench.metrics.retrieval import compute_retrieval_metrics

    metrics = compute_retrieval_metrics(ranked_event_ids, query)
    return QueryResult(
        query_id=query.id,
        capability=query.capability,
        retrieved_event_ids=tuple(ranked_event_ids),
        expected_event_ids=query.expected_evidence_ids,
        metrics=metrics,
        latency_ms=latency_ms,
        context_tokens=context_tokens,
        backend_metadata=backend_metadata or {},
    )
