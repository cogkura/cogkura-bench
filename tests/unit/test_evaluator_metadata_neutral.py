"""Evaluator scoring invariants for backend metadata."""

from datetime import UTC, datetime

from cogkurabench.evaluation.evaluator import aggregate_capability_results, evaluate_query
from cogkurabench.models import (
    AssessmentResponse,
    BenchmarkQuery,
    Capability,
    ContextResponse,
    RetrievedItem,
)


def _query(**kwargs: object) -> BenchmarkQuery:
    timestamp = datetime(2026, 1, 10, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": "q",
        "timestamp": timestamp,
        "capability": Capability.DIRECT_RECALL,
        "query": "test",
        "expected_evidence_ids": ("evt-a",),
        "forbidden_evidence_ids": ("evt-b",),
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)  # type: ignore[arg-type]


def _item(
    *,
    event_id: str,
    rank: int,
    metadata: dict[str, object],
) -> RetrievedItem:
    return RetrievedItem(
        source_event_ids=(event_id,),
        text="sample text",
        score=0.5,
        rank=rank,
        memory_type="episode",
        metadata=metadata,
    )


def test_evaluate_query_metrics_ignore_backend_metadata() -> None:
    query = _query()
    ranked_ids = ("evt-a", "evt-c")
    base_metadata = {"diagnostic": "baseline"}
    rich_metadata = {"diagnostic": "different", "activation": 99.0, "slot_fit": 0.0}

    base = evaluate_query(
        query,
        ranked_ids,
        latency_ms=1.0,
        backend_metadata=base_metadata,
        retrieved_items=(
            _item(event_id="evt-a", rank=1, metadata=base_metadata),
            _item(event_id="evt-c", rank=2, metadata={}),
        ),
    )
    rich = evaluate_query(
        query,
        ranked_ids,
        latency_ms=1.0,
        backend_metadata=rich_metadata,
        retrieved_items=(
            _item(event_id="evt-a", rank=1, metadata=rich_metadata),
            _item(event_id="evt-c", rank=2, metadata={"activation": -1.0}),
        ),
    )
    assert base.metrics == rich.metrics


def test_working_memory_metrics_ignore_item_metadata() -> None:
    query = _query(
        capability=Capability.WORKING_MEMORY,
        expected_evidence_ids=("evt-a", "evt-b"),
        prompt_budget_tokens=100,
    )
    context = ContextResponse(
        items=(
            _item(event_id="evt-a", rank=1, metadata={"activation": 1.0}),
            _item(event_id="evt-b", rank=2, metadata={"activation": 2.0}),
        ),
        estimated_tokens=42,
        latency_ms=2.0,
    )
    alternate_context = ContextResponse(
        items=(
            _item(event_id="evt-a", rank=1, metadata={"slot_fit": 0.0}),
            _item(event_id="evt-b", rank=2, metadata={"slot_fit": 1.0}),
        ),
        estimated_tokens=42,
        latency_ms=2.0,
    )
    base = evaluate_query(
        query,
        ("evt-a", "evt-b"),
        latency_ms=1.0,
        context_response=context,
        context_items=context.items,
    )
    alternate = evaluate_query(
        query,
        ("evt-a", "evt-b"),
        latency_ms=1.0,
        context_response=alternate_context,
        context_items=alternate_context.items,
    )
    assert base.metrics == alternate.metrics


def test_capability_aggregation_ignores_backend_metadata() -> None:
    query = _query()
    base = evaluate_query(
        query,
        ("evt-a",),
        latency_ms=1.0,
        backend_metadata={"note": "a"},
        retrieved_items=(_item(event_id="evt-a", rank=1, metadata={"note": "a"}),),
    )
    rich = evaluate_query(
        query,
        ("evt-a",),
        latency_ms=1.0,
        backend_metadata={"note": "b", "activation": 5.0},
        retrieved_items=(_item(event_id="evt-a", rank=1, metadata={"activation": 5.0}),),
    )
    base_caps = aggregate_capability_results([base])
    rich_caps = aggregate_capability_results([rich])
    assert base_caps == rich_caps


def test_metamemory_metrics_ignore_retrieved_item_metadata() -> None:
    query = _query(
        capability=Capability.METAMEMORY,
        should_abstain=True,
        expected_evidence_ids=(),
    )
    assessment = AssessmentResponse(
        indicates_missing_knowledge=True,
        indicates_conflict=False,
        latency_ms=1.0,
        flags=("missing_knowledge",),
    )
    base = evaluate_query(
        query,
        (),
        latency_ms=1.0,
        assessment_response=assessment,
        retrieved_items=(_item(event_id="evt-a", rank=1, metadata={}),),
    )
    rich = evaluate_query(
        query,
        (),
        latency_ms=1.0,
        assessment_response=assessment,
        retrieved_items=(_item(event_id="evt-a", rank=1, metadata={"activation": 9.9}),),
    )
    assert base.metrics == rich.metrics
