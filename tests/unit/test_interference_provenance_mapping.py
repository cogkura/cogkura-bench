"""Provenance mapping for semantic memories and supporting episodes."""

from cogkurabench.backends.cogkura_diagnostics import event_ids_for_memory


class _Evidence:
    def __init__(self, observation_id: str) -> None:
        self.observation_id = observation_id


class _Memory:
    def __init__(self, evidence: tuple[_Evidence, ...], observation_evidence=()) -> None:
        self.evidence = evidence
        self.observation_evidence = observation_evidence


def test_episode_and_semantic_evidence_map_to_event_ids() -> None:
    observation_map = {"obs-jenkins": "v2-jenkins", "obs-support": "v2-lineage-support"}
    episode = _Memory((_Evidence("obs-jenkins"),))
    semantic = _Memory((), (_Evidence("obs-support"), _Evidence("obs-jenkins")))
    assert event_ids_for_memory(episode, observation_id_to_event_id=observation_map) == (
        "v2-jenkins",
    )
    assert event_ids_for_memory(semantic, observation_id_to_event_id=observation_map) == (
        "v2-jenkins",
        "v2-lineage-support",
    )
