"""Dataset validation tests for competition expectations."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.dataset import _validate_competitions, validate_dataset
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionExpectation,
    EventType,
    ProjectEvent,
)


def _event(event_id: str, *, timestamp: str = "2026-03-01T10:00:00+00:00") -> ProjectEvent:
    return ProjectEvent(
        id=event_id,
        timestamp=datetime.fromisoformat(timestamp),
        sequence=1,
        subject_id="project-engineering",
        event_type=EventType.IMPLEMENTATION,
        content=f"event {event_id}",
    )


def test_validate_competitions_rejects_unknown_event() -> None:
    query = BenchmarkQuery(
        id="q",
        timestamp=datetime(2026, 4, 15, tzinfo=UTC),
        capability=Capability.INTERFERENCE,
        query="test",
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("missing",),
                competitor_event_ids=("b",),
            ),
        ),
    )
    errors = _validate_competitions(query, {"b": _event("b")})
    assert any("unknown event missing" in error for error in errors)


def test_validate_competitions_rejects_future_expected_event() -> None:
    query = BenchmarkQuery(
        id="q",
        timestamp=datetime(2026, 2, 1, tzinfo=UTC),
        capability=Capability.INTERFERENCE,
        query="test",
        expected_competitions=(
            CompetitionExpectation(
                id="exp",
                candidate_event_ids=("future",),
                competitor_event_ids=("old",),
            ),
        ),
    )
    events = {
        "future": _event("future", timestamp="2026-03-01T10:00:00+00:00"),
        "old": _event("old", timestamp="2026-01-01T10:00:00+00:00"),
    }
    errors = _validate_competitions(query, events)
    assert any("future event future" in error for error in errors)


def test_interference_dataset_validates() -> None:
    assert validate_dataset("interference_v1") == []
