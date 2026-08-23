"""Grouped retrieval metric unit tests."""

from datetime import UTC, datetime

from cogkurabench.metrics.ranking import flatten_source_event_ids
from cogkurabench.metrics.retrieval import compute_retrieval_metrics, group_recall_at_k, recall_at_k
from cogkurabench.models import BenchmarkQuery, Capability, RetrievedItem


def _query(**kwargs: object) -> BenchmarkQuery:
    timestamp = datetime(2026, 1, 10, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": "q",
        "timestamp": timestamp,
        "capability": Capability.DIRECT_RECALL,
        "query": "test",
        "retrieval_limit": 5,
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)  # type: ignore[arg-type]


def _item(source_ids: tuple[str, ...], rank: int) -> RetrievedItem:
    return RetrievedItem(
        source_event_ids=source_ids,
        text="sample",
        score=0.5,
        rank=rank,
        memory_type="episode",
    )


def test_group_recall_counts_item_not_flattened_position() -> None:
    items = (
        _item(("evt-1", "evt-2"), 1),
        _item(("evt-3", "evt-4"), 2),
        _item(("evt-5", "evt-6"), 3),
        _item(("evt-7", "evt-8"), 4),
        _item(("gold", "evt-9"), 5),
    )
    assert group_recall_at_k(items, ("gold",), k=5) == 1.0
    ranked = flatten_source_event_ids(items)
    assert ranked.index("gold") == 8
    assert recall_at_k(ranked, ("gold",), k=5) == 0.0


def test_compute_retrieval_metrics_returns_grouped_scores() -> None:
    items = (_item(("evt-a",), 1), _item(("evt-b",), 2))
    query = _query(expected_evidence_ids=("evt-a",))
    metrics = compute_retrieval_metrics(items, query)
    assert metrics["recall@5"] == 1.0
    assert "mrr" in metrics
