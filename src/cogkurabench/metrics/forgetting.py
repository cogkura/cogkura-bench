"""Forgetting metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from cogkurabench.metrics.retrieval import recall_at_k
from cogkurabench.models import BenchmarkQuery, ProjectEvent


def stale_suppression_rate(
    ranked_ids: Sequence[str],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K where forbidden stale evidence is absent."""
    if not forbidden_ids or k <= 0:
        return 1.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 1.0
    forbidden = set(forbidden_ids)
    suppressed = sum(1 for event_id in top_k if event_id not in forbidden)
    return suppressed / len(top_k)


def noise_intrusion_rate(
    ranked_ids: Sequence[str],
    events_by_id: Mapping[str, ProjectEvent],
    *,
    k: int,
) -> float:
    """Fraction of top-K results tagged as noise."""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    noise_hits = sum(
        1
        for event_id in top_k
        if event_id in events_by_id and "noise" in events_by_id[event_id].tags
    )
    return noise_hits / len(top_k)


def compute_forgetting_metrics(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
    *,
    events_by_id: Mapping[str, ProjectEvent],
) -> dict[str, float]:
    """Compute forgetting metrics for one query."""
    if query.capability.value != "forgetting":
        return {}
    return {
        "stale_suppression_rate": stale_suppression_rate(
            ranked_ids,
            query.forbidden_evidence_ids,
            k=query.retrieval_limit,
        ),
        "relevant_long_term_retention": recall_at_k(
            ranked_ids,
            query.expected_evidence_ids,
            k=query.retrieval_limit,
        ),
        "noise_intrusion_rate": noise_intrusion_rate(
            ranked_ids,
            events_by_id,
            k=query.retrieval_limit,
        ),
    }
