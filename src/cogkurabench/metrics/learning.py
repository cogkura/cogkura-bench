"""Learning delta metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.ranking import order_retrieved_items
from cogkurabench.metrics.retrieval import group_mean_reciprocal_rank, group_recall_at_k
from cogkurabench.models import RetrievedItem


def first_relevant_rank(
    items: Sequence[RetrievedItem],
    expected_ids: tuple[str, ...],
) -> float:
    """Return the 1-based item rank of the first relevant retrieved item."""
    if not expected_ids:
        return 0.0
    ordered = order_retrieved_items(items)
    for index, item in enumerate(ordered, start=1):
        if any(event_id in expected_ids for event_id in item.source_event_ids):
            return float(index)
    return 0.0


def _delta_first_relevant_rank(
    pre_rank: float,
    post_rank: float,
    *,
    k: int,
) -> float:
    if pre_rank > 0 and post_rank > 0:
        return pre_rank - post_rank
    if pre_rank == 0 and post_rank > 0:
        return float(k)
    return 0.0


def compute_learning_deltas(
    pre: QueryResult,
    post: QueryResult,
    *,
    k: int,
) -> dict[str, float]:
    """Compute grouped learning deltas between paired queries."""
    pre_items = order_retrieved_items(pre.retrieved_items)
    post_items = order_retrieved_items(post.retrieved_items)
    pre_recall = group_recall_at_k(pre_items, pre.expected_event_ids, k=k)
    post_recall = group_recall_at_k(post_items, post.expected_event_ids, k=k)
    pre_mrr = group_mean_reciprocal_rank(pre_items, pre.expected_event_ids)
    post_mrr = group_mean_reciprocal_rank(post_items, post.expected_event_ids)
    pre_rank = first_relevant_rank(pre_items, pre.expected_event_ids)
    post_rank = first_relevant_rank(post_items, post.expected_event_ids)

    return {
        f"delta_recall@{k}": post_recall - pre_recall,
        "delta_mrr": post_mrr - pre_mrr,
        "delta_first_relevant_rank": _delta_first_relevant_rank(pre_rank, post_rank, k=k),
    }
