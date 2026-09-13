"""Dataset validation tests for transient interference effects."""

from __future__ import annotations

from datetime import UTC, datetime

from cogkurabench.dataset import validate_dataset
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    TransientInterferenceExpectation,
)


def test_transient_interference_dataset_validates() -> None:
    assert validate_dataset("transient_interference_v1") == []


def test_interference_v1_unchanged_without_behavioural_fields() -> None:
    assert validate_dataset("interference_v1") == []


def test_interference_effects_require_transient_capability() -> None:
    query = BenchmarkQuery(
        id="bad",
        timestamp=datetime(2026, 4, 15, tzinfo=UTC),
        capability=Capability.DIRECT_RECALL,
        query="test",
        expected_interference_effects=(
            TransientInterferenceExpectation(
                id="eff",
                candidate_event_ids=("a",),
                competitor_event_ids=("b",),
                direction=CompetitionDirection.PROACTIVE,
            ),
        ),
    )
    errors = []
    from cogkurabench.dataset import _validate_interference_effects

    errors.extend(_validate_interference_effects(query, {}))
    assert any("capability" in error for error in errors)
