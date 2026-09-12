"""Unit tests for CogKura recall mapping diagnostics."""

from dataclasses import dataclass

from cogkurabench.backends.cogkura_diagnostics import (
    competition_inspection_to_observations,
    competition_mapping_counts,
    map_ranked_recall_results,
    retrieval_context_diagnostics_to_metadata,
)
from cogkurabench.models import CompetitionDirection


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


def test_retrieval_context_diagnostics_absent_when_missing() -> None:
    inspection = type("Inspection", (), {})()
    assert retrieval_context_diagnostics_to_metadata(inspection) is None


class _CompetitionEvidence:
    def __init__(
        self,
        *,
        competitor_memory: object,
        direction: str = "proactive",
        strength: float = 0.87,
    ) -> None:
        self.competitor_identity = type(
            "Identity",
            (),
            {
                "memory_kind": type("Kind", (), {"value": "episode"})(),
                "memory_key": competitor_memory.memory_key,
            },
        )()
        self.direction = type("Direction", (), {"value": direction})()
        self.strength = strength
        self.same_subject = True
        self.same_semantic_slot = True
        self.same_predicate = True
        self.shared_entity_ids = ("payments-api",)
        self.shared_features = ("deployment",)
        self.relationship_strength = 0.8
        self.joint_cue_fit = 0.7
        self.candidate_cue_fit = 0.9
        self.competitor_cue_fit = 0.8


class _KeyedEpisodeMemory(_EpisodeMemory):
    def __init__(
        self,
        *,
        memory_key: str,
        observation_ids: tuple[str, ...],
        statement: str = "text",
    ) -> None:
        super().__init__(observation_ids=observation_ids, statement=statement)
        self.memory_key = memory_key


class _InspectionCandidate:
    def __init__(self, *, memory: object, competitors: tuple[object, ...]) -> None:
        self.memory_kind = type("Kind", (), {"value": "episode"})()
        self.memory = memory
        self.competition = type(
            "CompetitionDiagnostics",
            (),
            {
                "competitor_count": len(competitors),
                "competitors": competitors,
            },
        )()


def test_competition_inspection_maps_event_ids() -> None:
    candidate = _KeyedEpisodeMemory(memory_key="cand", observation_ids=("obs-new",))
    competitor = _KeyedEpisodeMemory(memory_key="comp", observation_ids=("obs-old",))
    inspection = type(
        "Inspection",
        (),
        {
            "returned": (
                _InspectionCandidate(
                    memory=candidate,
                    competitors=(_CompetitionEvidence(competitor_memory=competitor),),
                ),
            ),
            "rejected": (_InspectionCandidate(memory=competitor, competitors=()),),
        },
    )()
    observations = competition_inspection_to_observations(
        inspection,
        observation_id_to_event_id={"obs-new": "deploy-gha-001", "obs-old": "deploy-jenkins-001"},
    )
    assert len(observations) == 1
    assert observations[0].candidate_source_event_ids == ("deploy-gha-001",)
    assert observations[0].competitor_source_event_ids == ("deploy-jenkins-001",)
    assert observations[0].direction is CompetitionDirection.PROACTIVE
    assert observations[0].strength == 0.87


def test_competition_mapping_counts_track_unmapped_pairs() -> None:
    candidate = _KeyedEpisodeMemory(memory_key="cand", observation_ids=("obs-new",))
    competitor = _KeyedEpisodeMemory(memory_key="comp", observation_ids=("obs-missing",))
    inspection = type(
        "Inspection",
        (),
        {
            "returned": (
                _InspectionCandidate(
                    memory=candidate,
                    competitors=(_CompetitionEvidence(competitor_memory=competitor),),
                ),
            ),
            "rejected": (_InspectionCandidate(memory=competitor, competitors=()),),
        },
    )()
    counts = competition_mapping_counts(
        inspection,
        observation_id_to_event_id={"obs-new": "deploy-gha-001"},
    )
    assert counts["competition_pairs_reported"] == 1
    assert counts["competition_pairs_mapped"] == 0
    assert counts["competition_pairs_unmapped"] == 1


def test_retrieval_context_diagnostics_serializes_dataclass_fields() -> None:
    @dataclass
    class _Context:
        state: str
        comparable_candidate_count: int

    inspection = type("Inspection", (), {"context": _Context("context_not_provided", 0)})()
    payload = retrieval_context_diagnostics_to_metadata(inspection)
    assert payload == {"state": "context_not_provided", "comparable_candidate_count": 0}
