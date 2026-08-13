"""Benchmark execution runner."""

from __future__ import annotations

import platform
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from cogkurabench import __version__
from cogkurabench.backends.base import MemoryBackend
from cogkurabench.clock import BenchmarkClock
from cogkurabench.evaluation.evaluator import (
    aggregate_capability_results,
    apply_learning_deltas,
    evaluate_query,
    finalize_metamemory_metrics,
)
from cogkurabench.evaluation.report import write_result_json, write_summary_markdown
from cogkurabench.evaluation.result import (
    BenchmarkResult,
    CapabilityResult,
    EnvironmentInfo,
    QueryResult,
)
from cogkurabench.metrics.retrieval import retrieved_event_ids
from cogkurabench.models import (
    AssessmentRequest,
    BenchmarkAction,
    BenchmarkDataset,
    Capability,
    ContextRequest,
    FeedbackAction,
    ProjectEvent,
    QueryAction,
    RetrievalRequest,
)


class BenchmarkRunner:
    """Execute a benchmark dataset against a memory backend."""

    async def run(
        self,
        dataset: BenchmarkDataset,
        backend: MemoryBackend,
        *,
        results_dir: Path | None = None,
        write_results: bool = True,
    ) -> BenchmarkResult:
        """Run the benchmark and return scored results."""
        started_at = datetime.now(UTC)
        start_time = time.perf_counter()

        await backend.reset()

        ingested_ids: set[str] = set()
        pending_events: list[ProjectEvent] = list(dataset.events)
        pending_events.sort(key=lambda event: (event.timestamp, event.sequence, event.id))
        events_by_id = dataset.event_by_id()
        queries_by_id = dataset.query_by_id()

        query_results: list[QueryResult] = []
        actions_by_time: dict[datetime, list[BenchmarkAction]] = defaultdict(list)
        for action in dataset.actions:
            actions_by_time[action.timestamp].append(action)

        clock = BenchmarkClock(
            current=dataset.events[0].timestamp if dataset.events else started_at
        )

        for timestamp in sorted(actions_by_time):
            clock.advance_to(timestamp)

            newly_visible = [
                event
                for event in pending_events
                if event.timestamp <= timestamp and event.id not in ingested_ids
            ]
            if newly_visible:
                await backend.ingest(newly_visible)
                ingested_ids.update(event.id for event in newly_visible)

            await backend.prepare(as_of=clock.current)
            if backend.capabilities.maintain:
                await backend.maintain(as_of=clock.current)

            for action in sorted(
                actions_by_time[timestamp],
                key=lambda item: (item.sequence, type(item).__name__),
            ):
                if isinstance(action, QueryAction):
                    query = action.query
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
                    ranked_ids = retrieved_event_ids(
                        [event_id for item in response.items for event_id in item.source_event_ids]
                    )

                    context_response = None
                    should_select_context = (
                        backend.capabilities.select_context
                        and query.prompt_budget_tokens is not None
                    )
                    if should_select_context:
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

                    assessment_response = None
                    if backend.capabilities.assess and (
                        query.should_abstain or query.capability is Capability.METAMEMORY
                    ):
                        assessment_request = AssessmentRequest(
                            query_id=query.id,
                            query=query.query,
                            as_of=clock.current,
                            goal=query.goal,
                            valid_at=query.valid_at,
                            should_abstain=query.should_abstain,
                            entity_ids=query.entity_ids,
                            predicate=query.predicate,
                            object_value=query.object_value,
                        )
                        assessment_response = await backend.assess(assessment_request)

                    query_results.append(
                        evaluate_query(
                            query,
                            ranked_ids,
                            latency_ms=response.latency_ms,
                            events_by_id=events_by_id,
                            context_response=context_response,
                            assessment_response=assessment_response,
                            backend_metadata=dict(response.backend_metadata),
                        )
                    )

                elif isinstance(action, FeedbackAction):
                    if backend.capabilities.learn:
                        await backend.apply_feedback(action.feedback)

        query_results = apply_learning_deltas(query_results, queries_by_id)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        capability_results = aggregate_capability_results(query_results)
        metamemory_metrics = finalize_metamemory_metrics(query_results)
        if metamemory_metrics and Capability.METAMEMORY.value in capability_results:
            existing = capability_results[Capability.METAMEMORY.value]
            capability_results[Capability.METAMEMORY.value] = type(existing)(
                capability=existing.capability,
                query_count=existing.query_count,
                metrics={**dict(existing.metrics), **metamemory_metrics},
            )
        elif metamemory_metrics:
            capability_results[Capability.METAMEMORY.value] = CapabilityResult(
                capability=Capability.METAMEMORY,
                query_count=0,
                metrics=metamemory_metrics,
            )

        backend_version = backend.version
        environment_metadata: dict[str, object] = {}
        if backend.name == "cogkura" and backend_version is not None:
            environment_metadata["cogkura_version"] = backend_version

        result = BenchmarkResult(
            benchmark_version=__version__,
            dataset_version=dataset.manifest.name,
            backend_name=backend.name,
            backend_version=backend_version,
            started_at=started_at,
            duration_ms=duration_ms,
            capability_results=capability_results,
            query_results=tuple(query_results),
            environment=EnvironmentInfo(
                python_version=sys.version.split()[0],
                platform=platform.platform(),
                git_commit=_git_commit(),
                backend_configuration=environment_metadata,
            ),
        )

        if write_results:
            output_root = results_dir or Path("results")
            timestamp_label = started_at.strftime("%Y%m%dT%H%M%SZ")
            output_dir = output_root / dataset.manifest.name / backend.name
            write_result_json(result, output_dir / f"{timestamp_label}.json")
            write_summary_markdown(result, output_dir / f"{timestamp_label}.summary.md")

        return result


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
    commit = completed.stdout.strip()
    return commit or None
