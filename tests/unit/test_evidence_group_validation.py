"""Evidence-group dataset validation tests."""

from datetime import UTC, datetime

from cogkurabench.dataset import validate_dataset
from cogkurabench.exceptions import ValidationError
from cogkurabench.models import EvidenceGroup


def test_evidence_group_rejects_empty_event_ids() -> None:
    try:
        EvidenceGroup(id="g", label="Group", event_ids=())
    except ValidationError as exc:
        assert "at least one event" in str(exc)
    else:
        raise AssertionError("expected ValidationError")


def test_evidence_group_rejects_duplicate_event_ids() -> None:
    try:
        EvidenceGroup(id="g", label="Group", event_ids=("evt-1", "evt-1"))
    except ValidationError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("expected ValidationError")


def test_query_rejects_overlapping_group_ids() -> None:
    from cogkurabench.models import BenchmarkQuery, Capability

    try:
        BenchmarkQuery(
            id="q",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            capability=Capability.WORKING_MEMORY,
            query="test",
            expected_evidence_groups=(
                EvidenceGroup(id="overlap", label="A", event_ids=("evt-1",)),
            ),
            forbidden_evidence_groups=(
                EvidenceGroup(id="overlap", label="B", event_ids=("evt-2",)),
            ),
        )
    except ValidationError as exc:
        assert "both expected and forbidden" in str(exc)
    else:
        raise AssertionError("expected ValidationError")


def test_mini_dataset_still_validates() -> None:
    assert validate_dataset("mini") == []
