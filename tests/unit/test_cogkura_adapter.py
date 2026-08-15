"""CogKura adapter unit tests."""

from cogkurabench.backends.cogkura import _indicates_missing_knowledge_from_flags


def test_missing_knowledge_flag_maps_to_true() -> None:
    assert _indicates_missing_knowledge_from_flags(("missing_knowledge",)) is True


def test_no_retrieved_memory_maps_to_true() -> None:
    assert _indicates_missing_knowledge_from_flags(("no_retrieved_memory",)) is True


def test_low_cue_coverage_maps_to_true() -> None:
    assert _indicates_missing_knowledge_from_flags(("low_cue_coverage",)) is True


def test_low_retrieval_strength_maps_to_true() -> None:
    assert _indicates_missing_knowledge_from_flags(("low_retrieval_strength",)) is True


def test_unrelated_flags_only_map_to_false() -> None:
    assert (
        _indicates_missing_knowledge_from_flags(("stale_evidence", "low_provenance_diversity"))
        is False
    )


def test_mixed_flags_include_missing_knowledge() -> None:
    assert _indicates_missing_knowledge_from_flags(("stale_evidence", "missing_knowledge")) is True
