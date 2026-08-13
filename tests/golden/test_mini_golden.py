"""Golden benchmark expectations for the mini dataset."""

import json
from pathlib import Path

import pytest

from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.runner import BenchmarkRunner

GOLDEN_DIR = Path(__file__).resolve().parent / "mini"


@pytest.mark.asyncio
async def test_oracle_golden_retrievals() -> None:
    dataset = load_dataset("mini")
    backend = OracleBackend(dataset.queries, dataset.events)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)

    actual = {
        qr.query_id: list(qr.retrieved_event_ids)
        for qr in result.query_results
        if qr.expected_event_ids
    }
    expected_path = GOLDEN_DIR / "oracle_retrievals.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert actual == expected


@pytest.mark.asyncio
async def test_token_overlap_golden_top_retrievals() -> None:
    dataset = load_dataset("mini")
    backend = TokenOverlapBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)

    actual = {qr.query_id: list(qr.retrieved_event_ids[:3]) for qr in result.query_results}
    expected_path = GOLDEN_DIR / "token_overlap_top3.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert actual == expected
