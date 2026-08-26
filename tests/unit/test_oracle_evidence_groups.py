"""Oracle backend group-aware retrieval tests."""

import pytest

from cogkurabench.backends.oracle import OracleBackend, _oracle_retrieval_event_ids
from cogkurabench.dataset import load_dataset
from cogkurabench.models import EvidenceGroup, RetrievalRequest


@pytest.mark.asyncio
async def test_oracle_returns_one_event_per_expected_group() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    backend = OracleBackend(dataset.queries, dataset.events)
    query = dataset.query_by_id()["customer-waterproof-jacket"]
    response = await backend.retrieve(
        RetrievalRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            limit=50,
        )
    )
    retrieved_ids = {event_id for item in response.items for event_id in item.source_event_ids}
    for group in query.expected_evidence_groups:
        assert any(event_id in retrieved_ids for event_id in group.event_ids)
    assert len(response.items) >= len(query.expected_evidence_groups)


def test_oracle_event_id_order_prefers_group_first_ids() -> None:
    from datetime import UTC, datetime

    from cogkurabench.models import BenchmarkQuery, Capability

    query = BenchmarkQuery(
        id="q",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        capability=Capability.WORKING_MEMORY,
        query="test",
        expected_evidence_ids=("flat-a", "flat-b"),
        expected_evidence_groups=(
            EvidenceGroup(id="g1", label="G1", event_ids=("group-a", "group-a-alt")),
            EvidenceGroup(id="g2", label="G2", event_ids=("group-b",)),
        ),
    )
    ordered = _oracle_retrieval_event_ids(query)
    assert ordered[:3] == ("group-a", "group-b", "flat-a")
    assert "group-a-alt" not in ordered
    assert ordered[-1] == "flat-b"
