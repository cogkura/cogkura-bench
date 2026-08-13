"""Capability aggregation and reporting tests."""

from datetime import UTC, datetime

from cogkurabench.evaluation.evaluator import aggregate_capability_results
from cogkurabench.evaluation.report import format_capability_table, format_result_tables
from cogkurabench.evaluation.result import (
    BenchmarkResult,
    CapabilityResult,
    EnvironmentInfo,
    QueryResult,
)
from cogkurabench.models import Capability


def _result(
    *,
    query_id: str,
    capability: Capability,
    metrics: dict[str, float],
    tags: tuple[str, ...] = (),
    should_abstain: bool = False,
) -> QueryResult:
    return QueryResult(
        query_id=query_id,
        capability=capability,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics=metrics,
        latency_ms=1.0,
        context_tokens=None,
        tags=tags,
        should_abstain=should_abstain,
    )


def test_abstain_queries_excluded_from_retrieval_averages() -> None:
    results = [
        _result(
            query_id="scored",
            capability=Capability.DIRECT_RECALL,
            metrics={"recall@5": 0.5},
        ),
        _result(
            query_id="abstain",
            capability=Capability.DIRECT_RECALL,
            metrics={"recall@5": 1.0},
            should_abstain=True,
        ),
    ]
    aggregated = aggregate_capability_results(results)
    assert aggregated["direct_recall"].metrics["recall@5"] == 0.5


def test_core_tag_filter_averages_subset_only() -> None:
    results = [
        _result(
            query_id="core",
            capability=Capability.DIRECT_RECALL,
            metrics={"recall@5": 1.0},
            tags=("core",),
        ),
        _result(
            query_id="coverage",
            capability=Capability.DIRECT_RECALL,
            metrics={"recall@5": 0.0},
        ),
    ]
    all_results = aggregate_capability_results(results)
    core_results = aggregate_capability_results(results, tags={"core"})
    assert all_results["direct_recall"].metrics["recall@5"] == 0.5
    assert core_results["direct_recall"].metrics["recall@5"] == 1.0
    assert core_results["direct_recall"].query_count == 1


def test_temporal_table_shows_both_accuracies() -> None:
    table = format_capability_table(
        {
            "temporal_recall": CapabilityResult(
                capability=Capability.TEMPORAL_RECALL,
                query_count=2,
                metrics={
                    "temporal_current_accuracy": 0.8,
                    "temporal_historical_accuracy": 0.6,
                },
            )
        }
    )
    assert "temporal_current_accuracy" in table
    assert "temporal_historical_accuracy" in table
    assert "0.800" in table
    assert "0.600" in table


def test_format_result_tables_includes_core_section() -> None:
    result = BenchmarkResult(
        benchmark_version="0.1.0",
        dataset_version="software_project_v1",
        backend_name="oracle",
        backend_version=None,
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        duration_ms=1.0,
        capability_results={
            "direct_recall": CapabilityResult(
                capability=Capability.DIRECT_RECALL,
                query_count=2,
                metrics={"recall@5": 0.5},
            )
        },
        query_results=(
            _result(
                query_id="core",
                capability=Capability.DIRECT_RECALL,
                metrics={"recall@5": 1.0},
                tags=("core",),
            ),
            _result(
                query_id="extra",
                capability=Capability.DIRECT_RECALL,
                metrics={"recall@5": 0.0},
            ),
        ),
        environment=EnvironmentInfo(
            python_version="3.12.0",
            platform="test",
            git_commit=None,
        ),
    )
    tables = format_result_tables(result)
    assert "## All queries" in tables
    assert "## Core queries" in tables


def test_core_metamemory_f1_uses_finalize_not_per_query_average() -> None:
    result = BenchmarkResult(
        benchmark_version="0.1.0",
        dataset_version="helios_v1",
        backend_name="oracle",
        backend_version=None,
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        duration_ms=1.0,
        capability_results={
            "metamemory": CapabilityResult(
                capability=Capability.METAMEMORY,
                query_count=1,
                metrics={"missing_knowledge_f1": 0.0},
            )
        },
        query_results=(
            _result(
                query_id="helios-meta-001",
                capability=Capability.METAMEMORY,
                metrics={
                    "missing_knowledge_tp": 1.0,
                    "missing_knowledge_fp": 0.0,
                    "missing_knowledge_fn": 0.0,
                    "missing_knowledge_tn": 0.0,
                    "missing_knowledge_f1": 0.0,
                },
                tags=("core",),
                should_abstain=True,
            ),
        ),
        environment=EnvironmentInfo(
            python_version="3.12.0",
            platform="test",
            git_commit=None,
        ),
    )
    tables = format_result_tables(result)
    core_section = tables.split("## Core queries", maxsplit=1)[1]
    assert "metamemory" in core_section
    assert "missing_knowledge_f1" in core_section
    assert "| 1.000 |" in core_section
