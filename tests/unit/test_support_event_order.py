"""Support event sets have a stable, backend-independent presentation."""

from types import SimpleNamespace

from cogkurabench.backends.cogkura import _supporting_event_ids


def test_supporting_events_ignore_storage_order_and_deduplicate() -> None:
    mapping = {("id-a", 1): "event-z", ("id-b", 1): "event-a", ("id-a", 2): "event-z"}
    evidence = [
        SimpleNamespace(observation_id="id-a", observation_revision=1),
        SimpleNamespace(observation_id="unknown", observation_revision=1),
        SimpleNamespace(observation_id="id-b", observation_revision=1),
        SimpleNamespace(observation_id="id-a", observation_revision=2),
    ]
    assert _supporting_event_ids(evidence, mapping) == ("event-a", "event-z")
    assert _supporting_event_ids(list(reversed(evidence)), mapping) == ("event-a", "event-z")
    assert _supporting_event_ids(evidence, {}) == ()
