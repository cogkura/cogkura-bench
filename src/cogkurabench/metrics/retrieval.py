"""Retrieval metrics for benchmark evaluation."""

from __future__ import annotations

import math
from collections.abc import Sequence

from cogkurabench.metrics.ranking import (
    item_has_any,
    item_is_forbidden,
    item_relevance_grade,
    order_retrieved_items,
    relevance_grade,
    sources_in_items,
    top_k_items,
)
from cogkurabench.models import BenchmarkQuery, RetrievedItem


def recall_at_k(
    ranked_ids: Sequence[str],
    expected_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of expected evidence retrieved in the top K event positions."""
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
    """Fraction of top-K event positions that are relevant."""
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
    """Reciprocal rank of the first expected evidence event position."""
    if not expected_ids:
        return 1.0
    expected = set(expected_ids)
    for index, event_id in enumerate(ranked_ids, start=1):
        if event_id in expected:
            return 1.0 / index
    return 0.0


def ndcg_at_k(
    ranked_ids: Sequence[str],
    query: BenchmarkQuery,
    *,
    k: int,
) -> float:
    """Normalized discounted cumulative gain at K over event positions."""
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
    """Fraction of top-K event positions that are forbidden."""
    if not forbidden_ids or k <= 0:
        return 0.0
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    forbidden = set(forbidden_ids)
    hits = sum(1 for event_id in top_k if event_id in forbidden)
    return hits / len(top_k)


def group_recall_at_k(
    items: Sequence[RetrievedItem],
    expected_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of expected evidence found in the top K retrieved items."""
    if not expected_ids:
        return 1.0
    found = sources_in_items(top_k_items(items, k))
    hits = sum(1 for event_id in expected_ids if event_id in found)
    return hits / len(expected_ids)


def group_precision_at_k(
    items: Sequence[RetrievedItem],
    relevant_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items that cite relevant evidence."""
    if k <= 0:
        return 0.0
    top = top_k_items(items, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item_has_any(item, relevant_ids))
    return hits / len(top)


def group_mean_reciprocal_rank(
    items: Sequence[RetrievedItem],
    expected_ids: Sequence[str],
) -> float:
    """Reciprocal rank of the first retrieved item citing expected evidence."""
    if not expected_ids:
        return 1.0
    ordered = order_retrieved_items(items)
    for index, item in enumerate(ordered, start=1):
        if item_has_any(item, expected_ids):
            return 1.0 / index
    return 0.0


def group_ndcg_at_k(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
    *,
    k: int,
) -> float:
    """Normalized discounted cumulative gain at K over retrieved items."""
    ordered = order_retrieved_items(items)
    top = ordered[:k]
    if not top:
        return 0.0

    dcg = 0.0
    for index, item in enumerate(top, start=1):
        grade = item_relevance_grade(item, query)
        if grade > 0:
            dcg += grade / math.log2(index + 1)

    ideal_grades = sorted(
        [item_relevance_grade(item, query) for item in ordered],
        reverse=True,
    )[:k]
    idcg = 0.0
    for index, grade in enumerate(ideal_grades, start=1):
        if grade > 0:
            idcg += grade / math.log2(index + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def group_forbidden_intrusion_rate(
    items: Sequence[RetrievedItem],
    forbidden_ids: Sequence[str],
    *,
    k: int,
) -> float:
    """Fraction of top-K retrieved items citing forbidden evidence."""
    if not forbidden_ids or k <= 0:
        return 0.0
    top = top_k_items(items, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item_is_forbidden(item, forbidden_ids))
    return hits / len(top)


def compute_group_retrieval_metrics(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute grouped retrieval metrics for one query."""
    relevant_ids = tuple(
        dict.fromkeys([*query.expected_evidence_ids, *query.acceptable_evidence_ids])
    )
    metrics: dict[str, float] = {
        "mrr": group_mean_reciprocal_rank(items, query.expected_evidence_ids),
        "forbidden_intrusion_rate": group_forbidden_intrusion_rate(
            items,
            query.forbidden_evidence_ids,
            k=query.retrieval_limit,
        ),
    }
    for k in (1, 3, 5, 10):
        metrics[f"recall@{k}"] = group_recall_at_k(
            items,
            query.expected_evidence_ids,
            k=k,
        )
        metrics[f"precision@{k}"] = group_precision_at_k(
            items,
            relevant_ids,
            k=k,
        )
        metrics[f"ndcg@{k}"] = group_ndcg_at_k(items, query, k=k)
    return metrics


def compute_retrieval_metrics(
    items: Sequence[RetrievedItem],
    query: BenchmarkQuery,
) -> dict[str, float]:
    """Compute grouped retrieval metrics for one query."""
    ordered = order_retrieved_items(items)
    return compute_group_retrieval_metrics(ordered, query)
