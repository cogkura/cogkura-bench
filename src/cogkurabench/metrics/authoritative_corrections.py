"""Authoritative correction metrics.

Scores persisted semantic state and retrieval against fixture expectations.
It does not recompute Core's correction rules.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.models import (
    AuthoritativeCorrectionExpectation,
    AuthoritativeCorrectionObservation,
    BenchmarkQuery,
    Capability,
)


def _expected_present(
    expectation: AuthoritativeCorrectionExpectation,
    *,
    corrections_enabled: bool,
) -> bool:
    if expectation.presence == "always":
        return True
    if expectation.presence == "never":
        return False
    if expectation.presence == "when_enabled":
        return corrections_enabled
    return not corrections_enabled


def _same_claim(
    observation: AuthoritativeCorrectionObservation,
    expectation: AuthoritativeCorrectionExpectation,
) -> bool:
    return (
        observation.subject == expectation.subject
        and observation.predicate == expectation.predicate
        and observation.object == expectation.object
    )


def _same_time(left: datetime | None, right: datetime | None) -> bool:
    if left is None or right is None:
        return left is right
    return left == right


def compute_authoritative_correction_metrics(
    query: BenchmarkQuery,
    observations: Sequence[AuthoritativeCorrectionObservation],
    *,
    supported: bool,
    corrections_enabled: bool,
    corrections_deferred: int,
    corrections_invalid: int,
    corrections_applied: int,
    rendered: str,
    recalled_objects: Sequence[str],
) -> dict[str, float]:
    """Score one checkpoint. Rates are finalized across the run."""
    if not supported:
        return {}
    if (
        query.capability is not Capability.AUTHORITATIVE_CORRECTION
        and not query.expected_authoritative_corrections
    ):
        return {}

    expected_present = 0
    matched_present = 0
    mismatches = 0
    unauthorized = 0
    knowledge_time = 0
    stale_context = 0
    false_suppression = 0
    incorrect_current = 0
    incorrect_historical = 0
    boundary_checks = 0
    boundary_passes = 0
    provenance_checks = 0
    provenance_passes = 0
    deferral_checks = 0
    deferral_passes = 0
    invalid_checks = 0
    invalid_passes = 0
    recall_checks = 0
    recall_passes = 0
    idempotency = 0
    matched_observations: set[int] = set()
    historical = query.valid_at is not None

    def _fail(expectation: AuthoritativeCorrectionExpectation) -> None:
        nonlocal mismatches, knowledge_time, stale_context, false_suppression
        nonlocal incorrect_current, incorrect_historical, unauthorized
        mismatches += 1
        if historical:
            incorrect_historical += 1
        else:
            incorrect_current += 1
        if expectation.failure_class == "knowledge_time":
            knowledge_time += 1
        elif expectation.failure_class == "stale_context":
            stale_context += 1
        elif expectation.failure_class == "false_suppression":
            false_suppression += 1
        elif expectation.failure_class == "unauthorized":
            unauthorized += 1

    for expectation in query.expected_authoritative_corrections:
        should_exist = _expected_present(expectation, corrections_enabled=corrections_enabled)
        found = next(
            (
                (index, observation)
                for index, observation in enumerate(observations)
                if _same_claim(observation, expectation)
            ),
            None,
        )
        if should_exist:
            expected_present += 1
            if found is None:
                _fail(expectation)
                continue
            index, observation = found
            matched_observations.add(index)
            claim_ok = True
            if expectation.status is not None and observation.status != expectation.status:
                claim_ok = False
            if (
                expectation.support_count is not None
                and observation.support_count != expectation.support_count
            ):
                claim_ok = False
            if (
                expectation.promotion_basis is not None
                and observation.promotion_basis != expectation.promotion_basis
            ):
                claim_ok = False
            if expectation.supporting_event_ids:
                provenance_checks += 1
                if set(observation.supporting_event_ids) == set(expectation.supporting_event_ids):
                    provenance_passes += 1
                else:
                    claim_ok = False
            if expectation.valid_from is not None or expectation.valid_until is not None:
                boundary_checks += 1
                bounds_ok = True
                if expectation.valid_from is not None and not _same_time(
                    observation.valid_from, expectation.valid_from
                ):
                    bounds_ok = False
                if expectation.valid_until is not None and not _same_time(
                    observation.valid_until, expectation.valid_until
                ):
                    bounds_ok = False
                if bounds_ok:
                    boundary_passes += 1
                else:
                    claim_ok = False
            if (
                expectation.revision_count is not None
                and observation.revision_count != expectation.revision_count
            ):
                claim_ok = False
                if query.extra_consolidations:
                    idempotency += 1
            if expectation.relation is not None and observation.relation != expectation.relation:
                claim_ok = False
            if claim_ok:
                matched_present += 1
            else:
                _fail(expectation)
        elif found is not None:
            matched_observations.add(found[0])
            _fail(expectation)
        if expectation.recall_present is True and should_exist:
            recall_checks += 1
            if expectation.object in recalled_objects:
                recall_passes += 1
            else:
                _fail(expectation)
        elif expectation.recall_present is False and not should_exist:
            recall_checks += 1
            if expectation.object not in recalled_objects:
                recall_passes += 1
            else:
                _fail(expectation)
        if corrections_enabled and expectation.corrections_deferred_count is not None:
            deferral_checks += 1
            if corrections_deferred == expectation.corrections_deferred_count:
                deferral_passes += 1
            else:
                mismatches += 1
        if corrections_enabled and expectation.corrections_invalid_count is not None:
            invalid_checks += 1
            if corrections_invalid == expectation.corrections_invalid_count:
                invalid_passes += 1
            else:
                mismatches += 1

    for index, _observation in enumerate(observations):
        if index not in matched_observations:
            unauthorized += 1
            mismatches += 1
            if historical:
                incorrect_historical += 1
            else:
                incorrect_current += 1

    if corrections_enabled:
        for phrase in query.render_forbidden:
            if phrase in rendered:
                stale_context += 1
                mismatches += 1
                incorrect_current += 1
        for phrase in query.render_required:
            if phrase not in rendered:
                false_suppression += 1
                mismatches += 1
                incorrect_current += 1

    if query.extra_consolidations and corrections_applied > 0:
        idempotency += 1
        mismatches += 1

    return {
        "authoritative_correction_expected_present": float(expected_present),
        "authoritative_correction_matched_present": float(matched_present),
        "authoritative_correction_mismatches": float(mismatches),
        "authoritative_correction_unauthorized": float(unauthorized),
        "authoritative_correction_knowledge_time": float(knowledge_time),
        "authoritative_correction_stale_context": float(stale_context),
        "authoritative_correction_false_suppression": float(false_suppression),
        "authoritative_correction_incorrect_current": float(incorrect_current),
        "authoritative_correction_incorrect_historical": float(incorrect_historical),
        "authoritative_correction_boundary_checks": float(boundary_checks),
        "authoritative_correction_boundary_passes": float(boundary_passes),
        "authoritative_correction_provenance_checks": float(provenance_checks),
        "authoritative_correction_provenance_passes": float(provenance_passes),
        "authoritative_correction_deferral_checks": float(deferral_checks),
        "authoritative_correction_deferral_passes": float(deferral_passes),
        "authoritative_correction_invalid_checks": float(invalid_checks),
        "authoritative_correction_invalid_passes": float(invalid_passes),
        "authoritative_correction_recall_checks": float(recall_checks),
        "authoritative_correction_recall_passes": float(recall_passes),
        "authoritative_correction_idempotency_violations": float(idempotency),
        "authoritative_correction_checkpoints": 1.0,
        "authoritative_correction_clean_checkpoints": 1.0 if mismatches == 0 else 0.0,
    }


def finalize_authoritative_correction_metrics(
    query_results: Sequence[QueryResult],
) -> dict[str, float]:
    """Sum checkpoint counts and emit rates. Empty denominators stay absent."""
    relevant = [
        result
        for result in query_results
        if "authoritative_correction_expected_present" in result.metrics
    ]
    if not relevant:
        return {}

    def _total(key: str) -> float:
        return sum(float(result.metrics.get(key, 0.0)) for result in relevant)

    expected = _total("authoritative_correction_expected_present")
    matched = _total("authoritative_correction_matched_present")
    unauthorized = _total("authoritative_correction_unauthorized")
    boundary_checks = _total("authoritative_correction_boundary_checks")
    provenance_checks = _total("authoritative_correction_provenance_checks")
    deferral_checks = _total("authoritative_correction_deferral_checks")
    recall_checks = _total("authoritative_correction_recall_checks")
    checkpoints = _total("authoritative_correction_checkpoints")
    metrics: dict[str, float] = {
        "authoritative_correction_unauthorized_transition_count": unauthorized,
        "authoritative_correction_incorrect_current_count": _total(
            "authoritative_correction_incorrect_current"
        ),
        "authoritative_correction_incorrect_historical_count": _total(
            "authoritative_correction_incorrect_historical"
        ),
        "authoritative_correction_knowledge_time_leak_count": _total(
            "authoritative_correction_knowledge_time"
        ),
        "authoritative_correction_stale_context_leak_count": _total(
            "authoritative_correction_stale_context"
        ),
        "authoritative_correction_false_suppression_count": _total(
            "authoritative_correction_false_suppression"
        ),
        "authoritative_correction_idempotency_violations": _total(
            "authoritative_correction_idempotency_violations"
        ),
        "authoritative_correction_undeclared_mismatch_count": _total(
            "authoritative_correction_mismatches"
        ),
    }
    if expected > 0:
        metrics["authoritative_correction_transition_recall"] = matched / expected
    if matched + unauthorized > 0:
        metrics["authoritative_correction_transition_precision"] = matched / (
            matched + unauthorized
        )
    if checkpoints > 0:
        metrics["authoritative_correction_state_accuracy"] = (
            _total("authoritative_correction_clean_checkpoints") / checkpoints
        )
    if boundary_checks > 0:
        metrics["authoritative_correction_temporal_boundary_accuracy"] = (
            _total("authoritative_correction_boundary_passes") / boundary_checks
        )
    if provenance_checks > 0:
        metrics["authoritative_correction_revision_provenance_accuracy"] = (
            _total("authoritative_correction_provenance_passes") / provenance_checks
        )
    if deferral_checks > 0:
        metrics["authoritative_correction_conflict_deferral_accuracy"] = (
            _total("authoritative_correction_deferral_passes") / deferral_checks
        )
    if recall_checks > 0:
        metrics["authoritative_correction_retrieval_accuracy"] = (
            _total("authoritative_correction_recall_passes") / recall_checks
        )
    return metrics


def _recalled_objects(metadata: Mapping[str, object]) -> tuple[str, ...]:
    raw = metadata.get("recalled_semantic_objects", ())
    if isinstance(raw, list | tuple):
        return tuple(str(item) for item in raw)
    return ()
