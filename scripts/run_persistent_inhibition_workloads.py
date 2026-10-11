#!/usr/bin/env python3
"""Run CogKuraBench 0.3.8 persistent-inhibition workloads and regressions."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Sequence

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.result import BenchmarkResult, QueryResult
from cogkurabench.metrics.persistent_inhibition_workload import (
    summarize_persistent_inhibition_workload,
    trace_growth_checkpoints,
)
from cogkurabench.models import BenchmarkDataset
from cogkurabench.runner import BenchmarkRunner

_WORKLOADS = (
    "persistent_inhibition_software_v1",
    "persistent_inhibition_customer_v1",
)
_REGRESSION_DATASETS = (
    "mini",
    "software_project_v1",
    "helios_v1",
    "customer_decision_context_v1",
)
_TRACE_KEYS = (
    "inhibition_trace_precision",
    "inhibition_trace_recall",
    "inhibition_trace_f1",
    "unexpected_inhibition_trace_rate",
)
_EFFECT_KEYS = (
    "persistent_inhibition_effect_precision",
    "persistent_inhibition_effect_recall",
    "persistent_inhibition_effect_f1",
    "unexpected_persistent_inhibition_rate",
    "persistent_inhibition_scope_isolation_accuracy",
    "repetition_strengthening_accuracy",
    "inhibition_recovery_order_accuracy",
    "future_trace_visibility_count",
    "positive_inhibition_penalty_violations",
    "activation_increase_due_to_inhibition",
)


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _metric(metrics: dict[str, float], key: str) -> str:
    value = metrics.get(key)
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def _capability_metrics(result: BenchmarkResult) -> dict[str, float]:
    merged: dict[str, float] = {}
    for capability_result in result.capability_results.values():
        merged.update(dict(capability_result.metrics))
    return merged


def _signature(query_result: QueryResult) -> tuple[tuple[tuple[str, ...], float | None, int], ...]:
    return tuple(
        (item.source_event_ids, item.score, item.rank) for item in query_result.retrieved_items
    )


async def _run(dataset_name: str, backend_name: str) -> BenchmarkResult:
    dataset = load_dataset(dataset_name)
    backend = create_backend(backend_name, dataset)
    return await BenchmarkRunner().run(dataset, backend, write_results=False)


def _profile_lines(title: str, metrics: dict[str, float], keys: Sequence[str]) -> list[str]:
    lines = [f"## {title}", ""]
    for key in keys:
        lines.append(f"- {key}: {_metric(metrics, key)}")
    lines.append("")
    return lines


def _timestamp_thirds(
    dataset: BenchmarkDataset,
    result: BenchmarkResult,
) -> list[str]:
    query_times = {query.id: query.timestamp for query in dataset.queries}
    use_times = {use.id: use.timestamp for use in dataset.uses}
    ordered_queries = sorted(result.query_results, key=lambda item: query_times[item.query_id])
    ordered_uses = sorted(result.use_results, key=lambda item: use_times[item.use_id])
    lines = ["### Latency and trace growth by simulated time", ""]
    if ordered_queries:
        bounds = (
            max(1, len(ordered_queries) // 3),
            max(2, (2 * len(ordered_queries)) // 3),
            len(ordered_queries),
        )
        start = 0
        for label, end in zip(("early", "middle", "late"), bounds, strict=True):
            window = ordered_queries[start:end]
            mean = sum(item.latency_ms for item in window) / len(window)
            lines.append(f"- query {label}: n={len(window)} mean_latency_ms={mean:.1f}")
            start = end
    early, middle, late = trace_growth_checkpoints(tuple(ordered_uses))
    for label, snapshot in (("early", early), ("middle", middle), ("late", late)):
        lines.append(
            f"- use {label}: uses={snapshot['uses']} traces={snapshot['trace_count']} "
            f"unique={snapshot['unique_trace_pair_count']} "
            f"repeated={snapshot['repeated_trace_count']}"
        )
    lines.append("")
    return lines


def _change_lines(
    recording: BenchmarkResult,
    application: BenchmarkResult,
) -> list[str]:
    recording_by_id = {item.query_id: item for item in recording.query_results}
    lines = ["### Returned-set changes, rank changes, and threshold suppressions", ""]
    any_row = False
    for query_result in application.query_results:
        recorded = recording_by_id[query_result.query_id]
        if query_result.retrieved_event_ids != recorded.retrieved_event_ids:
            any_row = True
            lines.append(
                f"- returned set `{query_result.query_id}`: "
                f"application {query_result.retrieved_event_ids} "
                f"recording {recorded.retrieved_event_ids}"
            )
        for observation in query_result.persistent_inhibition_observations:
            if observation.crossed_activation_threshold:
                any_row = True
                lines.append(
                    f"- threshold `{query_result.query_id}` "
                    f"candidate {observation.candidate_source_event_ids} "
                    f"penalty {observation.penalty:.4f}"
                )
            if (
                observation.rank_before is not None
                and observation.rank_after is not None
                and observation.rank_after > observation.rank_before
                and observation.penalty < 0
            ):
                any_row = True
                lines.append(
                    f"- rank `{query_result.query_id}` "
                    f"candidate {observation.candidate_source_event_ids} "
                    f"{observation.rank_before} -> {observation.rank_after} "
                    f"penalty {observation.penalty:.4f}"
                )
    if not any_row:
        lines.append("- none")
    lines.append("")
    return lines


async def _workload_lines(dataset_name: str) -> list[str]:
    dataset = load_dataset(dataset_name)
    control, recording, application = await asyncio.gather(
        _run(dataset_name, "cogkura"),
        _run(dataset_name, "cogkura-inhibition-recording"),
        _run(dataset_name, "cogkura-inhibition"),
    )
    lines: list[str] = [f"# {dataset_name}", ""]
    for title, result, keys in (
        (f"{dataset_name} control", control, ("recall@5",)),
        (f"{dataset_name} recording", recording, _TRACE_KEYS),
        (f"{dataset_name} application", application, (*_TRACE_KEYS, *_EFFECT_KEYS)),
    ):
        lines.extend(_profile_lines(title, _capability_metrics(result), keys))
    summary = summarize_persistent_inhibition_workload(
        application_queries=application.query_results,
        application_uses=application.use_results,
        recording_queries=recording.query_results,
        control_queries=control.query_results,
    )
    lines.extend(
        [
            "### Workload summary",
            "",
            f"- uses: {summary.use_count}",
            f"- uses with traces: {summary.uses_with_traces}",
            f"- traces: {summary.trace_count}",
            f"- unique trace pairs: {summary.unique_trace_pair_count}",
            f"- repeated traces: {summary.repeated_trace_count}",
            f"- max traces per use: {summary.max_traces_per_use}",
            f"- max traces per inhibited memory: {summary.max_traces_per_inhibited_memory}",
            f"- scope keys: {summary.scope_key_count}",
            f"- queries with stored traces: {summary.queries_with_stored_traces}",
            f"- queries with matched traces: {summary.queries_with_matched_traces}",
            f"- queries with effective traces: {summary.queries_with_effective_traces}",
            f"- queries with penalty: {summary.queries_with_penalty}",
            f"- rank changes: {summary.rank_change_count}",
            f"- threshold suppressions: {summary.threshold_suppression_count}",
            f"- returned-set changes: {summary.result_change_count}",
            f"- unattributed changes: {summary.unattributed_change_count}",
            f"- recording/control drift: {summary.recording_only_control_drift_count}",
            f"- trace saturation: {summary.trace_saturation_count}",
            f"- memory saturation: {summary.memory_saturation_count}",
            "",
        ]
    )
    lines.extend(_timestamp_thirds(dataset, application))
    lines.extend(_change_lines(recording, application))
    drift = 0
    for control_result, recording_result in zip(
        control.query_results,
        recording.query_results,
        strict=True,
    ):
        if _signature(control_result) != _signature(recording_result):
            drift += 1
            lines.append(f"- recording/control drift on `{control_result.query_id}`")
    if drift:
        lines.append("")
    return lines


async def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-regression",
        action="store_true",
        help="Skip controlled-fixture and default-dataset runs.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    lines = [
        "# Persistent inhibition workloads",
        "",
        f"Git commit: {_git_commit() or 'unknown'}",
        "",
    ]
    if not args.skip_regression:
        controlled = await _run("persistent_inhibition_v1", "cogkura-inhibition")
        lines.extend(
            _profile_lines(
                "persistent_inhibition_v1 application",
                _capability_metrics(controlled),
                (*_TRACE_KEYS, *_EFFECT_KEYS),
            )
        )
    for dataset_name in _WORKLOADS:
        lines.extend(await _workload_lines(dataset_name))
    if not args.skip_regression:
        transient = await _run("transient_interference_v2", "cogkura-interference")
        lines.extend(
            _profile_lines(
                "transient_interference_v2",
                _capability_metrics(transient),
                (
                    "interference_effect_precision",
                    "interference_effect_recall",
                    "interference_effect_f1",
                    "interference_effect_direction_accuracy",
                    "unexpected_interference_rate",
                ),
            )
        )
        lines.extend(["## Default datasets (cogkura)", ""])
        for dataset_name in _REGRESSION_DATASETS:
            result = await _run(dataset_name, "cogkura")
            metrics = _capability_metrics(result)
            lines.append(f"- {dataset_name}: recall@5 {_metric(metrics, 'recall@5')}")
        lines.append("")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
