"""Learning delta metrics."""

from __future__ import annotations

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.retrieval import mean_reciprocal_rank, recall_at_k


def first_relevant_rank(ranked_ids: tuple[str, ...], expected_ids: tuple[str, ...]) -> float:
    """Return the 1-based rank of the first relevant item, or 0 if missing."""
    if not expected_ids:
        return 0.0
    expected = set(expected_ids)
    for index, event_id in enumerate(ranked_ids, start=1):
        if event_id in expected:
            return float(index)
    return 0.0


def compute_learning_deltas(
    pre: QueryResult,
    post: QueryResult,
    *,
    k: int,
) -> dict[str, float]:
    """Compute learning deltas between paired queries."""
    pre_recall = recall_at_k(pre.retrieved_event_ids, pre.expected_event_ids, k=k)
    post_recall = recall_at_k(post.retrieved_event_ids, post.expected_event_ids, k=k)
    pre_mrr = mean_reciprocal_rank(pre.retrieved_event_ids, pre.expected_event_ids)
    post_mrr = mean_reciprocal_rank(post.retrieved_event_ids, post.expected_event_ids)
    pre_rank = first_relevant_rank(pre.retrieved_event_ids, pre.expected_event_ids)
    post_rank = first_relevant_rank(post.retrieved_event_ids, post.expected_event_ids)
    delta_rank = 0.0
    if pre_rank > 0 and post_rank > 0:
        delta_rank = pre_rank - post_rank
    elif pre_rank == 0 and post_rank > 0:
        delta_rank = float(k)
    return {
        f"delta_recall@{k}": post_recall - pre_recall,
        "delta_mrr": post_mrr - pre_mrr,
        "delta_first_relevant_rank": delta_rank,
    }
