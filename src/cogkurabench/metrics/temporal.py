"""Temporal recall metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.metrics.ranking import item_has_any, order_retrieved_items, top_k_items
from cogkurabench.models import BenchmarkQuery, RetrievedItem


def group_temporal_accuracy(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
    *,
    k: int | None = None,
) -> float:
    """Return 1.0 when expected evidence appears in top-K retrieved items."""
    if not query.expected_evidence_ids:
        return 1.0 if query.should_abstain else 0.0
    limit = k if k is not None else query.retrieval_limit
    top = top_k_items(items, limit)
    return 1.0 if any(item_has_any(item, query.expected_evidence_ids) for item in top) else 0.0


def compute_temporal_metrics(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute temporal metrics for one query."""
    if query.capability.value != "temporal_recall":
        return {}
    ordered = order_retrieved_items(items)
    if query.valid_at is not None:
        return {"temporal_historical_accuracy": group_temporal_accuracy(ordered, query)}
    return {"temporal_current_accuracy": group_temporal_accuracy(ordered, query)}
