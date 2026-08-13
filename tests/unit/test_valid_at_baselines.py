"""Baseline valid_at visibility tests."""

import pytest

from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.models import RetrievalRequest


@pytest.mark.asyncio
async def test_token_overlap_respects_valid_at() -> None:
    dataset = load_dataset("mini")
    backend = TokenOverlapBackend()
    await backend.reset()
    await backend.ingest(dataset.events)
    query = dataset.query_by_id()["temporal-hist-001"]
    response = await backend.retrieve(
        RetrievalRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            limit=10,
            valid_at=query.valid_at,
        )
    )
    retrieved = [event_id for item in response.items for event_id in item.source_event_ids]
    assert "evt-008" not in retrieved
