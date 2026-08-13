"""Temporal recall metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.models import BenchmarkQuery


def temporal_accuracy(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
    *,
    k: int | None = None,
) -> float:
    """Return 1.0 when expected evidence appears in top-K, else 0.0."""
    if not query.expected_evidence_ids:
        return 1.0 if query.should_abstain else 0.0
    limit = k if k is not None else query.retrieval_limit
    top_k = set(ranked_ids[:limit])
    return 1.0 if any(event_id in top_k for event_id in query.expected_evidence_ids) else 0.0


def compute_temporal_metrics(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute temporal metrics for one query."""
    if query.capability.value != "temporal_recall":
        return {}
    if query.valid_at is not None:
        return {"temporal_historical_accuracy": temporal_accuracy(ranked_ids, query)}
    return {"temporal_current_accuracy": temporal_accuracy(ranked_ids, query)}
