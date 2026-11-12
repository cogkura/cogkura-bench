"""Hand-calculated authoritative correction metrics."""

from __future__ import annotations

from datetime import datetime

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.authoritative_corrections import (
    compute_authoritative_correction_metrics,
    finalize_authoritative_correction_metrics,
)
from cogkurabench.models import (
    AuthoritativeCorrectionExpectation,
    AuthoritativeCorrectionObservation,
    BenchmarkQuery,
    Capability,
)


def _query(
    expectations: tuple[AuthoritativeCorrectionExpectation, ...],
) -> BenchmarkQuery:
    return BenchmarkQuery(
        id="q",
        timestamp=datetime.fromisoformat("2026-10-25T10:00:00+00:00"),
        capability=Capability.AUTHORITATIVE_CORRECTION,
        query="payments-api migration execution strategy",
        expected_authoritative_corrections=expectations,
    )


def _expectation(presence: str) -> AuthoritativeCorrectionExpectation:
    return AuthoritativeCorrectionExpectation(
        id="claim",
        subject="payments-api",
        predicate="migration_execution_strategy",
        object="deployment_pipeline",
        presence=presence,
    )


def _observation() -> AuthoritativeCorrectionObservation:
    return AuthoritativeCorrectionObservation(
        subject="payments-api",
        predicate="migration_execution_strategy",
        object="deployment_pipeline",
        status="active",
        support_count=1,
        valid_from=None,
        valid_until=None,
        promotion_basis="explicit_source_authority",
        supporting_event_ids=("edit",),
        revision_count=1,
        relation="supersedes",
        recalled=True,
    )


def _finalize(counts: dict[str, float]) -> dict[str, float]:
    result = QueryResult(
        query_id="q",
        capability=Capability.AUTHORITATIVE_CORRECTION,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics=counts,
        latency_ms=1.0,
        context_tokens=None,
    )
    return finalize_authoritative_correction_metrics((result,))


def test_empty_denominator_omits_rates() -> None:
    counts = compute_authoritative_correction_metrics(
        _query((_expectation("never"),)),
        (),
        supported=True,
        corrections_enabled=True,
        corrections_deferred=0,
        corrections_invalid=0,
        corrections_applied=0,
        rendered="",
        recalled_objects=(),
    )
    finalized = _finalize(counts)
    assert "authoritative_correction_transition_precision" not in finalized
    assert "authoritative_correction_transition_recall" not in finalized
    assert finalized["authoritative_correction_unauthorized_transition_count"] == 0


def test_unexpected_memory_lowers_precision() -> None:
    absent = AuthoritativeCorrectionExpectation(
        id="other",
        subject="payments-api",
        predicate="migration_execution_strategy",
        object="application_startup",
        presence="never",
    )
    counts = compute_authoritative_correction_metrics(
        _query((absent,)),
        (_observation(),),
        supported=True,
        corrections_enabled=True,
        corrections_deferred=0,
        corrections_invalid=0,
        corrections_applied=0,
        rendered="",
        recalled_objects=(),
    )
    finalized = _finalize(counts)
    assert finalized["authoritative_correction_transition_precision"] == 0.0
    assert finalized["authoritative_correction_unauthorized_transition_count"] == 1
    assert finalized["authoritative_correction_undeclared_mismatch_count"] == 1
