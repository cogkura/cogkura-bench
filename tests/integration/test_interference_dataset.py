"""Integration tests for the interference_v1 dataset."""

from __future__ import annotations

import importlib.util

import pytest

from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None


def test_interference_dataset_validates() -> None:
    assert validate_dataset("interference_v1") == []


@pytest.mark.asyncio
async def test_oracle_interference_reports_na_competition_metrics() -> None:
    dataset = load_dataset("interference_v1")
    backend = OracleBackend(dataset.queries, dataset.events)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    interference = result.capability_results[Capability.INTERFERENCE.value]
    primary = _primary_metric_name(Capability.INTERFERENCE)
    assert _format_metric_value(Capability.INTERFERENCE, primary, None) == "N/A"
    assert primary not in interference.metrics


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_interference_unmapped_pairs_are_zero() -> None:
    dataset = load_dataset("interference_v1")
    backend = create_backend("cogkura", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    for query_result in result.query_results:
        cogkura_meta = query_result.backend_metadata.get("cogkura", {})
        assert cogkura_meta.get("competition_pairs_unmapped", 0) == 0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_competition_disabled_retrieval_parity() -> None:
    from cogkurabench.backends.cogkura import CogKuraBackend

    dataset = load_dataset("interference_v1")
    enabled = CogKuraBackend(competition_enabled=True)
    disabled = CogKuraBackend(competition_enabled=False)

    enabled_result = await BenchmarkRunner().run(dataset, enabled, write_results=False)
    disabled_result = await BenchmarkRunner().run(dataset, disabled, write_results=False)

    enabled_by_id = {result.query_id: result for result in enabled_result.query_results}
    for disabled_result_item in disabled_result.query_results:
        enabled_item = enabled_by_id[disabled_result_item.query_id]
        # Competition diagnostics must not change gold retrieval coverage. Exact
        # MRR / full ranked lists can differ across CogKura runs from tie
        # ordering, including two competition-enabled runs, so they are not
        # used as a competition-neutrality signal.
        assert disabled_result_item.metrics.get("recall@5") == enabled_item.metrics.get("recall@5")
        enabled_gold = set(enabled_item.retrieved_event_ids) & set(enabled_item.expected_event_ids)
        disabled_gold = set(disabled_result_item.retrieved_event_ids) & set(
            disabled_result_item.expected_event_ids
        )
        assert disabled_gold == enabled_gold
        assert not disabled_result_item.competition_observations
        assert enabled.capabilities.competition_diagnostics is True
        assert disabled.capabilities.competition_diagnostics is False
