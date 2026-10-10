"""Selection matching for cached CogKura recall results."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cogkurabench.backends.cogkura import CogKuraBackend, _CachedRetrieval
from cogkurabench.exceptions import ValidationError
from cogkurabench.models import UseRequest


class _Kind:
    def __init__(self, value: str) -> None:
        self.value = value


class _Memory:
    def __init__(self, key: str) -> None:
        self.memory_key = key


class _Result:
    def __init__(self, kind: str, key: str) -> None:
        self.memory_kind = _Kind(kind)
        self.memory = _Memory(key)


def _request(*selected: str) -> UseRequest:
    return UseRequest(
        use_id="use-1",
        source_query_id="q",
        selected_event_ids=selected,
        as_of=datetime(2026, 4, 1, tzinfo=UTC),
        request_id="use-1",
    )


def test_selected_event_maps_to_one_cached_result() -> None:
    backend = CogKuraBackend()
    episode = _Result("episode", "ep")
    semantic = _Result("semantic", "sem")
    cached = _CachedRetrieval(
        results=(episode, semantic),
        event_ids=(("gha", "support"), ("jenkins",)),
        memories_by_identity={},
    )
    selected = backend._resolve_selected_results(cached, _request("gha"))
    assert selected == [episode]


def test_multi_provenance_semantic_matches_once() -> None:
    backend = CogKuraBackend()
    semantic = _Result("semantic", "sem")
    cached = _CachedRetrieval(
        results=(semantic,),
        event_ids=(("gha", "support"),),
        memories_by_identity={},
    )
    selected = backend._resolve_selected_results(cached, _request("support"))
    assert selected == [semantic]


def test_ambiguous_selection_fails() -> None:
    backend = CogKuraBackend()
    cached = _CachedRetrieval(
        results=(_Result("episode", "ep"), _Result("semantic", "sem")),
        event_ids=(("gha",), ("gha",)),
        memories_by_identity={},
    )
    with pytest.raises(ValidationError, match="multiple memories"):
        backend._resolve_selected_results(cached, _request("gha"))
