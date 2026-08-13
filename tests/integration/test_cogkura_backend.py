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
