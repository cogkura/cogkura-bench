"""Integration tests for transient_interference_v1."""

from __future__ import annotations

import importlib.util

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None


def test_transient_interference_dataset_validates() -> None:
    assert validate_dataset("transient_interference_v1") == []


@pytest.mark.asyncio
async def test_oracle_transient_interference_reports_na() -> None:
    dataset = load_dataset("transient_interference_v1")
    backend = create_backend("oracle", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    capability = result.capability_results[Capability.TRANSIENT_INTERFERENCE.value]
    primary = _primary_metric_name(Capability.TRANSIENT_INTERFERENCE)
    assert _format_metric_value(Capability.TRANSIENT_INTERFERENCE, primary, None) == "N/A"
    assert primary not in capability.metrics


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_control_profile_reports_na_behavioural_metrics() -> None:
    dataset = load_dataset("transient_interference_v1")
    backend = create_backend("cogkura", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    for query_result in result.query_results:
        assert not query_result.transient_interference_observations
        assert "interference_effect_f1" not in query_result.metrics


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_interference_unmapped_contributions_are_zero() -> None:
    dataset = load_dataset("transient_interference_v1")
    backend = create_backend("cogkura-interference", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    for query_result in result.query_results:
        cogkura_meta = query_result.backend_metadata.get("cogkura", {})
        assert cogkura_meta.get("interference_contributions_unmapped", 0) == 0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_interference_profiles_are_distinct() -> None:
    from cogkurabench.backends.cogkura import CogKuraBackend

    control = CogKuraBackend()
    enabled = CogKuraBackend(apply_interference=True)
    assert control.name == "cogkura"
    assert enabled.name == "cogkura-interference"
    assert control.capabilities.transient_interference is False
    assert enabled.capabilities.transient_interference is True
