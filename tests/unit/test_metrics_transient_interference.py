"""Unit tests for transient interference behavioural metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.metrics.transient_interference import compute_transient_interference_metrics
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    InterferenceContributionObservation,
    TransientInterferenceExpectation,
    TransientInterferenceObservation,
)


def _query(**kwargs: object) -> BenchmarkQuery:
    defaults = {
        "id": "q",
        "timestamp": datetime(2026, 4, 15, tzinfo=UTC),
        "capability": Capability.TRANSIENT_INTERFERENCE,
        "query": "test",
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)


def _observation(
    candidate: tuple[str, ...],
    competitor: tuple[str, ...],
    direction: CompetitionDirection,
    *,
    pressure: float = 0.5,
    penalty: float = -0.1,
) -> TransientInterferenceObservation:
    return TransientInterferenceObservation(
        candidate_source_event_ids=candidate,
        activation_before=0.0,
        activation_after=penalty,
        proactive_pressure=pressure if direction is CompetitionDirection.PROACTIVE else 0.0,
        retroactive_pressure=pressure if direction is CompetitionDirection.RETROACTIVE else 0.0,
        proactive_penalty=penalty if direction is CompetitionDirection.PROACTIVE else 0.0,
        retroactive_penalty=penalty if direction is CompetitionDirection.RETROACTIVE else 0.0,
        total_penalty=penalty,
        crossed_activation_threshold=False,
        rank_before=1,
        rank_after=2,
        contributions=(
            InterferenceContributionObservation(
                competitor_source_event_ids=competitor,
                direction=direction,
                competition_strength=0.8,
                competitor_accessibility=0.7,
                pressure=pressure,
            ),
        ),
    )


def test_perfect_behavioural_detection() -> None:
    query = _query(
        expected_interference_effects=(
            TransientInterferenceExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, diagnostics, _ = compute_transient_interference_metrics(
        query,
        [_observation(("new",), ("old",), CompetitionDirection.PROACTIVE)],
        transient_interference_supported=True,
    )
    assert metrics["interference_effect_precision"] == 1.0
    assert metrics["interference_effect_recall"] == 1.0
    assert metrics["interference_effect_f1"] == 1.0
    assert diagnostics[0].classification == "expected"


def test_unsupported_backend_returns_empty() -> None:
    query = _query(
        expected_interference_effects=(
            TransientInterferenceExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, diagnostics, _ = compute_transient_interference_metrics(
        query,
        [_observation(("new",), ("old",), CompetitionDirection.PROACTIVE)],
        transient_interference_supported=False,
    )
    assert metrics == {}
    assert diagnostics == ()


def test_unexpected_effect_reduces_precision() -> None:
    query = _query(
        expected_interference_effects=(
            TransientInterferenceExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, _, _ = compute_transient_interference_metrics(
        query,
        [
            _observation(("new",), ("old",), CompetitionDirection.PROACTIVE),
            _observation(("other",), ("noise",), CompetitionDirection.RETROACTIVE),
        ],
        transient_interference_supported=True,
    )
    assert metrics["interference_effect_precision"] == 0.5
    assert metrics["unexpected_interference_rate"] == 0.5


def test_wrong_direction_keeps_pair_but_lowers_direction_accuracy() -> None:
    query = _query(
        expected_interference_effects=(
            TransientInterferenceExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, diagnostics, _ = compute_transient_interference_metrics(
        query,
        [_observation(("new",), ("old",), CompetitionDirection.RETROACTIVE)],
        transient_interference_supported=True,
    )
    assert metrics["interference_effect_recall"] == 1.0
    assert diagnostics[0].classification == "expected"
    assert metrics["interference_effect_direction_accuracy"] == 0.0
