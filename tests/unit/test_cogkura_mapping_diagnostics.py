"""Unit tests for CogKura recall mapping diagnostics."""

from cogkurabench.backends.cogkura_diagnostics import map_ranked_recall_results


class _Evidence:
    def __init__(self, observation_id: str) -> None:
        self.observation_id = observation_id


class _EpisodeMemory:
    def __init__(self, *, observation_ids: tuple[str, ...], statement: str = "text") -> None:
        self.evidence = [_Evidence(observation_id) for observation_id in observation_ids]
        self.statement = statement


class _RecallResult:
    def __init__(self, *, memory_kind: str, memory: object, score: float = 1.0) -> None:
        self.memory_kind = type("Kind", (), {"value": memory_kind})()
        self.memory = memory
        self.score = score
        self.activation = 1.0
        self.latency_seconds = 0.01
        self.reason = "test"
        self.components = type(
            "Components",
            (),
            {
                "base_level": 0.1,
                "spreading": 0.1,
                "partial_match": 0.1,
                "noise": 0.0,
                "total": 0.3,
                "current_state": 0.0,
            },
        )()
        self.diagnostics = None


def test_map_ranked_recall_results_preserves_raw_rank_gaps() -> None:
    observation_map = {"obs-1": "event-1", "obs-2": "event-2"}
    results = [
        (
            1,
            _RecallResult(
                memory_kind="episode",
                memory=_EpisodeMemory(observation_ids=("obs-missing",)),
            ),
        ),
        (
            2,
            _RecallResult(
                memory_kind="semantic",
                memory=_EpisodeMemory(observation_ids=("obs-1",)),
            ),
        ),
    ]
    mapping = map_ranked_recall_results(
        results,
        observation_id_to_event_id=observation_map,
        statement_for_result=lambda result: str(result.memory.statement),
    )
    assert mapping.raw_count == 2
    assert mapping.mapped_count == 1
    assert mapping.unmapped_count == 1
    assert mapping.items[0].rank == 2
    assert mapping.provenance.wholly_unresolved_count == 1


def test_map_ranked_recall_results_all_unmapped_still_reports_raw() -> None:
    results = [
        (
            1,
            _RecallResult(
                memory_kind="episode",
                memory=_EpisodeMemory(observation_ids=("obs-unknown",)),
            ),
        ),
        (
            2,
            _RecallResult(
                memory_kind="semantic",
                memory=_EpisodeMemory(observation_ids=("obs-other",)),
            ),
        ),
        (
            3,
            _RecallResult(memory_kind="episode", memory=_EpisodeMemory(observation_ids=())),
        ),
    ]
    mapping = map_ranked_recall_results(
        results,
        observation_id_to_event_id={"obs-1": "event-1"},
        statement_for_result=lambda result: str(result.memory.statement),
    )
    assert mapping.raw_count == 3
    assert mapping.mapped_count == 0
    assert mapping.unmapped_count == 3
    assert mapping.provenance.no_provenance_count == 1
    assert mapping.provenance.wholly_unresolved_count == 2


def test_map_ranked_recall_results_empty_raw() -> None:
    mapping = map_ranked_recall_results(
        [],
        observation_id_to_event_id={},
        statement_for_result=lambda result: "",
    )
    assert mapping.raw_count == 0
    assert mapping.mapped_count == 0
    assert mapping.unmapped_count == 0
