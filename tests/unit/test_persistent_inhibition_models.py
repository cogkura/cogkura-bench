"""Unit tests for persistent inhibition benchmark models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cogkurabench.exceptions import ValidationError
from cogkurabench.models import (
    BenchmarkQuery,
    BenchmarkUse,
    Capability,
    CompetitionDirection,
    DatasetManifest,
    InhibitionTraceObservation,
    PersistentInhibitionComparison,
    PersistentInhibitionExpectation,
    PersistentInhibitionObservation,
)


def test_benchmark_use_defaults_request_id() -> None:
    use = BenchmarkUse(
        id="use-1",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        query_id="q-1",
        selected_event_ids=("gha",),
    )
    assert use.request_id == "use-1"


def test_benchmark_use_rejects_empty_selection() -> None:
    with pytest.raises(ValidationError):
        BenchmarkUse(
            id="use-1",
            timestamp=datetime(2026, 4, 1, tzinfo=UTC),
            query_id="q-1",
            selected_event_ids=(),
        )


def test_benchmark_use_rejects_overlapping_inhibition_ids() -> None:
    with pytest.raises(ValidationError):
        BenchmarkUse(
            id="use-1",
            timestamp=datetime(2026, 4, 1, tzinfo=UTC),
            query_id="q-1",
            selected_event_ids=("gha",),
            expected_inhibited_event_ids=("jenkins",),
            forbidden_inhibited_event_ids=("jenkins",),
        )


def test_manifest_uses_defaults_to_zero() -> None:
    manifest = DatasetManifest(
        name="mini",
        schema_version=1,
        events=1,
        queries=1,
        feedback=0,
        description="",
    )
    assert manifest.uses == 0


def test_query_persistent_inhibition_fields_default_empty() -> None:
    query = BenchmarkQuery(
        id="q",
        timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        capability=Capability.DIRECT_RECALL,
        query="test",
    )
    assert query.expected_persistent_inhibition == ()
    assert query.persistent_inhibition_comparisons == ()


def test_comparison_requires_a_check() -> None:
    with pytest.raises(ValidationError):
        PersistentInhibitionComparison(candidate_event_ids=("jenkins",))


def test_trace_observation_requires_both_sides() -> None:
    with pytest.raises(ValidationError):
        InhibitionTraceObservation(
            use_id="use-1",
            selected_source_event_ids=("gha",),
            inhibited_source_event_ids=(),
            direction=CompetitionDirection.PROACTIVE,
            induction_pressure=0.5,
        )


def test_expectation_rejects_overlapping_candidate_and_selected() -> None:
    with pytest.raises(ValidationError):
        PersistentInhibitionExpectation(
            id="effect",
            candidate_event_ids=("jenkins",),
            selected_event_ids=("jenkins",),
        )


def test_observation_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        PersistentInhibitionObservation(
            candidate_source_event_ids=("jenkins",),
            activation_before=0.0,
            activation_after=-0.1,
            stored_trace_count=-1,
            evaluated_trace_count=0,
            matched_trace_count=0,
            effective_trace_count=0,
            inhibition_pressure=0.0,
            penalty=-0.1,
            crossed_activation_threshold=False,
        )
