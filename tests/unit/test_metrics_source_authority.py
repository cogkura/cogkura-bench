"""Hand-calculated source-authority admission metrics."""

from __future__ import annotations

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.metrics.source_authority import (
    compute_source_authority_metrics,
    finalize_source_authority_metrics,
)
from cogkurabench.models import (
    Capability,
    SourceAuthorityExpectation,
    SourceAuthorityObservation,
)


def _expectation(expectation_id: str, admission: str) -> SourceAuthorityExpectation:
    return SourceAuthorityExpectation(
        id=expectation_id,
        subject="payments-api",
        predicate="migration_execution_strategy",
        object="deployment_pipeline" if admission != "none" else "application_startup",
        admission=admission,
        support_count=1 if admission == "authority" else None,
        promotion_support_count=1 if admission == "authority" else None,
        semantic_revision_count=1 if admission == "authority" else None,
    )


def _observation(obj: str, basis: str) -> SourceAuthorityObservation:
    return SourceAuthorityObservation(
        subject="payments-api",
        predicate="migration_execution_strategy",
        object=obj,
        status="active",
        support_count=1,
        promotion_basis=basis,
        promotion_support_count=1,
        supporting_event_ids=("evt",),
        semantic_revision_count=1,
    )


def _query(expectations: tuple[SourceAuthorityExpectation, ...]) -> object:
    from datetime import datetime

    from cogkurabench.models import BenchmarkQuery

    return BenchmarkQuery(
        id="q",
        timestamp=datetime.fromisoformat("2026-05-01T12:00:00+00:00"),
        capability=Capability.SOURCE_AUTHORITY,
        query="payments-api semantic state",
        expected_source_authority=expectations,
    )


def test_empty_denominator_omits_rates() -> None:
    query = _query((_expectation("absent", "none"),))
    counts = compute_source_authority_metrics(
        query,  # type: ignore[arg-type]
        (),
        source_authority_supported=True,
        authority_enabled=True,
        authority_invalid_count=0,
        authority_deferred_count=0,
    )
    result = QueryResult(
        query_id="q",
        capability=Capability.SOURCE_AUTHORITY,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics=counts,
        latency_ms=1.0,
        context_tokens=None,
    )
    finalized = finalize_source_authority_metrics((result,))
    assert "source_authority_admission_precision" not in finalized
    assert "source_authority_admission_recall" not in finalized
    assert finalized["source_authority_unauthorized_promotion_count"] == 0


def test_precision_counts_unexpected_promotions() -> None:
    query = _query((_expectation("wanted", "authority"),))
    counts = compute_source_authority_metrics(
        query,  # type: ignore[arg-type]
        (
            _observation("deployment_pipeline", "explicit_source_authority"),
            _observation("application_startup", "explicit_source_authority"),
        ),
        source_authority_supported=True,
        authority_enabled=True,
        authority_invalid_count=0,
        authority_deferred_count=0,
    )
    result = QueryResult(
        query_id="q",
        capability=Capability.SOURCE_AUTHORITY,
        retrieved_event_ids=(),
        expected_event_ids=(),
        metrics=counts,
        latency_ms=1.0,
        context_tokens=None,
    )
    finalized = finalize_source_authority_metrics((result,))
    assert finalized["source_authority_admission_recall"] == 1.0
    assert finalized["source_authority_admission_precision"] == 0.5
    assert finalized["source_authority_unauthorized_promotion_count"] == 1
    assert finalized["source_authority_promotion_basis_accuracy"] == 1.0


def test_unsupported_backend_emits_no_counts() -> None:
    query = _query((_expectation("wanted", "authority"),))
    assert (
        compute_source_authority_metrics(
            query,  # type: ignore[arg-type]
            (),
            source_authority_supported=False,
            authority_enabled=False,
            authority_invalid_count=0,
            authority_deferred_count=0,
        )
        == {}
    )
