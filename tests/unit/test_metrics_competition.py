"""Unit tests for competition diagnostic metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.metrics.competition import compute_competition_metrics
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    CompetitionExpectation,
    CompetitionObservation,
)


def _query(**kwargs: object) -> BenchmarkQuery:
    defaults = {
        "id": "q",
        "timestamp": datetime(2026, 4, 15, tzinfo=UTC),
        "capability": Capability.INTERFERENCE,
        "query": "test",
    }
    defaults.update(kwargs)
    return BenchmarkQuery(**defaults)


def _observation(
    candidate: tuple[str, ...],
    competitor: tuple[str, ...],
    direction: CompetitionDirection,
) -> CompetitionObservation:
    return CompetitionObservation(
        candidate_source_event_ids=candidate,
        competitor_source_event_ids=competitor,
        direction=direction,
    )


def test_perfect_detection() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, diagnostics = compute_competition_metrics(
        query,
        [_observation(("new",), ("old",), CompetitionDirection.PROACTIVE)],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_pair_precision"] == 1.0
    assert metrics["competition_pair_recall"] == 1.0
    assert metrics["competition_pair_f1"] == 1.0
    assert metrics["competition_direction_accuracy"] == 1.0
    assert diagnostics[0].classification == "expected"


def test_missed_expected_pair() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("new",),
                competitor_event_ids=("old",),
            ),
        )
    )
    metrics, _ = compute_competition_metrics(
        query,
        [],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_pair_recall"] == 0.0


def test_unexpected_pair_reduces_precision() -> None:
    query = _query()
    metrics, diagnostics = compute_competition_metrics(
        query,
        [_observation(("x",), ("y",), CompetitionDirection.CO_TEMPORAL)],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_pair_precision"] == 0.0
    assert diagnostics[0].classification == "unexpected"


def test_forbidden_pair_increases_rate() -> None:
    query = _query(
        forbidden_competitions=(
            CompetitionExpectation(
                id="forbidden",
                candidate_event_ids=("db",),
                competitor_event_ids=("backup",),
            ),
        )
    )
    metrics, diagnostics = compute_competition_metrics(
        query,
        [_observation(("db",), ("backup",), CompetitionDirection.CO_TEMPORAL)],
        competition_diagnostics_supported=True,
    )
    assert metrics["forbidden_competition_rate"] == 1.0
    assert diagnostics[0].classification == "forbidden"


def test_wrong_direction_counts_pair_but_not_direction_accuracy() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("a",),
                competitor_event_ids=("b",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        )
    )
    metrics, _ = compute_competition_metrics(
        query,
        [_observation(("a",), ("b",), CompetitionDirection.RETROACTIVE)],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_pair_recall"] == 1.0
    assert metrics["competition_direction_accuracy"] == 0.0


def test_grouped_provenance_intersection_matching() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("gha-001", "gha-002"),
                competitor_event_ids=("jenkins-001",),
            ),
        )
    )
    metrics, _ = compute_competition_metrics(
        query,
        [_observation(("gha-002", "gha-003"), ("jenkins-001",), CompetitionDirection.PROACTIVE)],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_pair_recall"] == 1.0


def test_duplicate_observations_are_deduplicated() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("a",),
                competitor_event_ids=("b",),
            ),
        )
    )
    duplicate = _observation(("a",), ("b",), CompetitionDirection.PROACTIVE)
    metrics, diagnostics = compute_competition_metrics(
        query,
        [duplicate, duplicate],
        competition_diagnostics_supported=True,
    )
    assert metrics["competition_observed_pairs"] == 1.0
    assert len(diagnostics) == 1


def test_unsupported_backend_returns_empty_metrics() -> None:
    query = _query(
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("a",),
                competitor_event_ids=("b",),
            ),
        )
    )
    metrics, diagnostics = compute_competition_metrics(
        query,
        [_observation(("a",), ("b",), CompetitionDirection.PROACTIVE)],
        competition_diagnostics_supported=False,
    )
    assert metrics == {}
    assert diagnostics == ()
