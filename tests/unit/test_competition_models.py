"""Unit tests for competition benchmark models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cogkurabench.exceptions import ValidationError
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


def test_competition_direction_values() -> None:
    assert CompetitionDirection.PROACTIVE.value == "proactive"
    assert CompetitionDirection.RETROACTIVE.value == "retroactive"
    assert CompetitionDirection.CO_TEMPORAL.value == "co_temporal"


def test_competition_expectation_rejects_identical_groups() -> None:
    with pytest.raises(ValidationError):
        CompetitionExpectation(
            id="dup",
            candidate_event_ids=("a",),
            competitor_event_ids=("a",),
        )


def test_competition_observation_metadata_is_immutable() -> None:
    observation = CompetitionObservation(
        candidate_source_event_ids=("a",),
        competitor_source_event_ids=("b",),
        direction=CompetitionDirection.PROACTIVE,
        metadata={"strength_source": "core"},
    )
    with pytest.raises(TypeError):
        observation.metadata["strength_source"] = "changed"


def test_query_defaults_empty_competition_fields() -> None:
    query = _query()
    assert query.expected_competitions == ()
    assert query.forbidden_competitions == ()


def test_query_rejects_duplicate_competition_ids() -> None:
    expectation = CompetitionExpectation(
        id="same",
        candidate_event_ids=("a",),
        competitor_event_ids=("b",),
    )
    with pytest.raises(ValidationError):
        _query(
            expected_competitions=(expectation,),
            forbidden_competitions=(expectation,),
        )
