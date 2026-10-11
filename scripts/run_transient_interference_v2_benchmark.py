#!/usr/bin/env python3
"""Run CogKuraBench 0.3.7 transient interference v2 and regression suites."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Sequence

from cogkurabench import __version__
from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.result import BenchmarkResult, QueryResult
from cogkurabench.runner import BenchmarkRunner

_REGRESSION_DATASETS = (
    "mini",
    "software_project_v1",
    "helios_v1",
    "customer_decision_context_v1",
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


def _merged(result: BenchmarkResult) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for capability_result in result.capability_results.values():
        metrics.update(dict(capability_result.metrics))
    return metrics


def _signature(query_result: QueryResult) -> list[tuple[tuple[str, ...], float | None, int]]:
    return [(item.source_event_ids, item.score, item.rank) for item in query_result.retrieved_items]


def _max_pressure(query_result: QueryResult, candidate: str, competitor: str) -> float:
    pressures = [
        contribution.pressure
        for observation in query_result.transient_interference_observations
        if candidate in observation.candidate_source_event_ids
        for contribution in observation.contributions
        if competitor in contribution.competitor_source_event_ids
    ]
    return max(pressures) if pressures else 0.0


def _penalty(query_result: QueryResult, candidate: str) -> float:
    penalties = [
        observation.total_penalty
        for observation in query_result.transient_interference_observations
        if candidate in observation.candidate_source_event_ids and observation.total_penalty < 0
    ]
    return min(penalties) if penalties else 0.0


async def _run(dataset_name: str, backend_name: str) -> BenchmarkResult:
    dataset = load_dataset(dataset_name)
    backend = create_backend(backend_name, dataset)
    return await BenchmarkRunner().run(dataset, backend, write_results=False)


def _lines(title: str, metrics: dict[str, float], keys: Sequence[str]) -> list[str]:
    lines = [f"## {title}", ""]
    for key in keys:
        lines.append(f"- {key}: {_metric(metrics, key)}")
    lines.append("")
    return lines


async def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-regression", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    lines = [
        "# Transient interference v2 benchmark run",
        "",
        f"CogKuraBench: {__version__}",
        f"Git commit: {_git_commit() or 'unknown'}",
        "",
    ]

    control = await _run("transient_interference_v2", "cogkura")
    enabled = await _run("transient_interference_v2", "cogkura-interference")
    enabled_metrics = _merged(enabled)
    lines.extend(
        _lines(
            "transient_interference_v2 control (cogkura)",
            _merged(control),
            ("interference_effect_f1",),
        )
    )
    lines.extend(
        _lines(
            "transient_interference_v2 enabled (cogkura-interference)",
            enabled_metrics,
            (
                "interference_effect_precision",
                "interference_effect_recall",
                "interference_effect_f1",
                "interference_effect_direction_accuracy",
                "unexpected_interference_rate",
                "positive_penalty_violation_count",
                "activation_increase_due_to_interference_count",
                "cotemporal_penalty_violation_count",
                "historical_future_interference_count",
            ),
        )
    )

    by_control = {item.query_id: item for item in control.query_results}
    unattributed = 0
    lines.extend(
        [
            "## Control versus interference",
            "",
            "| Query | Control top | Interference top | Penalty | Attributed |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for enabled_result in enabled.query_results:
        control_result = by_control[enabled_result.query_id]
        changed = _signature(control_result) != _signature(enabled_result)
        penalty = _penalty(enabled_result, "v2-gha")
        if penalty == 0.0:
            penalty = _penalty(enabled_result, "v2-jenkins")
        attributed = (
            (not changed)
            or penalty < 0.0
            or any(
                observation.total_penalty < 0
                for observation in enabled_result.transient_interference_observations
            )
        )
        if changed and not any(
            observation.total_penalty < 0
            for observation in enabled_result.transient_interference_observations
        ):
            unattributed += 1
            attributed = False
        control_top = control_result.retrieved_event_ids[:2]
        enabled_top = enabled_result.retrieved_event_ids[:2]
        lines.append(
            f"| `{enabled_result.query_id}` | {control_top} | {enabled_top} | "
            f"{penalty:.3f} | {'yes' if attributed else 'no'} |"
        )
    lines.extend(["", f"- unattributed_transient_retrieval_change_count: {unattributed}", ""])

    multi = next(item for item in enabled.query_results if item.query_id == "ti2-multi")
    pair = next(item for item in enabled.query_results if item.query_id == "ti2-pair")
    after = next(item for item in enabled.query_results if item.query_id == "ti2-after")
    lines.extend(
        [
            "## Accessibility and aggregation",
            "",
            f"- pair penalty magnitude: {abs(_penalty(pair, 'v2-gha')):.3f}",
            f"- multi penalty magnitude: {abs(_penalty(multi, 'v2-gha')):.3f}",
            (
                "- jenkins pressure before reinforcement: "
                f"{_max_pressure(multi, 'v2-gha', 'v2-jenkins'):.3f}"
            ),
            (
                "- jenkins pressure after reinforcement: "
                f"{_max_pressure(after, 'v2-gha', 'v2-jenkins'):.3f}"
            ),
            "",
        ]
    )

    frozen = await _run("transient_interference_v1", "cogkura-interference")
    lines.extend(
        _lines(
            "transient_interference_v1 on CogKura 0.17.6",
            _merged(frozen),
            (
                "interference_effect_precision",
                "interference_effect_recall",
                "interference_effect_f1",
                "unexpected_interference_rate",
            ),
        )
    )
    interference = await _run("interference_v1", "cogkura")
    lines.extend(
        _lines(
            "interference_v1",
            _merged(interference),
            (
                "competition_pair_f1",
                "competition_pair_precision",
                "competition_pair_recall",
                "competition_direction_accuracy",
            ),
        )
    )
    persistent = await _run("persistent_inhibition_v1", "cogkura-inhibition")
    lines.extend(
        _lines(
            "persistent_inhibition_v1 applied",
            _merged(persistent),
            (
                "inhibition_trace_precision",
                "inhibition_trace_recall",
                "persistent_inhibition_effect_precision",
                "persistent_inhibition_effect_recall",
                "unexpected_persistent_inhibition_rate",
                "persistent_inhibition_scope_isolation_accuracy",
                "repetition_strengthening_accuracy",
                "inhibition_recovery_order_accuracy",
                "positive_inhibition_penalty_violations",
            ),
        )
    )

    if not args.skip_regression:
        lines.extend(["## Ordinary retrieval (cogkura)", ""])
        for dataset_name in _REGRESSION_DATASETS:
            result = await _run(dataset_name, "cogkura")
            lines.append(f"- {dataset_name}: recall@5 {_metric(_merged(result), 'recall@5')}")
        lines.append("")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
