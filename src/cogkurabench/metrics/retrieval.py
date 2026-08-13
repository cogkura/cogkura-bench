"""Retrieval metrics for benchmark evaluation."""

from __future__ import annotations

import math
from collections.abc import Sequence

from cogkurabench.models import BenchmarkQuery


def retrieved_event_ids(
    ranked_ids: Sequence[str],
    *,
    deduplicate: bool = True,
) -> tuple[str, ...]:
    """Flatten ranked retrieved event IDs preserving order."""
    if not deduplicate:
        return tuple(ranked_ids)
    seen: set[str] = set()
    ordered: list[str] = []
    for event_id in ranked_ids:
        if event_id not in seen:
            seen.add(event_id)
            ordered.append(event_id)
    return tuple(ordered)


def recall_at_k(
    ranked_ids: Sequence[str],
    expected_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of expected evidence retrieved in the top K positions."""
    if not expected_ids:
        return 1.0
    top_k = set(ranked_ids[:k])
    hits = sum(1 for event_id in expected_ids if event_id in top_k)
    return hits / len(expected_ids)


def precision_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items that are relevant."""
    if k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    relevant = set(relevant_ids)
    hits = sum(1 for event_id in top_k if event_id in relevant)
    return hits / len(top_k)


def mean_reciprocal_rank(
    ranked_ids: Sequence[str],
    expected_ids: Sequence[str],
) -> float:
    """Reciprocal rank of the first expected evidence item."""
    if not expected_ids:
        return 1.0
    expected = set(expected_ids)
    for index, event_id in enumerate(ranked_ids, start=1):
        if event_id in expected:
            return 1.0 / index
    return 0.0


def relevance_grade(
    event_id: str,
    query: BenchmarkQuery,
) -> int:
    """Return nDCG relevance grade for an event ID."""
    if event_id in query.expected_evidence_ids:
        return 2
    if event_id in query.acceptable_evidence_ids:
        return 1
    return 0


def ndcg_at_k(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
    *,
    k: int,
) -> float:
    """Normalized discounted cumulative gain at K."""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0

    dcg = 0.0
    for index, event_id in enumerate(top_k, start=1):
        grade = relevance_grade(event_id, query)
        if grade > 0:
            dcg += grade / math.log2(index + 1)

    ideal_grades = sorted(
        [relevance_grade(event_id, query) for event_id in ranked_ids],
        reverse=True,
    )[:k]
    idcg = 0.0
    for index, grade in enumerate(ideal_grades, start=1):
        if grade > 0:
            idcg += grade / math.log2(index + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def forbidden_intrusion_rate(
    ranked_ids: Sequence[str],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items that are forbidden."""
    if not forbidden_ids or k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    forbidden = set(forbidden_ids)
    hits = sum(1 for event_id in top_k if event_id in forbidden)
    return hits / len(top_k)


def compute_retrieval_metrics(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute standard retrieval metrics for one query."""
    relevant_ids = tuple(
        dict.fromkeys([*query.expected_evidence_ids, *query.acceptable_evidence_ids])
    )
    metrics: dict[str, float] = {
        "mrr": mean_reciprocal_rank(ranked_ids, query.expected_evidence_ids),
        "forbidden_intrusion_rate": forbidden_intrusion_rate(
            ranked_ids,
            query.forbidden_evidence_ids,
            k=query.retrieval_limit,
        ),
    }
    for k in (1, 3, 5, 10):
        metrics[f"recall@{k}"] = recall_at_k(
            ranked_ids,
            query.expected_evidence_ids,
            k=k,
        )
        metrics[f"precision@{k}"] = precision_at_k(
            ranked_ids,
            relevant_ids,
            k=k,
        )
        metrics[f"ndcg@{k}"] = ndcg_at_k(ranked_ids, query, k=k)
    return metrics
