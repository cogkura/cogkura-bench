"""Hand-calculated persistent-inhibition workload summaries."""

from __future__ import annotations

from cogkurabench.evaluation.result import QueryResult, UseResult
from cogkurabench.metrics.persistent_inhibition_workload import (
    logical_trace_key,
    summarize_persistent_inhibition_workload,
    trace_growth_checkpoints,
)
from cogkurabench.models import (
    Capability,
    CompetitionDirection,
    InhibitionTraceObservation,
    PersistentInhibitionObservation,
    RetrievedItem,
)


def _trace(
    use_id: str,
    selected: str,
    inhibited: str,
    scope: str,
) -> InhibitionTraceObservation:
    return InhibitionTraceObservation(
        use_id=use_id,
        selected_source_event_ids=(selected,),
        inhibited_source_event_ids=(inhibited,),
        direction=CompetitionDirection.PROACTIVE,
        induction_pressure=0.3,
        scope_key=scope,
    )


def _item(event_id: str, score: float, rank: int) -> RetrievedItem:
    return RetrievedItem(source_event_ids=(event_id,), text=event_id, score=score, rank=rank)


def _query(
    query_id: str,
    items: tuple[RetrievedItem, ...],
    observations: tuple[PersistentInhibitionObservation, ...] = (),
) -> QueryResult:
    return QueryResult(
        query_id=query_id,
        capability=Capability.PERSISTENT_INHIBITION,
        retrieved_event_ids=tuple(item.source_event_ids[0] for item in items),
        expected_event_ids=("gold",),
        metrics={},
        latency_ms=1.0,
        context_tokens=None,
        retrieved_items=items,
        persistent_inhibition_observations=observations,
    )


def _observation(
    *,
    penalty: float,
    stored: int = 1,
    rank_before: int | None = 1,
    rank_after: int | None = 1,
    threshold: bool = False,
) -> PersistentInhibitionObservation:
    return PersistentInhibitionObservation(
        candidate_source_event_ids=("loser",),
        activation_before=0.5,
        activation_after=0.4,
        stored_trace_count=stored,
        evaluated_trace_count=stored,
        matched_trace_count=1 if stored else 0,
        effective_trace_count=1 if penalty < 0 else 0,
        inhibition_pressure=0.2,
        penalty=penalty,
        crossed_activation_threshold=threshold,
        rank_before=rank_before,
        rank_after=rank_after,
    )


def _use(
    use_id: str,
    traces: tuple[InhibitionTraceObservation, ...],
) -> UseResult:
    return UseResult(
        use_id=use_id,
        source_query_id=f"{use_id}-src",
        selected_event_ids=("winner",),
        expected_inhibited_event_ids=("loser",),
        inhibition_traces=traces,
        metrics={},
    )


def test_logical_trace_key_sorts_event_ids() -> None:
    trace = InhibitionTraceObservation(
        use_id="u",
        selected_source_event_ids=("b", "a"),
        inhibited_source_event_ids=("d", "c"),
        direction=CompetitionDirection.RETROACTIVE,
        induction_pressure=0.2,
        scope_key="slot",
    )
    assert logical_trace_key(trace) == (("a", "b"), ("c", "d"), "slot")


def test_summary_counts_repeats_rank_threshold_and_drift() -> None:
    repeated = _trace("u1", "winner", "loser", "slot")
    again = _trace("u2", "winner", "loser", "slot")
    other = _trace("u3", "other", "rival", "other-slot")
    uses = (
        _use("u1", (repeated,)),
        _use("u2", (again,)),
        _use("u3", (other, other)),
    )
    penalty = _observation(penalty=-0.1, rank_before=2, rank_after=2)
    ranked = _observation(penalty=-0.2, rank_before=1, rank_after=3)
    suppressed = _observation(penalty=-0.05, stored=64, threshold=True)
    application = (
        _query("q-penalty", (_item("a", 0.5, 1),), (penalty,)),
        _query("q-rank", (_item("b", 0.4, 1),), (ranked,)),
        _query("q-threshold", (_item("c", 0.3, 1),), (suppressed,)),
        _query("q-same", (_item("d", 0.2, 1),)),
        _query("q-unattr", (_item("e", 0.1, 1),)),
    )
    recording = (
        _query("q-penalty", (_item("a", 0.8, 1),)),
        _query("q-rank", (_item("b", 0.4, 1),)),
        _query("q-threshold", (_item("c", 0.3, 1),)),
        _query("q-same", (_item("d", 0.2, 1),)),
        _query("q-unattr", (_item("other", 0.1, 1),)),
    )
    control = (
        _query("q-penalty", (_item("a", 0.8, 1),)),
        _query("q-rank", (_item("b", 0.4, 1),)),
        _query("q-threshold", (_item("c", 0.3, 1),)),
        _query("q-same", (_item("d", 0.7, 1),)),
        _query("q-unattr", (_item("other", 0.1, 1),)),
    )
    summary = summarize_persistent_inhibition_workload(
        application_queries=application,
        application_uses=uses,
        recording_queries=recording,
        control_queries=control,
    )
    assert summary.trace_count == 4
    assert summary.unique_trace_pair_count == 2
    assert summary.repeated_trace_count == 2
    assert summary.scope_key_count == 2
    assert summary.max_traces_per_use == 2
    assert summary.queries_with_effective_traces == 3
    assert summary.queries_with_penalty == 3
    assert summary.rank_change_count == 1
    assert summary.threshold_suppression_count == 1
    assert summary.result_change_count == 1
    assert summary.unattributed_change_count == 1
    assert summary.recording_only_control_drift_count == 1
    assert summary.memory_saturation_count == 1
    assert summary.trace_saturation_count == 0


def test_trace_growth_checkpoints_split_ordered_uses() -> None:
    uses = (
        _use("u1", (_trace("u1", "winner", "loser", "slot"),)),
        _use("u2", (_trace("u2", "winner", "loser", "slot"),)),
        _use("u3", (_trace("u3", "other", "rival", "other"),)),
    )
    early, middle, late = trace_growth_checkpoints(uses)
    assert early["trace_count"] == 1
    assert early["repeated_trace_count"] == 0
    assert middle["trace_count"] == 2
    assert middle["repeated_trace_count"] == 1
    assert late["unique_trace_pair_count"] == 2
    assert late["repeated_trace_count"] == 1
