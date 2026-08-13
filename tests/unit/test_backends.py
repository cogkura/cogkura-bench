"""Backend behaviour tests."""

import pytest

from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend, overlap_score, tokenize
from cogkurabench.dataset import load_dataset
from cogkurabench.models import RetrievalRequest


def test_tokenize_lowercase_alphanumeric() -> None:
    assert tokenize("FastAPI-2.0 endpoints") == {"fastapi", "2", "0", "endpoints"}


def test_overlap_score_partial() -> None:
    assert overlap_score("redis coordination", "Redis was selected for coordination") == 1.0


@pytest.mark.asyncio
async def test_token_overlap_ranks_matching_event_first() -> None:
    dataset = load_dataset("mini")
    backend = TokenOverlapBackend()
    await backend.reset()
    await backend.ingest(dataset.events)

    query = dataset.query_by_id()["direct-001"]
    response = await backend.retrieve(
        RetrievalRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            limit=5,
        )
    )
    top_ids = [event_id for item in response.items for event_id in item.source_event_ids]
    assert top_ids[0] == "evt-001"


@pytest.mark.asyncio
async def test_oracle_returns_expected_evidence() -> None:
    dataset = load_dataset("mini")
    backend = OracleBackend(dataset.queries, dataset.events)
    query = dataset.query_by_id()["direct-001"]
    response = await backend.retrieve(
        RetrievalRequest(
            query_id=query.id,
            query=query.query,
            as_of=query.timestamp,
            limit=5,
        )
    )
    retrieved = [event_id for item in response.items for event_id in item.source_event_ids]
    assert retrieved == ["evt-001"]
