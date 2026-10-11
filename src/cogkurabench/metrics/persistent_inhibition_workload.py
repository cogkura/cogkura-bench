"""Workload summaries for persistent inhibition across longer histories."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cogkurabench.evaluation.result import QueryResult, UseResult
from cogkurabench.models import InhibitionTraceObservation, PersistentInhibitionObservation

_TRACE_SATURATION = 32
_MEMORY_SATURATION = 64


@dataclass(frozen=True, slots=True)
class PersistentInhibitionWorkloadSummary:
    """Aggregate trace and retrieval effects for one workload run."""

    use_count: int
    uses_with_traces: int
    trace_count: int
    unique_trace_pair_count: int
    repeated_trace_count: int
    max_traces_per_use: int
    max_traces_per_inhibited_memory: int
    scope_key_count: int
    query_count: int
    queries_with_stored_traces: int
    queries_with_matched_traces: int
    queries_with_effective_traces: int
    queries_with_penalty: int
    rank_change_count: int
    threshold_suppression_count: int
    result_change_count: int
    unattributed_change_count: int
    recording_only_control_drift_count: int
    trace_saturation_count: int
    memory_saturation_count: int


def logical_trace_key(
    trace: InhibitionTraceObservation,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Stable provenance key for one inhibitory relationship."""
    return (
        tuple(sorted(trace.selected_source_event_ids)),
        tuple(sorted(trace.inhibited_source_event_ids)),
        trace.scope_key or "",
    )


def _retrieval_signature(
    query_result: QueryResult,
) -> tuple[tuple[tuple[str, ...], float | None, int], ...]:
    return tuple(
        (item.source_event_ids, item.score, item.rank) for item in query_result.retrieved_items
    )


def _has_penalty(query_result: QueryResult) -> bool:
    return any(
        observation.penalty < 0 for observation in query_result.persistent_inhibition_observations
    )


def trace_growth_checkpoints(
    uses: Sequence[UseResult],
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Cumulative trace counts at the early, middle, and late thirds of use history."""
    ordered = list(uses)
    if not ordered:
        empty = {
            "uses": 0,
            "trace_count": 0,
            "unique_trace_pair_count": 0,
            "repeated_trace_count": 0,
        }
        return empty, dict(empty), dict(empty)
    bounds = (
        max(1, len(ordered) // 3),
        max(2, (2 * len(ordered)) // 3),
        len(ordered),
    )
    snapshots: list[dict[str, int]] = []
    for end in bounds:
        window = ordered[:end]
        traces = [trace for use in window for trace in use.inhibition_traces]
        unique = {logical_trace_key(trace) for trace in traces}
        snapshots.append(
            {
                "uses": len(window),
                "trace_count": len(traces),
                "unique_trace_pair_count": len(unique),
                "repeated_trace_count": len(traces) - len(unique),
            }
        )
    return snapshots[0], snapshots[1], snapshots[2]


def summarize_persistent_inhibition_workload(
    *,
    application_queries: Sequence[QueryResult],
    application_uses: Sequence[UseResult],
    recording_queries: Sequence[QueryResult] | None = None,
    control_queries: Sequence[QueryResult] | None = None,
) -> PersistentInhibitionWorkloadSummary:
    """Summarize traces and retrieval differences for one workload."""
    traces = [trace for use in application_uses for trace in use.inhibition_traces]
    unique_pairs = {logical_trace_key(trace) for trace in traces}
    scope_keys = {trace.scope_key for trace in traces if trace.scope_key}
    per_memory: dict[tuple[str, ...], int] = {}
    for trace in traces:
        key = tuple(sorted(trace.inhibited_source_event_ids))
        per_memory[key] = per_memory.get(key, 0) + 1
    max_per_use = max((len(use.inhibition_traces) for use in application_uses), default=0)
    max_per_memory = max(per_memory.values(), default=0)

    stored = matched = effective = penalized = 0
    rank_changes = threshold = 0
    memory_saturation = 0
    for query_result in application_queries:
        observations = query_result.persistent_inhibition_observations
        if any(item.stored_trace_count > 0 for item in observations):
            stored += 1
        if any(item.matched_trace_count > 0 for item in observations):
            matched += 1
        if any(item.effective_trace_count > 0 for item in observations):
            effective += 1
        if any(item.penalty < 0 for item in observations):
            penalized += 1
        if any(_rank_worsened(item) for item in observations):
            rank_changes += 1
        if any(item.crossed_activation_threshold for item in observations):
            threshold += 1
        if any(item.stored_trace_count >= _MEMORY_SATURATION for item in observations):
            memory_saturation += 1

    recording_by_id = {item.query_id: item for item in recording_queries or ()}
    control_by_id = {item.query_id: item for item in control_queries or ()}
    result_changes = 0
    unattributed = 0
    recording_drift = 0
    for query_result in application_queries:
        recording = recording_by_id.get(query_result.query_id)
        if recording is not None and (
            query_result.retrieved_event_ids != recording.retrieved_event_ids
        ):
            result_changes += 1
        if recording is not None and _retrieval_signature(query_result) != _retrieval_signature(
            recording
        ):
            if not _has_penalty(query_result):
                unattributed += 1
        control = control_by_id.get(query_result.query_id)
        if (
            control is not None
            and recording is not None
            and _retrieval_signature(control) != _retrieval_signature(recording)
        ):
            recording_drift += 1

    return PersistentInhibitionWorkloadSummary(
        use_count=len(application_uses),
        uses_with_traces=sum(1 for use in application_uses if use.inhibition_traces),
        trace_count=len(traces),
        unique_trace_pair_count=len(unique_pairs),
        repeated_trace_count=len(traces) - len(unique_pairs),
        max_traces_per_use=max_per_use,
        max_traces_per_inhibited_memory=max_per_memory,
        scope_key_count=len(scope_keys),
        query_count=len(application_queries),
        queries_with_stored_traces=stored,
        queries_with_matched_traces=matched,
        queries_with_effective_traces=effective,
        queries_with_penalty=penalized,
        rank_change_count=rank_changes,
        threshold_suppression_count=threshold,
        result_change_count=result_changes,
        unattributed_change_count=unattributed,
        recording_only_control_drift_count=recording_drift,
        trace_saturation_count=sum(
            1 for use in application_uses if len(use.inhibition_traces) >= _TRACE_SATURATION
        ),
        memory_saturation_count=memory_saturation,
    )


def _rank_worsened(observation: PersistentInhibitionObservation) -> bool:
    return (
        observation.rank_before is not None
        and observation.rank_after is not None
        and observation.rank_after > observation.rank_before
    )
