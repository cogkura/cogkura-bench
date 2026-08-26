"""Lifecycle diagnostic module tests."""

import importlib.util

import pytest

from cogkurabench.dataset import load_dataset
from cogkurabench.diagnostics.lifecycle import (
    LifecycleCaseSpec,
    LifecyclePolicy,
    run_lifecycle_case,
)
from cogkurabench.runner import BenchmarkRunner

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cogkura") is None,
    reason="cogkura not installed",
)


@pytest.mark.asyncio
async def test_benchmark_runner_case_matches_standard_runner() -> None:
    from cogkurabench.backends.cogkura import CogKuraBackend

    dataset = load_dataset("mini")
    backend_result = await BenchmarkRunner().run(
        dataset,
        CogKuraBackend(),
        write_results=False,
    )
    case_result = await run_lifecycle_case(
        LifecycleCaseSpec(
            case_id="benchmark_runner_standard",
            label="standard",
            policy=LifecyclePolicy(),
            use_benchmark_runner=True,
        ),
        dataset_name="mini",
        query_id="direct-001",
    )
    standard = backend_result.query_results[0]
    assert case_result.retrieved_item_count == len(standard.retrieved_items)


@pytest.mark.asyncio
async def test_reduced_lifecycle_case_reports_mapping_fields() -> None:
    case_result = await run_lifecycle_case(
        LifecycleCaseSpec(
            case_id="incremental_prepare_no_maintenance",
            label="no maintenance",
            policy=LifecyclePolicy(maintain="never"),
        ),
        dataset_name="mini",
        query_id="direct-001",
    )
    assert "raw_recall_count" in case_result.recall_mapping
    assert "mapped_recall_count" in case_result.recall_mapping
    assert (
        case_result.recall_mapping["raw_recall_count"]
        == case_result.recall_mapping["mapped_recall_count"]
        + case_result.recall_mapping["unmapped_recall_count"]
    )
