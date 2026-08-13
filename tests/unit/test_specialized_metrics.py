"""Specialized metric unit tests."""

from datetime import UTC, datetime

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.forgetting import compute_forgetting_metrics, stale_suppression_rate
from cogkurabench.metrics.learning import compute_learning_deltas, first_relevant_rank
from cogkurabench.metrics.metamemory import aggregate_binary_metrics, missing_knowledge_detection
from cogkurabench.metrics.temporal import temporal_accuracy
from cogkurabench.metrics.updating import current_state_ranking_score, stale_intrusion_rate
from cogkurabench.metrics.working_memory import evidence_coverage_at_budget
from cogkurabench.models import BenchmarkQuery, Capability, EventType, ProjectEvent


def _query(**kwargs: object) -> BenchmarkQuery:
    timestamp = datetime(2026, 1, 10, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": "q",
        "timestamp": timestamp,
        "capability": Capability.DIRECT_RECALL,
        "query": "test",
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)  # type: ignore[arg-type]


def _event(event_id: str, *, tags: tuple[str, ...] = ()) -> ProjectEvent:
    return ProjectEvent(
        id=event_id,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        sequence=1,
        subject_id="project-atlas",
        event_type=EventType.IMPLEMENTATION,
        content="sample",
        tags=tags,
    )


def test_temporal_accuracy_hit() -> None:
    query = _query(expected_evidence_ids=("evt-a",), capability=Capability.TEMPORAL_RECALL)
    assert temporal_accuracy(("evt-b", "evt-a"), query) == 1.0


def test_stale_intrusion_rate() -> None:
    assert stale_intrusion_rate(("evt-a", "evt-b"), ("evt-b",), k=2) == 0.5


def test_current_state_ranking_prefers_new() -> None:
    query = _query(
        expected_evidence_ids=("new",),
        forbidden_evidence_ids=("old",),
        capability=Capability.KNOWLEDGE_UPDATE,
    )
    assert current_state_ranking_score(("new", "old"), query) == 1.0


def test_forgetting_metrics() -> None:
    query = _query(
        expected_evidence_ids=("keep",),
        forbidden_evidence_ids=("stale",),
        capability=Capability.FORGETTING,
    )
    metrics = compute_forgetting_metrics(
        ("keep", "noise"),
        query,
        events_by_id={
            "keep": _event("keep"),
            "noise": _event("noise", tags=("noise",)),
        },
    )
    assert metrics["relevant_long_term_retention"] == 1.0
    assert stale_suppression_rate(("keep",), ("stale",), k=1) == 1.0


def test_working_memory_coverage() -> None:
    assert evidence_coverage_at_budget(("evt-a", "evt-b"), ("evt-a",)) == 1.0


def test_learning_delta_recall() -> None:
    pre = QueryResult(
        query_id="pre",
        capability=Capability.LEARNING,
        retrieved_event_ids=("old",),
        expected_event_ids=("new", "old"),
        metrics={"recall@5": 0.5},
        latency_ms=1.0,
        context_tokens=None,
    )
    post = QueryResult(
        query_id="post",
        capability=Capability.LEARNING,
        retrieved_event_ids=("new", "old"),
        expected_event_ids=("new", "old"),
        metrics={"recall@5": 1.0},
        latency_ms=1.0,
        context_tokens=None,
    )
    deltas = compute_learning_deltas(pre, post, k=5)
    assert deltas["delta_recall@5"] == 0.5
    assert first_relevant_rank(("new", "old"), ("new",)) == 1.0


def test_metamemory_aggregate() -> None:
    counts = {
        "missing_knowledge_tp": 2.0,
        "missing_knowledge_fp": 1.0,
        "missing_knowledge_fn": 0.0,
        "missing_knowledge_tn": 3.0,
    }
    metrics = aggregate_binary_metrics(counts, "missing_knowledge")
    assert metrics["missing_knowledge_precision"] == 2 / 3
    assert (
        missing_knowledge_detection(should_abstain=True, indicates_missing_knowledge=True)[
            "missing_knowledge_tp"
        ]
        == 1.0
    )
