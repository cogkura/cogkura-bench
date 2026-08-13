"""Knowledge-update metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.metrics.retrieval import recall_at_k
from cogkurabench.models import BenchmarkQuery


def stale_intrusion_rate(
    ranked_ids: Sequence[str],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K results that are forbidden stale evidence."""
    if not forbidden_ids or k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    forbidden = set(forbidden_ids)
    hits = sum(1 for event_id in top_k if event_id in forbidden)
    return hits / len(top_k)


def current_state_ranking_score(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
) -> float:
    """Score new-vs-old ranking: 1.0 when new expected outranks all forbidden."""
    if not query.expected_evidence_ids or not query.forbidden_evidence_ids:
        return 1.0
    new_ranks = [
        index + 1
        for index, event_id in enumerate(ranked_ids)
        if event_id in query.expected_evidence_ids
    ]
    old_ranks = [
        index + 1
        for index, event_id in enumerate(ranked_ids)
        if event_id in query.forbidden_evidence_ids
    ]
    if not new_ranks:
        return 0.0
    if not old_ranks:
        return 1.0
    return 1.0 if min(new_ranks) < min(old_ranks) else 0.0


def compute_update_metrics(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute knowledge-update metrics for one query."""
    if query.capability.value != "knowledge_update":
        return {}
    return {
        "updated_evidence_recall": recall_at_k(
            ranked_ids,
            query.expected_evidence_ids,
            k=query.retrieval_limit,
        ),
        "stale_intrusion_rate": stale_intrusion_rate(
            ranked_ids,
            query.forbidden_evidence_ids,
            k=query.retrieval_limit,
        ),
        "current_state_ranking": current_state_ranking_score(ranked_ids, query),
    }
