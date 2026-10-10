"""Integration tests for persistent_inhibition_v1."""

from __future__ import annotations

import importlib.util

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None


def test_persistent_inhibition_dataset_validates() -> None:
    assert validate_dataset("persistent_inhibition_v1") == []


@pytest.mark.asyncio
async def test_oracle_persistent_inhibition_reports_na() -> None:
    dataset = load_dataset("persistent_inhibition_v1")
    backend = create_backend("oracle", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    capability = result.capability_results[Capability.PERSISTENT_INHIBITION.value]
    primary = _primary_metric_name(Capability.PERSISTENT_INHIBITION)
    assert _format_metric_value(Capability.PERSISTENT_INHIBITION, primary, None) == "N/A"
    assert primary not in capability.metrics
    assert result.use_results == ()


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_cogkura_profiles_split_inhibition_capabilities() -> None:
    from cogkurabench.backends.cogkura import CogKuraBackend

    control = CogKuraBackend()
    recording = CogKuraBackend(inhibition_enabled=True, name="cogkura-inhibition-recording")
    applied = CogKuraBackend(
        inhibition_enabled=True,
        apply_inhibition=True,
        name="cogkura-inhibition",
    )
    assert control.capabilities.record_use is True
    assert control.capabilities.inhibition_traces is False
    assert control.capabilities.persistent_inhibition is False
    assert recording.capabilities.inhibition_traces is True
    assert recording.capabilities.persistent_inhibition is False
    assert applied.capabilities.persistent_inhibition is True
    assert applied.capabilities.transient_interference is False


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_control_profile_omits_effect_metrics() -> None:
    dataset = load_dataset("persistent_inhibition_v1")
    backend = create_backend("cogkura", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    capability = result.capability_results[Capability.PERSISTENT_INHIBITION.value]
    assert "persistent_inhibition_effect_f1" not in capability.metrics
    assert "inhibition_trace_f1" not in capability.metrics
    assert result.use_results == ()


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_recording_profile_scores_traces_not_effects() -> None:
    dataset = load_dataset("persistent_inhibition_v1")
    backend = create_backend("cogkura-inhibition-recording", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    capability = result.capability_results[Capability.PERSISTENT_INHIBITION.value]
    assert "persistent_inhibition_effect_f1" not in capability.metrics
    assert result.use_results
    assert "inhibition_trace_f1" in capability.metrics


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_applied_profile_maps_inhibition_diagnostics() -> None:
    dataset = load_dataset("persistent_inhibition_v1")
    backend = create_backend("cogkura-inhibition", dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    for query_result in result.query_results:
        cogkura_meta = query_result.backend_metadata.get("cogkura", {})
        assert cogkura_meta.get("persistent_inhibition_candidates_unmapped", 0) == 0
        assert cogkura_meta.get("persistent_inhibition_contributions_unmapped", 0) == 0
    for use_result in result.use_results:
        cogkura_meta = use_result.backend_metadata.get("cogkura", {})
        assert cogkura_meta.get("inhibition_traces_unmapped", 0) == 0
