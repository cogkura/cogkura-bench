"""Full-history backend tests."""

import pytest

from cogkurabench.backends.full_history import FullHistoryBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.models import RetrievalRequest


@pytest.mark.asyncio
async def test_full_history_returns_chronological_events() -> None:
    dataset = load_dataset("mini")
    backend = FullHistoryBackend()
    await backend.reset()
    await backend.ingest(dataset.events)

    query = dataset.query_by_id()["direct-001"]
    response = await backend.retrieve(
        RetrievalRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            limit=3,
        )
    )
    retrieved = [event_id for item in response.items for event_id in item.source_event_ids]
    assert retrieved == ["evt-001", "evt-002"]
