"""Ensure competition observations do not change retrieval metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.evaluation.evaluator import evaluate_query
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    CompetitionObservation,
    RetrievedItem,
)


def test_competition_observations_do_not_change_recall() -> None:
    query = BenchmarkQuery(
        id="q",
        timestamp=datetime(2026, 4, 15, tzinfo=UTC),
        capability=Capability.DIRECT_RECALL,
        query="test",
        expected_evidence_ids=("evt-001",),
    )
    items = (
        RetrievedItem(
            source_event_ids=("evt-001",),
            text="hit",
            score=1.0,
            rank=1,
        ),
    )
    baseline = evaluate_query(query, items, latency_ms=1.0)
    with_competition = evaluate_query(
        query,
        items,
        latency_ms=1.0,
        competition_observations=(
            CompetitionObservation(
                candidate_source_event_ids=("evt-001",),
                competitor_source_event_ids=("evt-002",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        ),
        competition_diagnostics_supported=True,
    )
    assert baseline.metrics["recall@5"] == with_competition.metrics["recall@5"]
    assert "competition_pair_f1" not in baseline.metrics
