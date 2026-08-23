"""Evaluator grouped scoring regression tests."""

from datetime import UTC, datetime

from cogkurabench.evaluation.evaluator import evaluate_query
from cogkurabench.models import BenchmarkQuery, Capability, RetrievedItem


def _query(**kwargs: object) -> BenchmarkQuery:
    timestamp = datetime(2026, 1, 10, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": "q",
        "timestamp": timestamp,
        "capability": Capability.DIRECT_RECALL,
        "query": "test",
        "expected_evidence_ids": ("gold",),
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


def test_grouped_top5_hit_when_gold_in_item_five() -> None:
    items = (
        _item(("evt-1", "evt-2"), 1),
        _item(("evt-3", "evt-4"), 2),
        _item(("evt-5", "evt-6"), 3),
        _item(("evt-7", "evt-8"), 4),
        _item(("gold", "evt-9"), 5),
    )
    result = evaluate_query(_query(), items, latency_ms=1.0)
    assert result.metrics["recall@5"] == 1.0
    assert "gold" in result.retrieved_event_ids
