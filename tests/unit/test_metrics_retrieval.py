"""Retrieval metric unit tests with hand-calculated expectations."""

from datetime import UTC, datetime

from cogkurabench.metrics.retrieval import (
    forbidden_intrusion_rate,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    retrieved_event_ids,
)
from cogkurabench.models import BenchmarkQuery, Capability


def _query(**kwargs: object) -> BenchmarkQuery:
    defaults = {
        "id": "q-test",
        "timestamp": "2026-01-10T10:00:00+00:00",
        "capability": Capability.DIRECT_RECALL,
        "query": "test",
    }
    defaults.update(kwargs)

    timestamp = defaults["timestamp"]
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp).replace(tzinfo=UTC)
    return BenchmarkQuery(
        id=str(defaults["id"]),
        timestamp=timestamp,
        capability=defaults["capability"],  # type: ignore[arg-type]
        query=str(defaults["query"]),
        expected_evidence_ids=tuple(defaults.get("expected_evidence_ids", ())),  # type: ignore[arg-type]
        acceptable_evidence_ids=tuple(defaults.get("acceptable_evidence_ids", ())),  # type: ignore[arg-type]
        forbidden_evidence_ids=tuple(defaults.get("forbidden_evidence_ids", ())),  # type: ignore[arg-type]
    )


def test_recall_at_k_half_match() -> None:
    ranked = ("evt-a", "evt-b", "evt-c")
    assert recall_at_k(ranked, ("evt-a", "evt-d"), k=3) == 0.5


def test_precision_at_k() -> None:
    ranked = ("evt-a", "evt-b", "evt-c")
    assert precision_at_k(ranked, ("evt-a", "evt-c"), k=3) == 2 / 3


def test_mrr_first_position() -> None:
    assert mean_reciprocal_rank(("evt-x", "evt-y"), ("evt-x",)) == 1.0


def test_mrr_second_position() -> None:
    assert mean_reciprocal_rank(("evt-y", "evt-x"), ("evt-x",)) == 0.5


def test_ndcg_expected_weighting() -> None:
    query = _query(
        expected_evidence_ids=("evt-b",),
        acceptable_evidence_ids=("evt-c",),
    )
    ranked = ("evt-a", "evt-b", "evt-c")
    # dcg = 2/log2(3) + 1/log2(4); ideal swaps b and c to front
    assert ndcg_at_k(ranked, query, k=3) < 1.0
    ideal_ranked = ("evt-b", "evt-c", "evt-a")
    assert ndcg_at_k(ideal_ranked, query, k=3) == 1.0


def test_forbidden_intrusion_rate() -> None:
    ranked = ("evt-a", "evt-b", "evt-c")
    assert forbidden_intrusion_rate(ranked, ("evt-b",), k=3) == 1 / 3


def test_retrieved_event_ids_deduplicates() -> None:
    assert retrieved_event_ids(("evt-a", "evt-a", "evt-b")) == ("evt-a", "evt-b")
