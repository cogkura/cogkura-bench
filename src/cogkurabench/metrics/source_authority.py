"""Source-authority admission metrics.

Scores durable semantic state against fixture expectations. It does not
recompute Core's eligibility rules.
"""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    SourceAuthorityExpectation,
    SourceAuthorityObservation,
)


def _admission(expectation: SourceAuthorityExpectation, *, authority_enabled: bool) -> str:
    if not authority_enabled and expectation.control_admission is not None:
        return expectation.control_admission
    return expectation.admission


def _expected_present(expectation: SourceAuthorityExpectation, *, authority_enabled: bool) -> bool:
    admission = _admission(expectation, authority_enabled=authority_enabled)
    if admission == "none":
        return False
    if admission == "recurrence":
        return True
    return authority_enabled


def _matches_claim(
    observation: SourceAuthorityObservation,
    expectation: SourceAuthorityExpectation,
) -> bool:
    return (
        observation.subject == expectation.subject
        and observation.predicate == expectation.predicate
        and observation.object == expectation.object
    )


def compute_source_authority_metrics(
    query: BenchmarkQuery,
    observations: Sequence[SourceAuthorityObservation],
    *,
    source_authority_supported: bool,
    authority_enabled: bool,
    authority_invalid_count: int,
    authority_deferred_count: int,
) -> dict[str, float]:
    """Score one checkpoint. Rates are finalized across the run."""
    if not source_authority_supported:
        return {}
    if query.capability is not Capability.SOURCE_AUTHORITY and not query.expected_source_authority:
        return {}

    expected_present = 0
    matched_present = 0
    basis_checks = 0
    basis_passes = 0
    revision_checks = 0
    revision_passes = 0
    deferral_checks = 0
    deferral_passes = 0
    invalid_checks = 0
    invalid_passes = 0
    unauthorized = 0
    scope_leakage = 0
    mismatches = 0
    idempotency = 0
    matched_observations: set[int] = set()

    for expectation in query.expected_source_authority:
        should_exist = _expected_present(expectation, authority_enabled=authority_enabled)
        found = next(
            (
                (index, observation)
                for index, observation in enumerate(observations)
                if _matches_claim(observation, expectation)
            ),
            None,
        )
        if should_exist:
            expected_present += 1
            if found is None:
                mismatches += 1
                if query.repeat_consolidation:
                    idempotency += 1
                continue
            index, observation = found
            matched_observations.add(index)
            claim_ok = True
            basis_checks += 1
            admission = _admission(expectation, authority_enabled=authority_enabled)
            expected_basis = (
                "recurrence" if admission == "recurrence" else "explicit_source_authority"
            )
            if observation.promotion_basis == expected_basis:
                basis_passes += 1
            else:
                claim_ok = False
            if (
                expectation.support_count is not None
                and observation.support_count != expectation.support_count
            ):
                claim_ok = False
            if (
                expected_basis == "explicit_source_authority"
                and expectation.promotion_support_count is not None
                and observation.promotion_support_count != expectation.promotion_support_count
            ):
                claim_ok = False
            if expectation.supporting_event_ids and set(observation.supporting_event_ids) != set(
                expectation.supporting_event_ids
            ):
                claim_ok = False
            if expectation.semantic_revision_count is not None:
                revision_checks += 1
                if observation.semantic_revision_count == expectation.semantic_revision_count:
                    revision_passes += 1
                else:
                    claim_ok = False
            if claim_ok:
                matched_present += 1
            else:
                mismatches += 1
                if query.repeat_consolidation:
                    idempotency += 1
        elif found is not None:
            matched_observations.add(found[0])
            unauthorized += 1
            scope_leakage += 1
            mismatches += 1
        if authority_enabled and expectation.authority_deferred_count is not None:
            deferral_checks += 1
            if authority_deferred_count == expectation.authority_deferred_count:
                deferral_passes += 1
            else:
                mismatches += 1
        if authority_enabled and expectation.authority_invalid_count is not None:
            invalid_checks += 1
            if authority_invalid_count == expectation.authority_invalid_count:
                invalid_passes += 1
            else:
                mismatches += 1

    for index, _observation in enumerate(observations):
        if index not in matched_observations:
            unauthorized += 1
            mismatches += 1

    return {
        "source_authority_expected_present": float(expected_present),
        "source_authority_matched_present": float(matched_present),
        "source_authority_unauthorized": float(unauthorized),
        "source_authority_basis_checks": float(basis_checks),
        "source_authority_basis_passes": float(basis_passes),
        "source_authority_revision_checks": float(revision_checks),
        "source_authority_revision_passes": float(revision_passes),
        "source_authority_deferral_checks": float(deferral_checks),
        "source_authority_deferral_passes": float(deferral_passes),
        "source_authority_invalid_checks": float(invalid_checks),
        "source_authority_invalid_passes": float(invalid_passes),
        "source_authority_idempotency_violations": float(idempotency),
        "source_authority_scope_leakage": float(scope_leakage),
        "source_authority_declared_mismatches": float(mismatches),
    }


def finalize_source_authority_metrics(
    query_results: Sequence[QueryResult],
) -> dict[str, float]:
    """Sum checkpoint counts and emit rates. Empty denominators stay absent."""
    relevant = [
        result for result in query_results if "source_authority_expected_present" in result.metrics
    ]
    if not relevant:
        return {}

    def _total(key: str) -> float:
        return sum(float(result.metrics.get(key, 0.0)) for result in relevant)

    expected = _total("source_authority_expected_present")
    matched = _total("source_authority_matched_present")
    unauthorized = _total("source_authority_unauthorized")
    basis_checks = _total("source_authority_basis_checks")
    revision_checks = _total("source_authority_revision_checks")
    deferral_checks = _total("source_authority_deferral_checks")
    invalid_checks = _total("source_authority_invalid_checks")
    metrics = {
        "source_authority_expected_present": expected,
        "source_authority_matched_present": matched,
        "source_authority_unauthorized_promotion_count": unauthorized,
        "source_authority_idempotency_violations": _total(
            "source_authority_idempotency_violations"
        ),
        "source_authority_scope_leakage_count": _total("source_authority_scope_leakage"),
        "source_authority_declared_mismatch_count": _total("source_authority_declared_mismatches"),
    }
    if expected > 0:
        metrics["source_authority_admission_recall"] = matched / expected
    if matched + unauthorized > 0:
        metrics["source_authority_admission_precision"] = matched / (matched + unauthorized)
    if basis_checks > 0:
        metrics["source_authority_promotion_basis_accuracy"] = (
            _total("source_authority_basis_passes") / basis_checks
        )
    if revision_checks > 0:
        metrics["source_authority_revision_binding_accuracy"] = (
            _total("source_authority_revision_passes") / revision_checks
        )
    if deferral_checks > 0:
        metrics["source_authority_deferral_accuracy"] = (
            _total("source_authority_deferral_passes") / deferral_checks
        )
    if invalid_checks > 0:
        metrics["source_authority_invalid_accuracy"] = (
            _total("source_authority_invalid_passes") / invalid_checks
        )
    return metrics
