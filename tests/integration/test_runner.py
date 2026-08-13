"""Runner integration tests."""

import pytest

from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.runner import BenchmarkRunner


@pytest.mark.asyncio
async def test_oracle_recall_at_five_is_perfect() -> None:
    dataset = load_dataset("mini")
    backend = OracleBackend(dataset.queries, dataset.events)
    runner = BenchmarkRunner()
    result = await runner.run(dataset, backend, write_results=False)

    scored = [qr for qr in result.query_results if qr.expected_event_ids]
    assert scored
    assert all(qr.metrics["recall@5"] == 1.0 for qr in scored)


@pytest.mark.asyncio
async def test_future_event_not_retrieved_early() -> None:
    dataset = load_dataset("mini")
    backend = TokenOverlapBackend()
    runner = BenchmarkRunner()
    result = await runner.run(dataset, backend, write_results=False)

    leak_result = next(qr for qr in result.query_results if qr.query_id == "leak-001")
    assert "evt-014" not in leak_result.retrieved_event_ids
