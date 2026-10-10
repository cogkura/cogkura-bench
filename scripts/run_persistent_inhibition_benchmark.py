#!/usr/bin/env python3
"""Run CogKuraBench 0.3.6 persistent inhibition and regression suites."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Sequence

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.result import BenchmarkResult
from cogkurabench.runner import BenchmarkRunner

_REGRESSION_DATASETS = (
    "mini",
    "software_project_v1",
    "helios_v1",
    "customer_decision_context_v1",
)

_RECOVERY_QUERIES = ("pi-immediate", "pi-repeated", "pi-half", "pi-later")


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


async def _run(dataset_name: str, backend_name: str) -> BenchmarkResult:
    dataset = load_dataset(dataset_name)
    backend = create_backend(backend_name, dataset)
    return await BenchmarkRunner().run(dataset, backend, write_results=False)


def _jenkins_penalty(result: BenchmarkResult, query_id: str) -> str:
    query_result = next(item for item in result.query_results if item.query_id == query_id)
    penalties = [
        abs(observation.penalty)
        for observation in query_result.persistent_inhibition_observations
        if observation.penalty < 0.0 and "pi-jenkins" in observation.candidate_source_event_ids
    ]
    if not penalties:
        return "0.000"
    return f"{max(penalties):.3f}"


def _profile_lines(title: str, metrics: dict[str, float], keys: Sequence[str]) -> list[str]:
    lines = [f"## {title}", ""]
    for key in keys:
        lines.append(f"- {key}: {_metric(metrics, key)}")
    lines.append("")
    return lines


async def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-regression",
        action="store_true",
        help="Skip existing-dataset control runs.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    lines = [
        "# Persistent inhibition benchmark run",
        "",
        f"Git commit: {_git_commit() or 'unknown'}",
        "",
    ]

    interference = await _run("interference_v1", "cogkura")
    lines.extend(
        _profile_lines(
            "interference_v1 (cogkura)",
            _capability_metrics(interference),
            (
                "competition_pair_f1",
                "competition_pair_precision",
                "competition_pair_recall",
                "competition_direction_accuracy",
                "forbidden_competition_rate",
            ),
        )
    )

    transient_control = await _run("transient_interference_v1", "cogkura")
    lines.extend(
        _profile_lines(
            "transient_interference_v1 control (cogkura)",
            _capability_metrics(transient_control),
            ("interference_effect_f1",),
        )
    )
    transient_enabled = await _run("transient_interference_v1", "cogkura-interference")
    lines.extend(
        _profile_lines(
            "transient_interference_v1 enabled (cogkura-interference)",
            _capability_metrics(transient_enabled),
            (
                "interference_effect_f1",
                "interference_effect_precision",
                "interference_effect_recall",
                "unexpected_interference_rate",
                "positive_penalty_violation_count",
            ),
        )
    )

    control = await _run("persistent_inhibition_v1", "cogkura")
    recording = await _run("persistent_inhibition_v1", "cogkura-inhibition-recording")
    applied = await _run("persistent_inhibition_v1", "cogkura-inhibition")
    control_metrics = _capability_metrics(control)
    recording_metrics = _capability_metrics(recording)
    applied_metrics = _capability_metrics(applied)

    lines.extend(
        _profile_lines(
            "persistent_inhibition_v1 control (cogkura)",
            control_metrics,
            ("persistent_inhibition_effect_f1", "inhibition_trace_f1"),
        )
    )
    lines.extend(
        _profile_lines(
            "persistent_inhibition_v1 recording",
            recording_metrics,
            (
                "inhibition_trace_precision",
                "inhibition_trace_recall",
                "inhibition_trace_f1",
                "unexpected_inhibition_trace_rate",
                "persistent_inhibition_effect_f1",
            ),
        )
    )
    lines.extend(
        _profile_lines(
            "persistent_inhibition_v1 applied",
            applied_metrics,
            (
                "inhibition_trace_precision",
                "inhibition_trace_recall",
                "inhibition_trace_f1",
                "unexpected_inhibition_trace_rate",
                "persistent_inhibition_effect_precision",
                "persistent_inhibition_effect_recall",
                "persistent_inhibition_effect_f1",
                "unexpected_persistent_inhibition_rate",
                "persistent_inhibition_scope_isolation_accuracy",
                "persistent_inhibition_history_accuracy",
                "repetition_strengthening_accuracy",
                "inhibition_recovery_order_accuracy",
                "positive_inhibition_penalty_violations",
                "activation_increase_due_to_inhibition",
                "out_of_scope_inhibition_count",
                "future_trace_visibility_count",
            ),
        )
    )

    lines.extend(["## Recording versus application", ""])
    lines.append("| Query | Recording penalty | Applied penalty | Returned equal |")
    lines.append("| --- | ---: | ---: | --- |")
    unattributed = 0
    no_effect_mismatch = 0
    control_recording_mismatch = 0
    for control_result, recording_result, applied_result in zip(
        control.query_results,
        recording.query_results,
        applied.query_results,
        strict=True,
    ):
        control_signature = [
            (item.source_event_ids, item.score, item.rank)
            for item in control_result.retrieved_items
        ]
        recording_signature = [
            (item.source_event_ids, item.score, item.rank)
            for item in recording_result.retrieved_items
        ]
        if control_signature != recording_signature:
            control_recording_mismatch += 1
        recording_penalty = _jenkins_penalty(recording, recording_result.query_id)
        applied_penalty = _jenkins_penalty(applied, applied_result.query_id)
        same_ids = recording_result.retrieved_event_ids == applied_result.retrieved_event_ids
        lines.append(
            f"| `{applied_result.query_id}` | {recording_penalty} | {applied_penalty} | "
            f"{'yes' if same_ids else 'no'} |"
        )
        changed = recording_result.retrieved_event_ids != applied_result.retrieved_event_ids or [
            (item.source_event_ids, item.score, item.rank)
            for item in recording_result.retrieved_items
        ] != [
            (item.source_event_ids, item.score, item.rank)
            for item in applied_result.retrieved_items
        ]
        has_penalty = any(
            observation.penalty < 0.0
            for observation in applied_result.persistent_inhibition_observations
        )
        if changed and not has_penalty:
            unattributed += 1
        if not has_penalty and changed:
            no_effect_mismatch += 1
    lines.extend(
        [
            "",
            f"- Control vs recording retrieval mismatches: {control_recording_mismatch}",
            f"- Unattributed application drift: {unattributed}",
            f"- No-effect parity mismatches: {no_effect_mismatch}",
            "",
            "## Recovery magnitudes (applied, Jenkins)",
            "",
            "| Stage | Query | Penalty magnitude |",
            "| --- | --- | ---: |",
        ]
    )
    for query_id in _RECOVERY_QUERIES:
        lines.append(f"| {query_id} | `{query_id}` | {_jenkins_penalty(applied, query_id)} |")
    lines.append("")

    if not args.skip_regression:
        lines.extend(["## Existing dataset regression (cogkura)", ""])
        for dataset_name in _REGRESSION_DATASETS:
            result = await _run(dataset_name, "cogkura")
            metrics = _capability_metrics(result)
            lines.append(f"- {dataset_name}: recall@5 {_metric(metrics, 'recall@5')}")
        lines.append("")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
