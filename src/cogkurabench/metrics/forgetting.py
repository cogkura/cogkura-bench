"""Forgetting metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from cogkurabench.metrics.ranking import (
    item_is_forbidden,
    order_retrieved_items,
    top_k_items,
)
from cogkurabench.metrics.retrieval import group_recall_at_k
from cogkurabench.models import BenchmarkQuery, ProjectEvent, RetrievedItem


def stale_suppression_rate(
    items: Sequence[RetrievedItem],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items where forbidden stale evidence is absent."""
    if not forbidden_ids or k <= 0:
        return 1.0
    top = top_k_items(items, k)
    if not top:
        return 1.0
    suppressed = sum(1 for item in top if not item_is_forbidden(item, forbidden_ids))
    return suppressed / len(top)


def noise_intrusion_rate(
    items: Sequence[RetrievedItem],
    events_by_id: Mapping[str, ProjectEvent],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items citing at least one noise-tagged event."""
    top = top_k_items(items, k)
    if not top:
        return 0.0
    noise_hits = sum(
        1
        for item in top
        if any(
            event_id in events_by_id and "noise" in events_by_id[event_id].tags
            for event_id in item.source_event_ids
        )
    )
    return noise_hits / len(top)


def compute_forgetting_metrics(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
    *,
    events_by_id: Mapping[str, ProjectEvent],
) -> dict[str, float]:
    """Compute forgetting metrics for one query."""
    if query.capability.value != "forgetting":
        return {}
    ordered = order_retrieved_items(items)
    limit = query.retrieval_limit
    return {
        "stale_suppression_rate": stale_suppression_rate(
            ordered,
            query.forbidden_evidence_ids,
            k=limit,
        ),
        "relevant_long_term_retention": group_recall_at_k(
            ordered,
            query.expected_evidence_ids,
            k=limit,
        ),
        "noise_intrusion_rate": noise_intrusion_rate(
            ordered,
            events_by_id,
            k=limit,
        ),
    }
