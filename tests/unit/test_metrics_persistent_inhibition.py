"""Hand-calculated persistent inhibition metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.evaluation.result import QueryResult, UseResult
from cogkurabench.metrics.persistent_inhibition import (
    compute_inhibition_trace_metrics,
    compute_persistent_inhibition_metrics,
    finalize_inhibition_trace_metrics,
    finalize_persistent_inhibition_metrics,
)
from cogkurabench.models import (
    BenchmarkQuery,
    BenchmarkUse,
    Capability,
    CompetitionDirection,
    InhibitionTraceObservation,
    PersistentInhibitionComparison,
    PersistentInhibitionContributionObservation,
    PersistentInhibitionExpectation,
    PersistentInhibitionObservation,
)


def _query(**kwargs: object) -> BenchmarkQuery:
    defaults = {
        "id": "q",
        "timestamp": datetime(2026, 4, 15, tzinfo=UTC),
        "capability": Capability.PERSISTENT_INHIBITION,
        "query": "test",
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)


def _observation(
    candidate: str,
    *,
    penalty: float = -0.2,
    selected: str = "gha",
    before: float = 0.4,
    after: float | None = None,
    crossed: bool = False,
    rank_before: int | None = 1,
    rank_after: int | None = 2,
) -> PersistentInhibitionObservation:
    activation_after = before + penalty if after is None else after
    return PersistentInhibitionObservation(
        candidate_source_event_ids=(candidate,),
        activation_before=before,
        activation_after=activation_after,
        stored_trace_count=1,
        evaluated_trace_count=1,
        matched_trace_count=1,
        effective_trace_count=1,
        inhibition_pressure=0.5,
        penalty=penalty,
        crossed_activation_threshold=crossed,
        rank_before=rank_before,
        rank_after=rank_after,
        contributions=(
            PersistentInhibitionContributionObservation(
                selected_source_event_ids=(selected,),
                direction=CompetitionDirection.PROACTIVE,
                induction_pressure=0.5,
                age_seconds=10.0,
                remaining_strength=0.5,
            ),
        ),
    )


def _trace(inhibited: str, selected: str = "gha") -> InhibitionTraceObservation:
    return InhibitionTraceObservation(
        use_id="use-1",
        selected_source_event_ids=(selected,),
        inhibited_source_event_ids=(inhibited,),
        direction=CompetitionDirection.PROACTIVE,
        induction_pressure=0.6,
    )


def _query_result(
    query_id: str,
    observations: tuple[PersistentInhibitionObservation, ...],
    metrics: dict[str, float],
) -> QueryResult:
    return QueryResult(
        query_id=query_id,
        capability=Capability.PERSISTENT_INHIBITION,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics=metrics,
        latency_ms=1.0,
        context_tokens=None,
        persistent_inhibition_observations=observations,
    )


def test_perfect_trace_induction() -> None:
    use = BenchmarkUse(
        id="use-1",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        query_id="q",
        selected_event_ids=("gha",),
        expected_inhibited_event_ids=("jenkins",),
    )
    metrics, diagnostics = compute_inhibition_trace_metrics(use, (_trace("jenkins"),))
    assert metrics["inhibition_trace_precision"] == 1.0
    assert metrics["inhibition_trace_recall"] == 1.0
    assert metrics["inhibition_trace_f1"] == 1.0
    assert metrics["unexpected_inhibition_trace_rate"] == 0.0
    assert diagnostics[0].classification == "expected"


def test_missed_inhibition_trace() -> None:
    use = BenchmarkUse(
        id="use-1",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        query_id="q",
        selected_event_ids=("gha",),
        expected_inhibited_event_ids=("jenkins",),
    )
    metrics, _diagnostics = compute_inhibition_trace_metrics(use, ())
    assert metrics["inhibition_trace_recall"] == 0.0
    assert metrics["inhibition_trace_precision"] == 1.0
    assert metrics["inhibition_trace_f1"] == 0.0


def test_unexpected_inhibition_trace() -> None:
    use = BenchmarkUse(
        id="use-1",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        query_id="q",
        selected_event_ids=("gha", "redis"),
        forbidden_inhibited_event_ids=(),
    )
    metrics, diagnostics = compute_inhibition_trace_metrics(use, (_trace("jenkins"),))
    assert metrics["inhibition_trace_precision"] == 0.0
    assert metrics["unexpected_inhibition_trace_rate"] == 1.0
    assert diagnostics[0].classification == "unexpected"


def test_perfect_persistent_effect() -> None:
    query = _query(
        expected_persistent_inhibition=(
            PersistentInhibitionExpectation(
                id="jenkins",
                candidate_event_ids=("jenkins",),
                selected_event_ids=("gha",),
            ),
        )
    )
    metrics, diagnostics = compute_persistent_inhibition_metrics(
        query,
        (_observation("jenkins"),),
        persistent_inhibition_supported=True,
    )
    assert metrics["persistent_inhibition_effect_precision"] == 1.0
    assert metrics["persistent_inhibition_effect_recall"] == 1.0
    assert metrics["persistent_inhibition_effect_f1"] == 1.0
    assert diagnostics[0].classification == "expected"


def test_unexpected_persistent_effect() -> None:
    query = _query(
        forbidden_persistent_inhibition=(
            PersistentInhibitionExpectation(
                id="db",
                candidate_event_ids=("postgres",),
                selected_event_ids=("gha",),
            ),
        )
    )
    metrics, diagnostics = compute_persistent_inhibition_metrics(
        query,
        (_observation("postgres"),),
        persistent_inhibition_supported=True,
    )
    assert metrics["persistent_inhibition_effect_precision"] == 0.0
    assert metrics["unexpected_persistent_inhibition_rate"] == 1.0
    assert diagnostics[0].classification == "forbidden"


def test_out_of_scope_false_suppression() -> None:
    query = _query(
        forbidden_persistent_inhibition=(
            PersistentInhibitionExpectation(
                id="isolated",
                candidate_event_ids=("jenkins",),
            ),
        ),
        persistent_inhibition_comparisons=(
            PersistentInhibitionComparison(
                candidate_event_ids=("jenkins",),
                scope_isolation=True,
            ),
        ),
    )
    metrics, _diagnostics = compute_persistent_inhibition_metrics(
        query,
        (_observation("jenkins"),),
        persistent_inhibition_supported=True,
    )
    assert metrics["persistent_inhibition_scope_isolation_accuracy"] == 0.0
    assert metrics["out_of_scope_inhibition_count"] == 1.0


def test_unsupported_backend_omits_effect_metrics() -> None:
    query = _query(
        expected_persistent_inhibition=(
            PersistentInhibitionExpectation(id="jenkins", candidate_event_ids=("jenkins",)),
        )
    )
    metrics, diagnostics = compute_persistent_inhibition_metrics(
        query,
        (_observation("jenkins"),),
        persistent_inhibition_supported=False,
    )
    assert metrics == {}
    assert diagnostics == ()


def test_recovery_and_repetition_ordering() -> None:
    fresh = _observation("jenkins", penalty=-0.1)
    repeated = _observation("jenkins", penalty=-0.4)
    later = _observation("jenkins", penalty=-0.2)
    latest = _observation("jenkins", penalty=-0.05)
    queries = {
        "single": _query(id="single"),
        "repeated": _query(
            id="repeated",
            persistent_inhibition_comparisons=(
                PersistentInhibitionComparison(
                    candidate_event_ids=("jenkins",),
                    stronger_than_query_id="single",
                ),
            ),
        ),
        "half": _query(
            id="half",
            persistent_inhibition_comparisons=(
                PersistentInhibitionComparison(
                    candidate_event_ids=("jenkins",),
                    weaker_than_query_id="repeated",
                ),
            ),
        ),
        "later": _query(
            id="later",
            persistent_inhibition_comparisons=(
                PersistentInhibitionComparison(
                    candidate_event_ids=("jenkins",),
                    weaker_than_query_id="half",
                ),
            ),
        ),
    }
    base_metrics = {"persistent_inhibition_effect_expected_total": 1.0}
    results = [
        _query_result("single", (fresh,), base_metrics),
        _query_result("repeated", (repeated,), base_metrics),
        _query_result("half", (later,), base_metrics),
        _query_result("later", (latest,), base_metrics),
    ]
    aggregated = finalize_persistent_inhibition_metrics(results, queries)
    assert aggregated["repetition_strengthening_accuracy"] == 1.0
    assert aggregated["inhibition_recovery_order_accuracy"] == 1.0


def test_wrong_rank_and_threshold() -> None:
    query = _query(
        expected_persistent_inhibition=(
            PersistentInhibitionExpectation(
                id="jenkins",
                candidate_event_ids=("jenkins",),
                expect_rank_worsening=True,
                expect_threshold_suppression=False,
            ),
        )
    )
    metrics, _diagnostics = compute_persistent_inhibition_metrics(
        query,
        (_observation("jenkins", rank_before=2, rank_after=1, crossed=True),),
        persistent_inhibition_supported=True,
    )
    assert metrics["persistent_inhibition_rank_effect_accuracy"] == 0.0
    assert metrics["persistent_inhibition_threshold_suppression_accuracy"] == 0.0


def test_trace_finalize_micro_averages() -> None:
    use = BenchmarkUse(
        id="use-1",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        query_id="q",
        selected_event_ids=("gha",),
        expected_inhibited_event_ids=("jenkins",),
    )
    metrics, diagnostics = compute_inhibition_trace_metrics(use, (_trace("jenkins"),))
    result = UseResult(
        use_id="use-1",
        source_query_id="q",
        selected_event_ids=("gha",),
        expected_inhibited_event_ids=("jenkins",),
        inhibition_traces=(_trace("jenkins"),),
        metrics=metrics,
        diagnostics=diagnostics,
    )
    aggregated = finalize_inhibition_trace_metrics((result,))
    assert aggregated["inhibition_trace_f1"] == 1.0
