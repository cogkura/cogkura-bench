"""Integration gates for the 0.3.8 persistent-inhibition workloads."""

from __future__ import annotations

import importlib.util

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.persistent_inhibition_workload import (
    summarize_persistent_inhibition_workload,
)
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None
_WORKLOADS = (
    "persistent_inhibition_software_v1",
    "persistent_inhibition_customer_v1",
)
_CO_CONSUMPTION = {
    "persistent_inhibition_software_v1": "sw-use-cache",
    "persistent_inhibition_customer_v1": "cu-use-traits",
}


def _signature(query_result: QueryResult) -> tuple[tuple[tuple[str, ...], float | None, int], ...]:
    return tuple(
        (item.source_event_ids, item.score, item.rank) for item in query_result.retrieved_items
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset_name", _WORKLOADS)
async def test_oracle_workload_effect_f1_is_na(dataset_name: str) -> None:
    dataset = load_dataset(dataset_name)
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("oracle", dataset),
        write_results=False,
    )
    capability = result.capability_results[Capability.PERSISTENT_INHIBITION.value]
    primary = _primary_metric_name(Capability.PERSISTENT_INHIBITION)
    assert primary not in capability.metrics
    assert _format_metric_value(Capability.PERSISTENT_INHIBITION, primary, None) == "N/A"
    assert result.use_results == ()


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize("dataset_name", _WORKLOADS)
async def test_workload_safety_gate(dataset_name: str) -> None:
    dataset = load_dataset(dataset_name)
    runner = BenchmarkRunner()
    control = await runner.run(dataset, create_backend("cogkura", dataset), write_results=False)
    recording = await runner.run(
        dataset,
        create_backend("cogkura-inhibition-recording", dataset),
        write_results=False,
    )
    application = await runner.run(
        dataset,
        create_backend("cogkura-inhibition", dataset),
        write_results=False,
    )
    for left, right in zip(control.query_results, recording.query_results, strict=True):
        assert _signature(left) == _signature(right)
    metrics = application.capability_results[Capability.PERSISTENT_INHIBITION.value].metrics
    for key in (
        "inhibition_trace_precision",
        "inhibition_trace_recall",
        "persistent_inhibition_effect_precision",
        "persistent_inhibition_effect_recall",
        "persistent_inhibition_scope_isolation_accuracy",
    ):
        assert metrics[key] == 1.0
    for key in (
        "unexpected_inhibition_trace_rate",
        "unexpected_persistent_inhibition_rate",
        "future_trace_visibility_count",
        "positive_inhibition_penalty_violations",
        "activation_increase_due_to_inhibition",
    ):
        assert metrics[key] == 0.0
    summary = summarize_persistent_inhibition_workload(
        application_queries=application.query_results,
        application_uses=application.use_results,
        recording_queries=recording.query_results,
        control_queries=control.query_results,
    )
    assert summary.recording_only_control_drift_count == 0
    assert summary.unattributed_change_count == 0
    co_consumption = next(
        use for use in application.use_results if use.use_id == _CO_CONSUMPTION[dataset_name]
    )
    assert co_consumption.inhibition_traces == ()
