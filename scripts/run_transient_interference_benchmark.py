#!/usr/bin/env python3
"""Run 0.3.5 transient interference and hardening benchmark suites."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Sequence

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
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


def _metric(result_metrics: dict[str, float], key: str) -> str:
    value = result_metrics.get(key)
    if value is None:
        return "N/A"
    return f"{value:.3f}"


async def _run_case(dataset_name: str, backend_name: str) -> tuple[str, dict[str, float]]:
    dataset = load_dataset(dataset_name)
    backend = create_backend(backend_name, dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    merged: dict[str, float] = {}
    for capability_result in result.capability_results.values():
        merged.update(dict(capability_result.metrics))
    return backend_name, merged


async def _compare_control_enabled(dataset_name: str) -> list[str]:
    dataset = load_dataset(dataset_name)
    control_backend = create_backend("cogkura", dataset)
    enabled_backend = create_backend("cogkura-interference", dataset)
    control = await BenchmarkRunner().run(dataset, control_backend, write_results=False)
    enabled = await BenchmarkRunner().run(dataset, enabled_backend, write_results=False)
    lines = [f"### {dataset_name} control vs enabled", ""]
    changed = 0
    unattributed = 0
    for control_result, enabled_result in zip(
        control.query_results,
        enabled.query_results,
        strict=True,
    ):
        if control_result.retrieved_event_ids != enabled_result.retrieved_event_ids:
            changed += 1
            has_penalty = any(
                obs.total_penalty < 0.0
                for obs in enabled_result.transient_interference_observations
            )
            if not has_penalty:
                unattributed += 1
    lines.append(f"- Queries with changed retrieved IDs: {changed}")
    lines.append(f"- Unattributed retrieval changes: {unattributed}")
    lines.append("")
    return lines


async def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-regression",
        action="store_true",
        help="Skip existing-dataset control/enabled observation runs.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    lines = [
        "# Transient interference benchmark run",
        "",
        f"Git commit: {_git_commit() or 'unknown'}",
        "",
        "## interference_v1 hardening (cogkura)",
        "",
    ]
    _, hardening = await _run_case("interference_v1", "cogkura")
    for key in (
        "competition_pair_f1",
        "competition_pair_precision",
        "competition_pair_recall",
        "competition_direction_accuracy",
        "forbidden_competition_rate",
    ):
        lines.append(f"- {key}: {_metric(hardening, key)}")

    lines.extend(["", "## transient_interference_v1 control (cogkura)", ""])
    _, control = await _run_case("transient_interference_v1", "cogkura")
    lines.append(f"- interference_effect_f1: {_metric(control, 'interference_effect_f1')}")

    lines.extend(["", "## transient_interference_v1 enabled (cogkura-interference)", ""])
    _, enabled = await _run_case("transient_interference_v1", "cogkura-interference")
    for key in (
        "interference_effect_f1",
        "interference_effect_precision",
        "interference_effect_recall",
        "interference_effect_direction_accuracy",
        "unexpected_interference_rate",
        "threshold_suppression_accuracy",
        "rank_effect_accuracy",
        "positive_penalty_violation_count",
        "activation_increase_due_to_interference_count",
        "cotemporal_penalty_violation_count",
        "historical_future_interference_count",
    ):
        lines.append(f"- {key}: {_metric(enabled, key)}")

    if not args.skip_regression:
        lines.extend(["", "## Existing dataset regression observation", ""])
        for dataset_name in _REGRESSION_DATASETS:
            lines.extend(await _compare_control_enabled(dataset_name))

    output = "\n".join(lines)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
