"""Knowledge-update metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.metrics.ranking import (
    item_has_any,
    item_is_forbidden,
    order_retrieved_items,
    top_k_items,
)
from cogkurabench.metrics.retrieval import group_recall_at_k
from cogkurabench.models import BenchmarkQuery, RetrievedItem


def group_stale_intrusion_rate(
    items: Sequence[RetrievedItem],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items citing forbidden stale evidence."""
    if not forbidden_ids or k <= 0:
        return 0.0
    top = top_k_items(items, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item_is_forbidden(item, forbidden_ids))
    return hits / len(top)


def group_current_state_ranking_score(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
) -> float:
    """Score new-vs-old ranking over retrieved items."""
    if not query.expected_evidence_ids or not query.forbidden_evidence_ids:
        return 1.0
    ordered = order_retrieved_items(items)
    new_ranks: list[int] = []
    old_ranks: list[int] = []
    for index, item in enumerate(ordered, start=1):
        has_expected = item_has_any(item, query.expected_evidence_ids)
        has_forbidden = item_is_forbidden(item, query.forbidden_evidence_ids)
        if has_expected and not has_forbidden:
            new_ranks.append(index)
        if has_forbidden:
            old_ranks.append(index)
    if not new_ranks:
        return 0.0
    if not old_ranks:
        return 1.0
    return 1.0 if min(new_ranks) < min(old_ranks) else 0.0


def compute_update_metrics(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute knowledge-update metrics for one query."""
    if query.capability.value != "knowledge_update":
        return {}
    ordered = order_retrieved_items(items)
    limit = query.retrieval_limit
    return {
        "updated_evidence_recall": group_recall_at_k(
            ordered,
            query.expected_evidence_ids,
            k=limit,
        ),
        "stale_intrusion_rate": group_stale_intrusion_rate(
            ordered,
            query.forbidden_evidence_ids,
            k=limit,
        ),
        "current_state_ranking": group_current_state_ranking_score(ordered, query),
    }
