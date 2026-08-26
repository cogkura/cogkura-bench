"""Controlled lifecycle replay variants for CogKura diagnostics."""

from __future__ import annotations

import asyncio
import subprocess
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from cogkurabench import __version__
from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.clock import BenchmarkClock
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.evaluator import evaluate_query
from cogkurabench.models import (
    BenchmarkAction,
    BenchmarkDataset,
    ContextRequest,
    QueryAction,
    RetrievalRequest,
)
from cogkurabench.runner import BenchmarkRunner

PrepareMode = Literal["incremental", "query_only"]
MaintainMode = Literal["incremental", "query_only", "never"]
IngestMode = Literal["incremental", "bulk_at_query"]


@dataclass(frozen=True, slots=True)
class LifecyclePolicy:
    """Lifecycle variant configuration."""

    prepare: PrepareMode = "incremental"
    maintain: MaintainMode = "incremental"
    ingest: IngestMode = "incremental"


@dataclass(frozen=True, slots=True)
class LifecycleCaseSpec:
    """One diagnostic lifecycle case."""

    case_id: str
    label: str
    policy: LifecyclePolicy
    use_benchmark_runner: bool = False


LIFECYCLE_CASES: tuple[LifecycleCaseSpec, ...] = (
    LifecycleCaseSpec(
        case_id="benchmark_runner_standard",
        label="Standard BenchmarkRunner replay",
        policy=LifecyclePolicy(),
        use_benchmark_runner=True,
    ),
    LifecycleCaseSpec(
        case_id="incremental_prepare_no_maintenance",
        label="Incremental prepare, no maintenance",
        policy=LifecyclePolicy(maintain="never"),
    ),
    LifecycleCaseSpec(
        case_id="incremental_prepare_query_maintenance",
        label="Incremental prepare, query-only maintenance",
        policy=LifecyclePolicy(maintain="query_only"),
    ),
    LifecycleCaseSpec(
        case_id="incremental_ingest_query_prepare_no_maintenance",
        label="Incremental ingest, query-only prepare, no maintenance",
        policy=LifecyclePolicy(prepare="query_only", maintain="never"),
    ),
    LifecycleCaseSpec(
        case_id="incremental_ingest_query_prepare_query_maintenance",
        label="Incremental ingest, query-only prepare, query-only maintenance",
        policy=LifecyclePolicy(prepare="query_only", maintain="query_only"),
    ),
    LifecycleCaseSpec(
        case_id="bulk_ingest_query_prepare_no_maintenance",
        label="Bulk ingest at query, query-only prepare, no maintenance",
        policy=LifecyclePolicy(ingest="bulk_at_query", prepare="query_only", maintain="never"),
    ),
    LifecycleCaseSpec(
        case_id="bulk_ingest_query_prepare_query_maintenance",
        label="Bulk ingest at query, query-only prepare, query-only maintenance",
        policy=LifecyclePolicy(
            ingest="bulk_at_query",
            prepare="query_only",
            maintain="query_only",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class LifecycleCaseResult:
    """Structured output from one lifecycle diagnostic case."""

    case_id: str
    label: str
    benchmark_version: str
    cogkura_version: str | None
    git_commit: str | None
    git_dirty: bool
    dataset: str
    query_id: str
    executed_at: str
    policy: dict[str, str]
    lifecycle_counters: dict[str, Any]
    last_prepare: dict[str, Any]
    last_maintenance: dict[str, Any]
    memory_inventory: dict[str, Any]
    recall_mapping: dict[str, Any]
    context_mapping: dict[str, Any]
    selector_funnel: dict[str, Any]
    evidence_group_coverage_at_retrieval: float | None
    evidence_group_coverage_at_budget: float | None
    retrieved_item_count: int
    context_item_count: int
    context_tokens: int | None


def _git_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _git_dirty() -> bool:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return bool(completed.stdout.strip())


def _actions_by_time(dataset: BenchmarkDataset) -> dict[datetime, list[BenchmarkAction]]:
    grouped: dict[datetime, list[BenchmarkAction]] = defaultdict(list)
    for action in dataset.actions:
        grouped[action.timestamp].append(action)
    return grouped


def _query_actions_at(timestamp: datetime, actions: list[BenchmarkAction]) -> list[QueryAction]:
    return [action for action in actions if isinstance(action, QueryAction)]


async def run_lifecycle_case(
    case: LifecycleCaseSpec,
    *,
    dataset_name: str = "customer_decision_context_v1",
    query_id: str = "customer-waterproof-jacket",
) -> LifecycleCaseResult:
    """Execute one lifecycle diagnostic case."""
    dataset = load_dataset(dataset_name)
    query = dataset.query_by_id()[query_id]
    executed_at = datetime.now(UTC).isoformat()

    if case.use_benchmark_runner:
        backend = CogKuraBackend()
        result = await BenchmarkRunner().run(dataset, backend, write_results=False)
        query_result = next(item for item in result.query_results if item.query_id == query_id)
        snapshot = await backend.diagnostic_snapshot()
        recall_mapping = _extract_mapping(query_result.backend_metadata, "recall_mapping")
        context_mapping = _extract_mapping(query_result.context_backend_metadata, "context_mapping")
        selector_funnel = _extract_mapping(query_result.context_backend_metadata, "selector_funnel")
        return LifecycleCaseResult(
            case_id=case.case_id,
            label=case.label,
            benchmark_version=__version__,
            cogkura_version=backend.version,
            git_commit=_git_commit(),
            git_dirty=_git_dirty(),
            dataset=dataset_name,
            query_id=query_id,
            executed_at=executed_at,
            policy={
                "prepare": case.policy.prepare,
                "maintain": case.policy.maintain,
                "ingest": case.policy.ingest,
            },
            lifecycle_counters=_snapshot_section(snapshot, "lifecycle_counters"),
            last_prepare=_snapshot_section(snapshot, "last_prepare"),
            last_maintenance=_snapshot_section(snapshot, "last_maintenance"),
            memory_inventory=_snapshot_section(snapshot, "memory_inventory"),
            recall_mapping=recall_mapping,
            context_mapping=context_mapping,
            selector_funnel=selector_funnel,
            evidence_group_coverage_at_retrieval=query_result.metrics.get(
                "evidence_group_coverage_at_retrieval"
            ),
            evidence_group_coverage_at_budget=query_result.metrics.get(
                "evidence_group_coverage_at_budget"
            ),
            retrieved_item_count=len(query_result.retrieved_items),
            context_item_count=len(query_result.context_items),
            context_tokens=query_result.context_tokens,
        )

    backend = CogKuraBackend()
    await backend.reset()
    policy = case.policy
    actions_by_time = _actions_by_time(dataset)
    pending_events = sorted(
        dataset.events, key=lambda event: (event.timestamp, event.sequence, event.id)
    )
    ingested_ids: set[str] = set()
    clock = BenchmarkClock(current=pending_events[0].timestamp)
    events_by_id = dataset.event_by_id()
    bulk_ingested = False

    for timestamp in sorted(actions_by_time):
        clock.advance_to(timestamp)
        actions = actions_by_time[timestamp]
        query_actions = _query_actions_at(timestamp, actions)
        is_query_timestamp = bool(query_actions)

        if policy.ingest == "bulk_at_query":
            if is_query_timestamp and not bulk_ingested:
                newly_visible = [event for event in pending_events if event.id not in ingested_ids]
                if newly_visible:
                    await backend.ingest(newly_visible)
                    ingested_ids.update(event.id for event in newly_visible)
                bulk_ingested = True
        else:
            newly_visible = [
                event
                for event in pending_events
                if event.timestamp <= timestamp and event.id not in ingested_ids
            ]
            if newly_visible:
                await backend.ingest(newly_visible)
                ingested_ids.update(event.id for event in newly_visible)

        should_prepare = policy.prepare == "incremental" or is_query_timestamp
        if should_prepare:
            await backend.prepare(as_of=clock.current)

        should_maintain = False
        if policy.maintain == "incremental":
            should_maintain = True
        elif policy.maintain == "query_only" and is_query_timestamp:
            should_maintain = True
        if should_maintain:
            await backend.maintain(as_of=clock.current)

        for query_action in query_actions:
            if query_action.query.id != query_id:
                continue
            request = RetrievalRequest(
                query_id=query.id,
                query=query.query,
                as_of=clock.current,
                limit=query.retrieval_limit,
                goal=query.goal,
                valid_at=query.valid_at,
                entity_ids=query.entity_ids,
                predicate=query.predicate,
                object_value=query.object_value,
            )
            response = await backend.retrieve(request)
            context_response = None
            if query.prompt_budget_tokens is not None:
                context_request = ContextRequest(
                    query_id=query.id,
                    query=query.query,
                    as_of=clock.current,
                    goal=query.goal,
                    valid_at=query.valid_at,
                    prompt_budget_tokens=query.prompt_budget_tokens,
                    entity_ids=query.entity_ids,
                    predicate=query.predicate,
                    object_value=query.object_value,
                )
                context_response = await backend.select_context(context_request)
            query_result = evaluate_query(
                query,
                response.items,
                latency_ms=response.latency_ms,
                events_by_id=events_by_id,
                context_response=context_response,
                backend_metadata=dict(response.backend_metadata),
                context_items=context_response.items if context_response is not None else (),
                context_backend_metadata=(
                    dict(context_response.backend_metadata) if context_response is not None else {}
                ),
            )
            snapshot = await backend.diagnostic_snapshot()
            recall_mapping = _extract_mapping(query_result.backend_metadata, "recall_mapping")
            context_mapping = _extract_mapping(
                query_result.context_backend_metadata,
                "context_mapping",
            )
            selector_funnel = _extract_mapping(
                query_result.context_backend_metadata,
                "selector_funnel",
            )
            return LifecycleCaseResult(
                case_id=case.case_id,
                label=case.label,
                benchmark_version=__version__,
                cogkura_version=backend.version,
                git_commit=_git_commit(),
                git_dirty=_git_dirty(),
                dataset=dataset_name,
                query_id=query_id,
                executed_at=executed_at,
                policy={
                    "prepare": policy.prepare,
                    "maintain": policy.maintain,
                    "ingest": policy.ingest,
                },
                lifecycle_counters=_snapshot_section(snapshot, "lifecycle_counters"),
                last_prepare=_snapshot_section(snapshot, "last_prepare"),
                last_maintenance=_snapshot_section(snapshot, "last_maintenance"),
                memory_inventory=_snapshot_section(snapshot, "memory_inventory"),
                recall_mapping=recall_mapping,
                context_mapping=context_mapping,
                selector_funnel=selector_funnel,
                evidence_group_coverage_at_retrieval=query_result.metrics.get(
                    "evidence_group_coverage_at_retrieval"
                ),
                evidence_group_coverage_at_budget=query_result.metrics.get(
                    "evidence_group_coverage_at_budget"
                ),
                retrieved_item_count=len(query_result.retrieved_items),
                context_item_count=len(query_result.context_items),
                context_tokens=query_result.context_tokens,
            )

    raise RuntimeError(f"Query {query_id!r} was not executed for lifecycle case {case.case_id!r}")


def _extract_mapping(metadata: Mapping[str, Any], key: str) -> dict[str, Any]:
    cogkura_meta = metadata.get("cogkura", {})
    if not isinstance(cogkura_meta, dict):
        return {}
    value = cogkura_meta.get(key, {})
    return dict(value) if isinstance(value, dict) else {}


def _snapshot_section(snapshot: dict[str, object], key: str) -> dict[str, Any]:
    value = snapshot.get(key, {})
    return dict(value) if isinstance(value, dict) else {}


def lifecycle_case_to_dict(result: LifecycleCaseResult) -> dict[str, Any]:
    """Serialize a lifecycle case result for JSON output."""
    return {
        "case_id": result.case_id,
        "label": result.label,
        "benchmark_version": result.benchmark_version,
        "cogkura_version": result.cogkura_version,
        "git_commit": result.git_commit,
        "git_dirty": result.git_dirty,
        "dataset": result.dataset,
        "query_id": result.query_id,
        "executed_at": result.executed_at,
        "policy": result.policy,
        "lifecycle_counters": result.lifecycle_counters,
        "last_prepare": result.last_prepare,
        "last_maintenance": result.last_maintenance,
        "memory_inventory": result.memory_inventory,
        "recall_mapping": result.recall_mapping,
        "context_mapping": result.context_mapping,
        "selector_funnel": result.selector_funnel,
        "evidence_group_coverage_at_retrieval": result.evidence_group_coverage_at_retrieval,
        "evidence_group_coverage_at_budget": result.evidence_group_coverage_at_budget,
        "retrieved_item_count": result.retrieved_item_count,
        "context_item_count": result.context_item_count,
        "context_tokens": result.context_tokens,
    }


async def run_all_lifecycle_cases(
    *,
    dataset_name: str = "customer_decision_context_v1",
    query_id: str = "customer-waterproof-jacket",
) -> list[LifecycleCaseResult]:
    results: list[LifecycleCaseResult] = []
    for case in LIFECYCLE_CASES:
        results.append(
            await run_lifecycle_case(
                case,
                dataset_name=dataset_name,
                query_id=query_id,
            )
        )
    return results


def main() -> None:
    """CLI entry for lifecycle diagnostics."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run customer decision lifecycle diagnostics.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()
    results = asyncio.run(run_all_lifecycle_cases())
    if args.json:
        print(json.dumps([lifecycle_case_to_dict(result) for result in results], indent=2))
        return
    for result in results:
        print(f"=== {result.case_id} ===")
        print(result.label)
        print(
            "raw/mapped recall:",
            result.recall_mapping.get("raw_recall_count"),
            "/",
            result.recall_mapping.get("mapped_recall_count"),
        )
        print(
            "raw/mapped context:",
            result.context_mapping.get("raw_selected_count"),
            "/",
            result.context_mapping.get("mapped_selected_count"),
        )
        print("group coverage retrieval:", result.evidence_group_coverage_at_retrieval)
        print("group coverage budget:", result.evidence_group_coverage_at_budget)
        print()


if __name__ == "__main__":
    main()
