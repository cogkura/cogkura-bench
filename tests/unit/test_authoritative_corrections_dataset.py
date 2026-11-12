"""Dataset rules for authoritative_corrections_v1."""

from __future__ import annotations

import subprocess

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import Capability


def test_corrections_dataset_validates() -> None:
    assert validate_dataset("authoritative_corrections_v1") == []
    dataset = load_dataset("authoritative_corrections_v1")
    assert dataset.manifest.required_capabilities == (Capability.AUTHORITATIVE_CORRECTION,)
    assert dataset.manifest.events == len(dataset.events)
    assert dataset.manifest.queries == len(dataset.queries)
    assert all(query.capability is Capability.AUTHORITATIVE_CORRECTION for query in dataset.queries)
    assert all(query.expected_authoritative_corrections for query in dataset.queries)


def test_corrections_name_claims_not_core_revision_keys() -> None:
    events = {event.id: event for event in load_dataset("authoritative_corrections_v1").events}
    correction = events["ac-time-correct"].semantic_facts[0].correction
    assert correction is not None
    assert correction.replaces_object == "application_startup"
    assert correction.unknown_revision_key is None
    unknown = events["ac-c09-edit"].semantic_facts[0].correction
    assert unknown is not None
    assert unknown.unknown_revision_key == "missing-revision"
    withdrawal = events["ac-time-withdraw"].semantic_withdrawals[0]
    assert withdrawal.target_object == "deployment_pipeline"
    assert withdrawal.authority_basis == "application_asserted"


def test_temporal_spine_uses_distinct_clocks() -> None:
    queries = {query.id: query for query in load_dataset("authoritative_corrections_v1").queries}
    assert queries["ac-q-c02"].valid_at is None
    assert queries["ac-q-hist-early"].valid_at is not None
    assert queries["ac-q-hist-early"].timestamp > queries["ac-q-c06"].timestamp
    assert queries["ac-q-c11"].skip_episode_encoding is True
    assert queries["ac-q-c18"].extra_consolidations == 2


def test_frozen_datasets_remain_unchanged() -> None:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            "datasets/source_authority_v1",
            "datasets/mini",
            "datasets/interference_v1",
            "datasets/persistent_inhibition_v1",
            "datasets/transient_interference_v2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
