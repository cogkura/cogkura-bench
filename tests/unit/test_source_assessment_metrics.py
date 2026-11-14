"""Hand-calculated source check scoring, including unknown and missing outputs."""

from __future__ import annotations

from dataclasses import replace

import pytest

from cogkurabench.exceptions import ValidationError
from cogkurabench.metrics.source_assessment import (
    compute_source_assessment_metrics,
    finalize_source_assessment_metrics,
)
from cogkurabench.source_models import (
    EvidenceCoverageObservation,
    SourceAssessmentExpectation,
    SourceAssessmentObservation,
    SourceInspectionSpec,
)


def observation() -> SourceAssessmentObservation:
    return SourceAssessmentObservation(
        state="known",
        conflict="none_observed",
        conflict_complete=True,
        cross_source_disagreement=False,
        independence="unknown",
        inventory_complete=True,
        decision_history="unavailable",
        reasons=(),
        quality=EvidenceCoverageObservation(True, True, False, None, False, 1, 1, 1, 0, 1),
        revisions=(),
        event_ids=("a",),
        pending_count=0,
        indeterminate_revision_count=0,
        transition_event_ids=(),
        transition_effective_times=(),
        unmapped_evidence_count=0,
        decisions=(),
        decisions_available=False,
        decisions_complete=None,
        decisions_truncated=None,
    )


def test_hand_calculated_mismatch_and_non_applicable_relation() -> None:
    gold = SourceAssessmentExpectation(
        {
            "state": "known",
            "quality.locator_complete": True,
            "quality.relation_complete": None,
            "event_ids": ("b",),
        }
    )
    metrics = compute_source_assessment_metrics(
        gold, observation(), supported=True, decisions_supported=False
    )
    assert metrics["source_assessment_accuracy"] == 0.5
    assert metrics["source_assessment_mismatch_count"] == 2
    assert metrics["source_completeness_accuracy"] == 0.5
    assert metrics["source_attribution_accuracy"] == 0


def test_unsupported_is_na_but_missing_supported_payload_fails() -> None:
    gold = SourceAssessmentExpectation({"state": "unknown"})
    assert (
        compute_source_assessment_metrics(gold, None, supported=False, decisions_supported=False)
        == {}
    )
    metrics = compute_source_assessment_metrics(
        gold, None, supported=True, decisions_supported=False
    )
    assert metrics["source_assessment_accuracy"] == 0


def test_independence_unknown_is_not_confidence_and_false_completeness_fails() -> None:
    gold = SourceAssessmentExpectation(
        {
            "state": "indeterminate",
            "inventory_complete": False,
            "independence": "unknown",
            "event_ids_excludes": ("future",),
        }
    )
    forged = replace(observation(), independence="independent", event_ids=("future",))
    metrics = compute_source_assessment_metrics(
        gold, forged, supported=True, decisions_supported=False
    )
    assert metrics["source_false_certainty_count"] == 3
    assert metrics["source_future_leak_count"] == 1
    assert metrics["source_assessment_accuracy"] == 0


def test_diagnostics_na_when_off_and_not_a_fabricated_empty_history() -> None:
    gold = SourceAssessmentExpectation({"state": "known"}, {"decisions_available": True})
    off = compute_source_assessment_metrics(
        gold, observation(), supported=True, decisions_supported=False
    )
    on = compute_source_assessment_metrics(
        gold, observation(), supported=True, decisions_supported=True
    )
    assert off["source_assessment_accuracy"] == 1
    assert on["source_assessment_accuracy"] == 0.5


def test_micro_average_and_conflict_precision_recall() -> None:
    rows = [
        {
            "source_assessment_check_count": 3,
            "source_assessment_match_count": 2,
            "source_assessment_mismatch_count": 1,
            "source_conflict_matched_count": 1,
            "source_conflict_observed_count": 2,
            "source_conflict_expected_count": 1,
        },
        {
            "source_assessment_check_count": 1,
            "source_assessment_match_count": 1,
            "source_assessment_mismatch_count": 0,
            "source_conflict_matched_count": 0,
            "source_conflict_observed_count": 0,
            "source_conflict_expected_count": 1,
        },
    ]
    metrics = finalize_source_assessment_metrics(rows)
    assert metrics["source_assessment_accuracy"] == 0.75
    assert metrics["source_assessment_mismatch_count"] == 1
    assert metrics["source_conflict_precision"] == metrics["source_conflict_recall"] == 0.5


@pytest.mark.parametrize(
    "kwargs", ({"max_revisions": 0}, {"max_evidence": True}, {"qualifiers": {"nested": {"x": 1}}})
)
def test_bad_inspection_inputs_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SourceInspectionSpec("service", "policy", **kwargs)


@pytest.mark.parametrize(
    "checks",
    (
        {"state": "imaginary"},
        {"state": "known", "trust_score": 1},
        {"state": "known", "pending_count": True},
        {"state": "known", "event_ids": "not-a-list"},
    ),
)
def test_bad_gold_is_not_silently_ignored(checks: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SourceAssessmentExpectation(checks)


def test_backend_metadata_cannot_supply_source_gold_answers() -> None:
    from datetime import UTC, datetime

    from cogkurabench.evaluation.evaluator import evaluate_query
    from cogkurabench.models import BenchmarkQuery, Capability

    query = BenchmarkQuery(
        id="neutral",
        query="policy",
        timestamp=datetime(2026, 11, 1, tzinfo=UTC),
        capability=Capability.SOURCE_ASSESSMENT,
        source_inspection=SourceInspectionSpec("service", "policy"),
        expected_source_assessment=SourceAssessmentExpectation({"state": "known"}),
    )
    result = evaluate_query(
        query,
        (),
        latency_ms=0,
        source_assessment_supported=True,
        backend_metadata={"source_assessment": {"state": "known", "accuracy": 1}},
    )
    assert result.metrics["source_assessment_accuracy"] == 0
    result = evaluate_query(
        query,
        (),
        latency_ms=0,
        source_assessment_supported=True,
        source_assessment=observation(),
        backend_metadata={"source_assessment": {"state": "wrong"}},
    )
    assert result.metrics["source_assessment_accuracy"] == 1
