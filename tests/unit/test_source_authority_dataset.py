"""Dataset rules for source_authority_v1."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime

import pytest

from cogkurabench.dataset import _parse_semantic_fact, load_dataset, validate_dataset
from cogkurabench.exceptions import ValidationError
from cogkurabench.models import Capability, EventType, ProjectEvent, SourceAuthority


def test_source_authority_dataset_validates() -> None:
    assert validate_dataset("source_authority_v1") == []
    dataset = load_dataset("source_authority_v1")
    assert dataset.manifest.required_capabilities == (Capability.SOURCE_AUTHORITY,)
    assert dataset.manifest.events == len(dataset.events)
    assert dataset.manifest.queries == len(dataset.queries)
    assert dataset.feedback == ()
    assert all(query.capability is Capability.SOURCE_AUTHORITY for query in dataset.queries)
    assert all(query.expected_source_authority for query in dataset.queries)


def test_authority_is_not_inferred_and_invalid_bases_are_allowed() -> None:
    ordinary = next(
        event for event in load_dataset("source_authority_v1").events if event.id == "sa-a5"
    )
    assert ordinary.semantic_facts[0].confidence == 1.0
    assert ordinary.semantic_facts[0].authority is None
    confirmed = next(
        event for event in load_dataset("source_authority_v1").events if event.id == "sa-a6"
    )
    assert confirmed.status == "confirmed"
    assert confirmed.semantic_facts[0].authority is None
    referenced = next(
        event for event in load_dataset("source_authority_v1").events if event.id == "sa-a7"
    )
    assert referenced.source_ref == "docs/support-tier.md"
    assert referenced.semantic_facts[0].authority is None
    invalid = next(
        event for event in load_dataset("source_authority_v1").events if event.id == "sa-a8"
    )
    assert invalid.semantic_facts[0].authority == SourceAuthority(basis="confirmed")


def test_legacy_events_default_source_identity() -> None:
    event = ProjectEvent(
        id="evt",
        timestamp=datetime.fromisoformat("2026-05-01T10:00:00+00:00"),
        sequence=1,
        subject_id="s",
        event_type=EventType.DOCUMENTATION,
        content="fact",
    )
    assert event.source_record_id == "evt"
    assert event.tenant_id == "benchmark"


def test_malformed_authority_is_rejected() -> None:
    with pytest.raises(ValidationError, match="non-empty string"):
        SourceAuthority(basis=" ")
    from cogkurabench.dataset import _parse_source_authority_declaration

    with pytest.raises(ValidationError, match="authority must be an object"):
        _parse_source_authority_declaration("application_asserted")
    with pytest.raises(ValidationError, match="only basis"):
        _parse_source_authority_declaration({"basis": "application_asserted", "extra": "no"})


def test_revision_pair_and_reprocess_checkpoints() -> None:
    dataset = load_dataset("source_authority_v1")
    events = {event.id: event for event in dataset.events}
    assert events["sa-a9-v1"].source_record_id == events["sa-a9-v2"].source_record_id
    assert events["sa-a9-v1"].source_version == "1"
    assert events["sa-a9-v2"].source_version == "2"
    assert events["sa-a9-v1"].id != events["sa-a9-v2"].id
    stale = next(query for query in dataset.queries if query.id == "sa-q-a9")
    assert stale.skip_episode_encoding is True
    repeated = next(query for query in dataset.queries if query.id == "sa-q-a13")
    assert repeated.repeat_consolidation is True
    later = next(query for query in dataset.queries if query.id == "sa-q-a14")
    assert later.expected_source_authority[0].control_admission == "recurrence"
    assert events["sa-a9-v1"].timestamp < events["sa-a9-v2"].timestamp


def test_frozen_datasets_are_unchanged() -> None:
    paths = [
        "datasets/mini",
        "datasets/software_project_v1",
        "datasets/helios_v1",
        "datasets/customer_decision_context_v1",
        "datasets/interference_v1",
        "datasets/transient_interference_v1",
        "datasets/transient_interference_v2",
        "datasets/persistent_inhibition_v1",
        "datasets/persistent_inhibition_software_v1",
        "datasets/persistent_inhibition_customer_v1",
    ]
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", *paths],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_parser_round_trip_rejects_missing_basis() -> None:
    payload = {
        "subject": "payments-api",
        "predicate": "cache_backend",
        "object": "redis",
        "authority": {},
    }

    with pytest.raises(ValidationError, match="string basis"):
        _parse_semantic_fact(payload)
    encoded = json.dumps(payload)
    assert "authority" in encoded
