"""CogKura recall metadata extraction tests."""

import importlib.util

import pytest

from cogkurabench.backends.cogkura import _recall_result_to_metadata

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cogkura") is None,
    reason="cogkura not installed",
)


def test_recall_result_to_metadata_includes_public_fields() -> None:
    from cogkura.models import ActivationComponents, MemoryKind, RecallResult

    class _SemanticMemory:
        statement = "PostgreSQL backs the ledger"
        status = "ACTIVE"
        predicate = "backing-store"
        subject_entity_id = "charge-ledger"
        object_value = "PostgreSQL"
        slot_key = "slot-1"

    result = RecallResult(
        memory_kind=MemoryKind.SEMANTIC,
        memory=_SemanticMemory(),
        activation=1.25,
        score=0.75,
        latency_seconds=0.01,
        components=ActivationComponents(
            base_level=0.5,
            spreading=0.2,
            partial_match=0.1,
            noise=0.0,
            total=0.8,
            current_state=0.1,
        ),
        reason="activation=1.25; temporal_mode=current",
    )
    metadata = _recall_result_to_metadata(result)
    assert metadata["activation"] == 1.25
    assert metadata["reason"] == "activation=1.25; temporal_mode=current"
    assert metadata["activation_total"] == 0.8
    assert metadata["semantic_predicate"] == "backing-store"
    assert metadata["semantic_status"] == "ACTIVE"


def test_recall_result_to_metadata_omits_optional_fields_when_absent() -> None:
    from cogkura.models import ActivationComponents, MemoryKind, RecallResult

    class _EpisodeMemory:
        statement = "Episode text"

    result = RecallResult(
        memory_kind=MemoryKind.EPISODE,
        memory=_EpisodeMemory(),
        activation=0.5,
        score=0.4,
        latency_seconds=0.02,
        components=ActivationComponents(
            base_level=0.1,
            spreading=0.1,
            partial_match=0.1,
            noise=0.0,
            total=0.3,
            current_state=0.0,
        ),
        reason="activation=0.5",
    )
    metadata = _recall_result_to_metadata(result)
    assert "rank_activation" not in metadata
    assert "semantic_predicate" not in metadata
    assert metadata["reason"] == "activation=0.5"
