"""Retrieval parity checks for CogKura 0.17.0 against captured 0.16.4 fingerprints."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None
FINGERPRINTS_PATH = Path(__file__).resolve().parent / "cogkura_0164_retrieval_parity.json"


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_mini_cogkura_retrieval_parity_with_0164_baseline() -> None:
    fingerprints = json.loads(FINGERPRINTS_PATH.read_text(encoding="utf-8"))
    dataset = load_dataset("mini")
    backend = create_backend("cogkura", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)

    for query_result in result.query_results:
        expected = fingerprints["mini"].get(query_result.query_id)
        if expected is None:
            continue
        assert list(query_result.retrieved_event_ids) == expected["retrieved_event_ids"]
        actual_ranks = [
            [item.rank, list(item.source_event_ids)] for item in query_result.retrieved_items
        ]
        assert actual_ranks == expected["ranks"]
