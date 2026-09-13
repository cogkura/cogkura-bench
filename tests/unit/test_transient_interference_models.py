"""Unit tests for transient interference benchmark models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cogkurabench.exceptions import ValidationError
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
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


def test_transient_interference_expectation_rejects_identical_groups() -> None:
    with pytest.raises(ValidationError):
        TransientInterferenceExpectation(
            id="dup",
            candidate_event_ids=("a",),
            competitor_event_ids=("a",),
            direction=CompetitionDirection.PROACTIVE,
        )


def test_query_defaults_empty_interference_fields() -> None:
    query = _query()
    assert query.expected_interference_effects == ()
    assert query.forbidden_interference_effects == ()


def test_query_rejects_duplicate_interference_ids() -> None:
    expectation = TransientInterferenceExpectation(
        id="same",
        candidate_event_ids=("a",),
        competitor_event_ids=("b",),
        direction=CompetitionDirection.PROACTIVE,
    )
    with pytest.raises(ValidationError):
        _query(
            expected_interference_effects=(expectation,),
            forbidden_interference_effects=(expectation,),
        )


def test_transient_interference_observation_requires_candidate_ids() -> None:
    with pytest.raises(ValidationError):
        TransientInterferenceObservation(
            candidate_source_event_ids=(),
            activation_before=0.0,
            activation_after=-0.1,
            proactive_pressure=0.0,
            retroactive_pressure=0.0,
            proactive_penalty=0.0,
            retroactive_penalty=0.0,
            total_penalty=-0.1,
            crossed_activation_threshold=False,
            rank_before=1,
            rank_after=2,
        )
