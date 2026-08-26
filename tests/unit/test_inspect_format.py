"""Inspect formatting unit tests."""

from datetime import UTC, datetime

from cogkurabench.evaluation.result import (
    EvidenceGroupDiagnosticResult,
    QueryResult,
)
from cogkurabench.inspect_format import (
    format_evidence_groups_section,
    format_query_inspection,
    format_retrieved_item,
)
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    EventType,
    ProjectEvent,
    RetrievedItem,
)


def test_format_retrieved_item_includes_metadata() -> None:
    item = RetrievedItem(
        source_event_ids=("evt-001",),
        text="PostgreSQL ledger",
        score=0.87,
        rank=2,
        memory_type="semantic",
        metadata={"activation": 1.5, "temporal_mode": "current"},
    )
    rendered = format_retrieved_item(item)
    assert "Rank 2" in rendered
    assert "evt-001" in rendered
    assert "activation: 1.5" in rendered
    assert "temporal_mode: current" in rendered


def test_format_query_inspection_includes_cue_and_gold_fields() -> None:
    timestamp = datetime(2026, 2, 17, 10, tzinfo=UTC)
    query = BenchmarkQuery(
        id="helios-update-001",
        timestamp=timestamp,
        capability=Capability.KNOWLEDGE_UPDATE,
        query="Where do finalized charges persist in production now?",
        expected_evidence_ids=("helios-012",),
        acceptable_evidence_ids=("helios-015",),
        forbidden_evidence_ids=("helios-002",),
        entity_ids=("charge-ledger",),
    )
    event = ProjectEvent(
        id="helios-012",
        timestamp=timestamp,
        sequence=1,
        subject_id="project-helios",
        event_type=EventType.DOCUMENTATION,
        content="PostgreSQL ledger documentation",
    )
    query_result = QueryResult(
        query_id=query.id,
        capability=query.capability,
        retrieved_event_ids=("helios-012",),
        retrieved_items=(
            RetrievedItem(
                source_event_ids=("helios-012",),
                text="PostgreSQL ledger documentation",
                score=0.9,
                rank=1,
                memory_type="episode",
                metadata={"activation": 2.1},
            ),
        ),
        expected_event_ids=query.expected_evidence_ids,
        metrics={"recall@5": 1.0},
        latency_ms=1.0,
        context_tokens=None,
    )
    rendered = format_query_inspection(query, query_result, {event.id: event})
    assert "Query id: helios-update-001" in rendered
    assert "Entity ids: charge-ledger" in rendered
    assert "Expected evidence:" in rendered
    assert "Acceptable evidence:" in rendered
    assert "Forbidden evidence:" in rendered
    assert "helios-012" in rendered
    assert "helios-002" in rendered
    assert "Retrieved items:" in rendered


def test_format_evidence_groups_section() -> None:
    query_result = QueryResult(
        query_id="customer-waterproof-jacket",
        capability=Capability.WORKING_MEMORY,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics={},
        latency_ms=1.0,
        context_tokens=100,
        evidence_group_diagnostics=(
            EvidenceGroupDiagnosticResult(
                group_id="hiking_interest",
                label="Established hiking interest",
                retrieval_present=True,
                context_present=True,
                first_retrieval_rank=1,
                first_context_rank=1,
                stage="selected",
            ),
            EvidenceGroupDiagnosticResult(
                group_id="lightweight_preference",
                label="Prefers lightweight outerwear",
                retrieval_present=True,
                context_present=False,
                first_retrieval_rank=14,
                first_context_rank=None,
                stage="selection_drop",
            ),
        ),
    )
    rendered = format_evidence_groups_section(query_result)
    assert "Evidence groups" in rendered
    assert "Established hiking interest" in rendered
    assert "selection_drop" in rendered
    assert "yes" in rendered
