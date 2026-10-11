"""Integration tests for transient_interference_v2."""

from __future__ import annotations

import importlib.util

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None


def test_transient_interference_v2_validates() -> None:
    assert validate_dataset("transient_interference_v2") == []


@pytest.mark.asyncio
async def test_oracle_v2_reports_na() -> None:
    dataset = load_dataset("transient_interference_v2")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("oracle", dataset),
        write_results=False,
    )
    capability = result.capability_results[Capability.TRANSIENT_INTERFERENCE.value]
    primary = _primary_metric_name(Capability.TRANSIENT_INTERFERENCE)
    assert primary not in capability.metrics
    assert _format_metric_value(Capability.TRANSIENT_INTERFERENCE, primary, None) == "N/A"


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_control_profile_omits_transient_effect_metrics() -> None:
    dataset = load_dataset("transient_interference_v2")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("cogkura", dataset),
        write_results=False,
    )
    capability = result.capability_results[Capability.TRANSIENT_INTERFERENCE.value]
    assert "interference_effect_f1" not in capability.metrics


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_v2_interference_profile_meets_release_gate() -> None:
    dataset = load_dataset("transient_interference_v2")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("cogkura-interference", dataset),
        write_results=False,
    )
    metrics = result.capability_results[Capability.TRANSIENT_INTERFERENCE.value].metrics
    assert metrics["interference_effect_precision"] == 1.0
    assert metrics["interference_effect_recall"] == 1.0
    assert metrics["interference_effect_f1"] == 1.0
    assert metrics["interference_effect_direction_accuracy"] == 1.0
    assert metrics["unexpected_interference_rate"] == 0.0
    assert metrics["interference_effect_expected_matched"] > 0.0
    for key in (
        "positive_penalty_violation_count",
        "activation_increase_due_to_interference_count",
        "cotemporal_penalty_violation_count",
        "historical_future_interference_count",
    ):
        assert metrics[key] == 0.0
    for query_result in result.query_results:
        cogkura_meta = query_result.backend_metadata.get("cogkura", {})
        assert cogkura_meta.get("interference_contributions_unmapped", 0) == 0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_persistent_inhibition_gate_still_holds() -> None:
    dataset = load_dataset("persistent_inhibition_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("cogkura-inhibition", dataset),
        write_results=False,
    )
    metrics = result.capability_results[Capability.PERSISTENT_INHIBITION.value].metrics
    assert metrics["inhibition_trace_precision"] == 1.0
    assert metrics["inhibition_trace_recall"] == 1.0
    assert metrics["unexpected_inhibition_trace_rate"] == 0.0
    assert metrics["persistent_inhibition_effect_precision"] == 1.0
    assert metrics["persistent_inhibition_effect_recall"] == 1.0
    assert metrics["unexpected_persistent_inhibition_rate"] == 0.0
    assert metrics["persistent_inhibition_scope_isolation_accuracy"] == 1.0
    assert metrics["repetition_strengthening_accuracy"] == 1.0
    assert metrics["inhibition_recovery_order_accuracy"] == 1.0
    for key in (
        "positive_inhibition_penalty_violations",
        "activation_increase_due_to_inhibition",
        "out_of_scope_inhibition_count",
        "future_trace_visibility_count",
    ):
        assert metrics[key] == 0.0
