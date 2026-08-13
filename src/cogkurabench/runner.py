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
from cogkurabench.evaluation.evaluator import aggregate_capability_results, evaluate_query
from cogkurabench.evaluation.report import write_result_json, write_summary_markdown
from cogkurabench.evaluation.result import BenchmarkResult, EnvironmentInfo, QueryResult
from cogkurabench.metrics.retrieval import retrieved_event_ids
from cogkurabench.models import (
    AssessmentRequest,
    BenchmarkAction,
    BenchmarkDataset,
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
                    )
                    response = await backend.retrieve(request)
                    ranked_ids = retrieved_event_ids(
                        [event_id for item in response.items for event_id in item.source_event_ids]
                    )
                    query_results.append(
                        evaluate_query(
                            query,
                            ranked_ids,
                            latency_ms=response.latency_ms,
                            backend_metadata=dict(response.backend_metadata),
                        )
                    )

                    if backend.capabilities.select_context and query.prompt_budget_tokens:
                        context_request = ContextRequest(
                            query_id=query.id,
                            query=query.query,
                            as_of=clock.current,
                            goal=query.goal,
                            valid_at=query.valid_at,
                            prompt_budget_tokens=query.prompt_budget_tokens,
                        )
                        await backend.select_context(context_request)

                    if backend.capabilities.assess:
                        assessment_request = AssessmentRequest(
                            query_id=query.id,
                            query=query.query,
                            as_of=clock.current,
                            goal=query.goal,
                            valid_at=query.valid_at,
                            should_abstain=query.should_abstain,
                        )
                        await backend.assess(assessment_request)

                elif isinstance(action, FeedbackAction):
                    if backend.capabilities.learn:
                        await backend.apply_feedback(action.feedback)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        capability_results = aggregate_capability_results(query_results)
        result = BenchmarkResult(
            benchmark_version=__version__,
            dataset_version=dataset.manifest.name,
            backend_name=backend.name,
            backend_version=backend.version,
            started_at=started_at,
            duration_ms=duration_ms,
            capability_results=capability_results,
            query_results=tuple(query_results),
            environment=EnvironmentInfo(
                python_version=sys.version.split()[0],
                platform=platform.platform(),
                git_commit=_git_commit(),
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
