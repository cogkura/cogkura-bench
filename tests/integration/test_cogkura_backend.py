"""CogKura backend integration tests."""

import importlib.util

import pytest

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.models import AssessmentRequest, RetrievalRequest
from cogkurabench.runner import BenchmarkRunner

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cogkura") is None,
    reason="cogkura not installed",
)


@pytest.mark.asyncio
async def test_cogkura_maps_recall_to_event_ids() -> None:
    dataset = load_dataset("mini")
    backend = CogKuraBackend()
    await backend.reset()
    event = dataset.events[0]
    await backend.ingest([event])
    await backend.prepare(as_of=event.timestamp)
    response = await backend.retrieve(
        RetrievalRequest(
            query_id="direct-001",
            query="Which API framework was selected?",
            as_of=event.timestamp,
            limit=5,
        )
    )
    event_ids = [event_id for item in response.items for event_id in item.source_event_ids]
    assert event.id in event_ids


@pytest.mark.asyncio
async def test_cogkura_mini_run_has_no_future_leak() -> None:
    dataset = load_dataset("mini")
    backend = CogKuraBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    leak = next(item for item in result.query_results if item.query_id == "leak-001")
    assert "evt-014" not in leak.retrieved_event_ids


@pytest.mark.asyncio
async def test_cogkura_assess_is_available_for_metamemory() -> None:
    dataset = load_dataset("mini")
    backend = CogKuraBackend()
    await backend.reset()
    query = dataset.query_by_id()["meta-001"]
    for event in dataset.events:
        if event.timestamp <= query.timestamp:
            await backend.ingest([event])
    await backend.prepare(as_of=query.timestamp)
    assessment = await backend.assess(
        AssessmentRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            should_abstain=True,
        )
    )
    assert assessment is not None


@pytest.mark.asyncio
async def test_cogkura_ingest_writes_entity_ids_to_encoded_episodes() -> None:
    from datetime import UTC, datetime

    from cogkurabench.models import EventType, ProjectEvent

    backend = CogKuraBackend()
    await backend.reset()
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    event = ProjectEvent(
        id="helios-style-001",
        timestamp=timestamp,
        sequence=1,
        subject_id="project-helios",
        event_type=EventType.ARCHITECTURE_DECISION,
        content="PostgreSQL replaces DynamoDB as the authoritative charge ledger backing store.",
        entities=("postgresql", "charge-ledger"),
    )
    await backend.ingest([event])
    await backend.prepare(as_of=timestamp)
    memory = backend._memory
    assert memory is not None
    episodes = await memory.list_episodes(tenant_id="benchmark")
    assert len(episodes) == 1
    entity_ids = {entity.entity_id for entity in episodes[0].entities}
    assert "postgresql" in entity_ids
    assert "charge-ledger" in entity_ids


@pytest.mark.asyncio
async def test_cogkura_retrieve_does_not_record_access() -> None:
    from datetime import UTC, datetime

    from cogkurabench.models import EventType, ProjectEvent

    backend = CogKuraBackend()
    await backend.reset()
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    events = [
        ProjectEvent(
            id=f"evt-{index}",
            timestamp=timestamp,
            sequence=index,
            subject_id="project-helios",
            event_type=EventType.DOCUMENTATION,
            content=f"Ledger documentation variant {index} for PostgreSQL charge storage.",
            entities=("charge-ledger",),
        )
        for index in range(1, 4)
    ]
    await backend.ingest(events)
    await backend.prepare(as_of=timestamp)
    memory = backend._memory
    assert memory is not None
    access_calls = 0
    original_record_access = memory.record_access

    async def counting_record_access(*args: object, **kwargs: object) -> object:
        nonlocal access_calls
        access_calls += 1
        return await original_record_access(*args, **kwargs)

    memory.record_access = counting_record_access  # type: ignore[method-assign]
    request = RetrievalRequest(
        query_id="retrieve-twice",
        query="Where is the charge ledger stored?",
        as_of=timestamp,
        limit=3,
        entity_ids=("charge-ledger",),
    )
    first = await backend.retrieve(request)
    second = await backend.retrieve(request)
    assert access_calls == 0
    first_ids = [item.source_event_ids[0] for item in first.items if item.source_event_ids]
    second_ids = [item.source_event_ids[0] for item in second.items if item.source_event_ids]
    assert first_ids == second_ids
