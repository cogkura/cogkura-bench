"""CogKura memory backend adapter."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from cogkurabench.backends.cogkura_diagnostics import (
    COGKURA_METADATA_SCHEMA_VERSION,
    RecallMappingResult,
    competition_inspection_to_metadata,
    competition_inspection_to_observations,
    competition_mapping_counts,
    dataclass_to_metadata,
    json_safe_metadata_value,
    map_ranked_recall_results,
    recall_mapping_metadata,
    recall_result_to_metadata,
    relationship_inspection_to_metadata,
    retrieval_context_diagnostics_to_metadata,
)
from cogkurabench.models import (
    AssessmentRequest,
    AssessmentResponse,
    BackendCapabilities,
    BenchmarkFeedback,
    ContextRequest,
    ContextResponse,
    EntityRelationship,
    FeedbackOutcome,
    ProjectEvent,
    RetrievalRequest,
    RetrievalResponse,
    SemanticFact,
)

if TYPE_CHECKING:
    from cogkura.memory import Memory
    from cogkura.models import RecallResult, StoredEpisode, StoredSemanticMemory


TENANT_ID = "benchmark"
SOURCE_NAMESPACE = "cogkurabench.events"

MISSING_KNOWLEDGE_FLAGS: frozenset[str] = frozenset(
    {
        "missing_knowledge",
        "no_retrieved_memory",
        "low_cue_coverage",
        "low_retrieval_strength",
    }
)


def _indicates_missing_knowledge_from_flags(flags: Sequence[str]) -> bool:
    return any(flag in flags for flag in MISSING_KNOWLEDGE_FLAGS)


def _require_cogkura() -> Any:
    try:
        import cogkura  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "CogKura backend requires the optional dependency. "
            "Install with: uv sync --extra cogkura --dev"
        ) from exc
    return cogkura


def _installed_cogkura_version(cogkura: Any) -> str:
    from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415

    try:
        return version("cogkura")
    except PackageNotFoundError:
        return str(cogkura.__version__)


def _has_structured_cue(
    entity_ids: tuple[str, ...],
    predicate: str | None,
    object_value: str | None,
) -> bool:
    return bool(entity_ids) or predicate is not None or object_value is not None


def _build_retrieval_cue(
    *,
    query: str,
    entity_ids: tuple[str, ...] = (),
    predicate: str | None = None,
    object_value: str | None = None,
) -> str | Any:
    if not _has_structured_cue(entity_ids, predicate, object_value):
        return query
    _require_cogkura()
    from cogkura.models import RetrievalCue  # noqa: PLC0415

    return RetrievalCue(
        text=query,
        entity_ids=entity_ids,
        predicate=predicate,
        object_value=object_value,
    )


def _semantic_facts_to_metadata(facts: tuple[SemanticFact, ...]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for fact in facts:
        entry: dict[str, object] = {
            "predicate": fact.predicate,
            "object_value": fact.object,
            "subject_entity_id": fact.subject,
            "cardinality": fact.cardinality,
            "polarity": fact.polarity,
            "qualifiers": dict(fact.qualifiers),
        }
        if fact.valid_from is not None:
            entry["valid_from"] = fact.valid_from.isoformat()
        if fact.valid_until is not None:
            entry["valid_until"] = fact.valid_until.isoformat()
        payload.append(entry)
    return payload


def _relationships_to_metadata(
    relationships: tuple[EntityRelationship, ...],
) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for relationship in relationships:
        entry: dict[str, object] = {
            "source_entity_id": relationship.source_entity_id,
            "relation_type": relationship.relation_type,
            "target_entity_id": relationship.target_entity_id,
        }
        if relationship.provenance is not None:
            entry["provenance"] = relationship.provenance
        payload.append(entry)
    return payload


class CogKuraBackend:
    """Benchmark adapter for CogKura 0.17.x public memory API."""

    def __init__(self, *, competition_enabled: bool = True) -> None:
        self._competition_enabled = competition_enabled
        self._memory: Memory | None = None
        self._observation_store: Any = None
        self._observation_id_to_event_id: dict[str, str] = {}
        self._version: str | None = None
        self._bench_version: str | None = None
        self._events_ingested = 0
        self._relationships_ingested = 0
        self._ingest_calls = 0
        self._prepare_calls = 0
        self._maintenance_calls = 0
        self._last_prepare_at: datetime | None = None
        self._last_maintenance_at: datetime | None = None
        self._last_episode_encoding: dict[str, object] = {}
        self._last_semantic_consolidation: dict[str, object] = {}
        self._last_forgetting: dict[str, object] = {}
        self._cumulative_forgetting: dict[str, int] = {
            "evaluated": 0,
            "active": 0,
            "fading": 0,
            "forgotten": 0,
            "reactivated": 0,
            "references_compacted": 0,
        }

    @property
    def name(self) -> str:
        return "cogkura"

    @property
    def version(self) -> str | None:
        return self._version

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            retrieve=True,
            select_context=True,
            assess=True,
            learn=True,
            forget=True,
            maintain=True,
            competition_diagnostics=self._competition_enabled,
        )

    async def reset(self) -> None:
        import cogkurabench

        cogkura = _require_cogkura()
        from cogkura.algorithms.semantic import (
            ComplementaryLearningSemanticConsolidator,  # noqa: PLC0415
        )
        from cogkura.models import CompetitionConfig  # noqa: PLC0415
        from cogkura.storage.in_memory_observation import InMemoryObservationStore  # noqa: PLC0415

        self._version = _installed_cogkura_version(cogkura)
        self._bench_version = cogkurabench.__version__
        if self._memory is not None:
            await self._memory.clear(tenant_id=TENANT_ID)
        self._observation_store = InMemoryObservationStore()
        self._memory = cogkura.Memory(
            observation_store=self._observation_store,
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                minimum_supporting_episodes=1,
            ),
            competition_config=CompetitionConfig(enabled=self._competition_enabled),
        )
        self._observation_id_to_event_id.clear()
        self._events_ingested = 0
        self._relationships_ingested = 0
        self._ingest_calls = 0
        self._prepare_calls = 0
        self._maintenance_calls = 0
        self._last_prepare_at = None
        self._last_maintenance_at = None
        self._last_episode_encoding = {}
        self._last_semantic_consolidation = {}
        self._last_forgetting = {}
        self._cumulative_forgetting = {
            "evaluated": 0,
            "active": 0,
            "fading": 0,
            "forgotten": 0,
            "reactivated": 0,
            "references_compacted": 0,
        }

    async def ingest(self, events: Sequence[ProjectEvent]) -> None:
        _require_cogkura()
        from cogkura.observations.models import ObservationInput  # noqa: PLC0415

        memory = self._require_memory()
        for event in events:
            metadata: dict[str, object] = {}
            if event.semantic_facts:
                metadata["semantic_facts"] = _semantic_facts_to_metadata(event.semantic_facts)
            if event.tags:
                metadata["tags"] = list(event.tags)
            if event.entities:
                metadata["entity_ids"] = list(event.entities)
            if event.session_id is not None:
                metadata["session_id"] = event.session_id
            if event.relationships:
                metadata["relationships"] = _relationships_to_metadata(event.relationships)
                self._relationships_ingested += len(event.relationships)
            await memory.observe(
                ObservationInput(
                    tenant_id=TENANT_ID,
                    subject_id=event.subject_id,
                    source_namespace=SOURCE_NAMESPACE,
                    source_record_id=event.id,
                    event_type=event.event_type.value,
                    content=event.content,
                    observed_at=event.timestamp,
                    metadata=metadata,
                )
            )
        self._events_ingested += len(events)
        self._ingest_calls += 1
        await self._refresh_observation_map()

    async def prepare(self, *, as_of: datetime) -> None:
        memory = self._require_memory()
        episode_result = await memory.encode_episodes(tenant_id=TENANT_ID, as_of=as_of)
        semantic_result = await memory.consolidate_semantics(tenant_id=TENANT_ID, as_of=as_of)
        self._prepare_calls += 1
        self._last_prepare_at = as_of
        self._last_episode_encoding = dataclass_to_metadata(episode_result)
        self._last_semantic_consolidation = dataclass_to_metadata(semantic_result)
        await self._refresh_observation_map()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        start = time.perf_counter()
        memory = self._require_memory()
        cue = _build_retrieval_cue(
            query=request.query,
            entity_ids=request.entity_ids,
            predicate=request.predicate,
            object_value=request.object_value,
        )
        results = await memory.recall(
            cue,
            tenant_id=TENANT_ID,
            limit=request.limit,
            as_of=request.as_of,
            valid_at=request.valid_at,
        )
        inspection = await memory.inspect_recall(
            cue,
            tenant_id=TENANT_ID,
            limit=request.limit,
            as_of=request.as_of,
            valid_at=request.valid_at,
        )
        mapping = self._map_recall_results(results)
        latency_ms = (time.perf_counter() - start) * 1000.0
        competition_observations = competition_inspection_to_observations(
            inspection,
            observation_id_to_event_id=self._observation_id_to_event_id,
        )
        competition_counts = competition_mapping_counts(
            inspection,
            observation_id_to_event_id=self._observation_id_to_event_id,
        )
        backend_metadata = self._build_response_metadata(
            recall_mapping=mapping,
            snapshot_at=request.as_of,
            relationship_inspection=relationship_inspection_to_metadata(inspection),
            retrieval_context=retrieval_context_diagnostics_to_metadata(inspection),
            competition_inspection=competition_inspection_to_metadata(inspection),
            competition_counts=competition_counts,
        )
        return RetrievalResponse(
            items=mapping.items,
            latency_ms=latency_ms,
            competition_observations=competition_observations,
            backend_metadata=backend_metadata,
        )

    async def select_context(self, request: ContextRequest) -> ContextResponse | None:
        if request.prompt_budget_tokens is None:
            return None
        start = time.perf_counter()
        memory = self._require_memory()
        cue = _build_retrieval_cue(
            query=request.query,
            entity_ids=request.entity_ids,
            predicate=request.predicate,
            object_value=request.object_value,
        )
        snapshot = await memory.select_working_memory(
            cue,
            tenant_id=TENANT_ID,
            goal=request.goal,
            prompt_budget_tokens=request.prompt_budget_tokens,
            as_of=request.as_of,
            valid_at=request.valid_at,
        )
        ranked_items = [(item.rank, item.recall) for item in snapshot.items]
        mapping = map_ranked_recall_results(
            ranked_items,
            observation_id_to_event_id=self._observation_id_to_event_id,
            statement_for_result=self._statement_for_result,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        backend_metadata = self._build_response_metadata(
            context_mapping=mapping,
            selector_funnel={
                "selector_candidate_count": snapshot.candidate_count,
                "selector_selected_count": snapshot.selected_count,
                "goal_filtered_count": snapshot.goal_filtered_count,
                "inhibited_count": snapshot.inhibited_count,
                "budget_skipped_count": snapshot.budget_skipped_count,
            },
            snapshot_at=request.as_of,
        )
        return ContextResponse(
            items=mapping.items,
            estimated_tokens=snapshot.estimated_prompt_tokens,
            latency_ms=latency_ms,
            backend_metadata=backend_metadata,
        )

    async def assess(self, request: AssessmentRequest) -> AssessmentResponse | None:
        start = time.perf_counter()
        memory = self._require_memory()
        cue = _build_retrieval_cue(
            query=request.query,
            entity_ids=request.entity_ids,
            predicate=request.predicate,
            object_value=request.object_value,
        )
        assessment = await memory.assess_memory(
            cue,
            tenant_id=TENANT_ID,
            goal=request.goal,
            as_of=request.as_of,
            valid_at=request.valid_at,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        flags = tuple(flag.value for flag in assessment.flags)
        indicates_missing = _indicates_missing_knowledge_from_flags(flags)
        indicates_conflict = "conflicting_semantic_memory" in flags
        signals = {
            "cue_coverage": assessment.signals.cue_coverage,
            "top_retrieval_strength": assessment.signals.top_retrieval_strength,
            "mean_retrieval_strength": assessment.signals.mean_retrieval_strength,
            "evidence_confidence": assessment.signals.evidence_confidence,
            "semantic_conflict": assessment.signals.semantic_conflict,
            "provenance_diversity": assessment.signals.provenance_diversity,
            "forgetting_pressure": assessment.signals.forgetting_pressure,
            "learned_utility": assessment.signals.learned_utility,
            "freshness": assessment.signals.freshness,
        }
        assessment_metadata: dict[str, object] = {"retrieved_count": assessment.retrieved_count}
        context = getattr(assessment, "context", None)
        if context is not None:
            assessment_metadata["retrieval_context"] = dataclass_to_metadata(context)
        return AssessmentResponse(
            indicates_missing_knowledge=indicates_missing,
            indicates_conflict=indicates_conflict,
            latency_ms=latency_ms,
            signals=signals,
            flags=flags,
            backend_metadata=assessment_metadata,
        )

    async def apply_feedback(self, feedback: BenchmarkFeedback) -> None:
        _require_cogkura()
        from cogkura.models import (  # noqa: PLC0415
            LearningFeedback,
            LearningOutcome,
            MemoryFeedback,
        )

        memory = self._require_memory()
        identities = await self._identities_for_event_ids(feedback.target_event_ids)
        if not identities:
            return
        outcome_map = {
            FeedbackOutcome.HELPFUL: LearningOutcome.HELPFUL,
            FeedbackOutcome.UNHELPFUL: LearningOutcome.UNHELPFUL,
            FeedbackOutcome.INCORRECT: LearningOutcome.INCORRECT,
        }
        await memory.learn(
            LearningFeedback(
                tenant_id=TENANT_ID,
                feedback_id=feedback.id,
                occurred_at=feedback.timestamp,
                items=tuple(
                    MemoryFeedback(identity=identity, outcome=outcome_map[feedback.outcome])
                    for identity in identities
                ),
            )
        )

    async def maintain(self, *, as_of: datetime) -> None:
        memory = self._require_memory()
        forgetting_result = await memory.apply_forgetting(tenant_id=TENANT_ID, as_of=as_of)
        self._maintenance_calls += 1
        self._last_maintenance_at = as_of
        self._last_forgetting = dataclass_to_metadata(forgetting_result)
        for key in self._cumulative_forgetting:
            self._cumulative_forgetting[key] += int(getattr(forgetting_result, key, 0))

    async def diagnostic_snapshot(self) -> dict[str, object]:
        """Return a CogKura-only lifecycle and inventory snapshot."""
        memory = self._require_memory()
        _require_cogkura()
        from cogkura.models import SemanticMemoryStatus  # noqa: PLC0415

        episodes_all = await memory.list_episodes(tenant_id=TENANT_ID, include_inactive=True)
        semantics_all = await memory.list_semantic_memories(
            tenant_id=TENANT_ID,
            include_inactive=True,
        )
        semantics_superseded = await memory.list_semantic_memories(
            tenant_id=TENANT_ID,
            include_inactive=True,
            status=SemanticMemoryStatus.SUPERSEDED,
        )

        semantic_keys: set[str] = set()
        semantic_status_counts = {
            "semantic_status_active_count": 0,
            "semantic_status_contested_count": 0,
            "semantic_status_superseded_count": 0,
        }
        semantic_is_active_count = 0
        for semantic in semantics_all:
            semantic_keys.add(semantic.memory_key)
            if semantic.is_active:
                semantic_is_active_count += 1
            status_value = json_safe_metadata_value(semantic.status)
            if status_value == "active":
                semantic_status_counts["semantic_status_active_count"] += 1
            elif status_value == "contested":
                semantic_status_counts["semantic_status_contested_count"] += 1
            elif status_value == "superseded":
                semantic_status_counts["semantic_status_superseded_count"] += 1

        episode_is_active_count = sum(1 for episode in episodes_all if episode.is_active)

        return {
            "schema_version": COGKURA_METADATA_SCHEMA_VERSION,
            "lifecycle_counters": {
                "events_ingested": self._events_ingested,
                "ingest_calls": self._ingest_calls,
                "prepare_calls": self._prepare_calls,
                "maintenance_calls": self._maintenance_calls,
                "last_prepare_at": (
                    self._last_prepare_at.isoformat() if self._last_prepare_at is not None else None
                ),
                "last_maintenance_at": (
                    self._last_maintenance_at.isoformat()
                    if self._last_maintenance_at is not None
                    else None
                ),
            },
            "last_prepare": {
                "episode_encoding": self._last_episode_encoding,
                "semantic_consolidation": self._last_semantic_consolidation,
            },
            "last_maintenance": {
                "last_forgetting": self._last_forgetting,
                "cumulative_forgetting": dict(self._cumulative_forgetting),
            },
            "memory_inventory": {
                "episode_listed_count": len(episodes_all),
                "episode_is_active_count": episode_is_active_count,
                "semantic_listed_count": len(semantic_keys),
                "semantic_is_active_count": semantic_is_active_count,
                "semantic_superseded_listed_count": len(semantics_superseded),
                **semantic_status_counts,
            },
        }

    def _require_memory(self) -> Memory:
        if self._memory is None:
            raise RuntimeError("CogKura backend has not been reset.")
        return self._memory

    async def _refresh_observation_map(self) -> None:
        if self._observation_store is None:
            return
        observations = await self._observation_store.list(tenant_id=TENANT_ID)
        self._observation_id_to_event_id = {
            observation.id: observation.source_record_id for observation in observations
        }

    def _map_recall_results(
        self,
        results: Sequence[RecallResult],
        ranked_pairs: Sequence[tuple[int, RecallResult]] | None = None,
    ) -> RecallMappingResult:
        if ranked_pairs is None:
            ranked_pairs = [(index, result) for index, result in enumerate(results, start=1)]
        return map_ranked_recall_results(
            ranked_pairs,
            observation_id_to_event_id=self._observation_id_to_event_id,
            statement_for_result=self._statement_for_result,
        )

    def _build_response_metadata(
        self,
        *,
        recall_mapping: RecallMappingResult | None = None,
        context_mapping: RecallMappingResult | None = None,
        selector_funnel: Mapping[str, object] | None = None,
        snapshot_at: datetime | None = None,
        relationship_inspection: Mapping[str, object] | None = None,
        retrieval_context: Mapping[str, object] | None = None,
        competition_inspection: Mapping[str, object] | None = None,
        competition_counts: Mapping[str, int] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "cogkura": {
                "schema_version": COGKURA_METADATA_SCHEMA_VERSION,
                "cogkura_version": self._version,
                "bench_version": self._bench_version,
                "relationships_ingested": self._relationships_ingested,
                "lifecycle_counters": {
                    "events_ingested": self._events_ingested,
                    "ingest_calls": self._ingest_calls,
                    "prepare_calls": self._prepare_calls,
                    "maintenance_calls": self._maintenance_calls,
                    "last_prepare_at": (
                        self._last_prepare_at.isoformat()
                        if self._last_prepare_at is not None
                        else None
                    ),
                    "last_maintenance_at": (
                        self._last_maintenance_at.isoformat()
                        if self._last_maintenance_at is not None
                        else None
                    ),
                },
                "last_prepare": {
                    "episode_encoding": self._last_episode_encoding,
                    "semantic_consolidation": self._last_semantic_consolidation,
                },
                "last_maintenance": {
                    "last_forgetting": self._last_forgetting,
                    "cumulative_forgetting": dict(self._cumulative_forgetting),
                },
            }
        }
        cogkura_payload = payload["cogkura"]
        assert isinstance(cogkura_payload, dict)
        if snapshot_at is not None:
            cogkura_payload["snapshot_at"] = snapshot_at.isoformat()
        if recall_mapping is not None:
            cogkura_payload["recall_mapping"] = recall_mapping_metadata(recall_mapping)
        if context_mapping is not None:
            cogkura_payload["context_mapping"] = {
                "raw_selected_count": context_mapping.raw_count,
                "mapped_selected_count": context_mapping.mapped_count,
                "unmapped_selected_count": context_mapping.unmapped_count,
                **recall_mapping_metadata(context_mapping),
            }
        if selector_funnel is not None:
            cogkura_payload["selector_funnel"] = dict(selector_funnel)
        if relationship_inspection is not None:
            cogkura_payload["relationship_inspection"] = dict(relationship_inspection)
        if retrieval_context is not None:
            cogkura_payload["retrieval_context"] = dict(retrieval_context)
        if competition_inspection is not None:
            cogkura_payload["competition_inspection"] = dict(competition_inspection)
        if competition_counts is not None:
            cogkura_payload.update(dict(competition_counts))
        return payload

    def _statement_for_result(self, result: RecallResult) -> str:
        memory = result.memory
        if hasattr(memory, "statement"):
            return str(memory.statement)
        return ""

    async def _identities_for_event_ids(
        self,
        event_ids: Sequence[str],
    ) -> list[Any]:
        _require_cogkura()
        from cogkura.models import MemoryIdentity, MemoryKind  # noqa: PLC0415

        memory = self._require_memory()
        target_ids = set(event_ids)
        identities: list[MemoryIdentity] = []
        episodes = await memory.list_episodes(tenant_id=TENANT_ID)
        for episode in episodes:
            if self._episode_matches_event_ids(episode, target_ids):
                identities.append(
                    MemoryIdentity(memory_kind=MemoryKind.EPISODE, memory_key=episode.memory_key)
                )
        semantics = await memory.list_semantic_memories(tenant_id=TENANT_ID)
        for semantic in semantics:
            if self._semantic_matches_event_ids(semantic, target_ids):
                identities.append(
                    MemoryIdentity(memory_kind=MemoryKind.SEMANTIC, memory_key=semantic.memory_key)
                )
        return identities

    def _episode_matches_event_ids(self, episode: StoredEpisode, target_ids: set[str]) -> bool:
        for evidence in episode.evidence:
            event_id = self._observation_id_to_event_id.get(evidence.observation_id)
            if event_id in target_ids:
                return True
        return False

    def _semantic_matches_event_ids(
        self, semantic: StoredSemanticMemory, target_ids: set[str]
    ) -> bool:
        for evidence in semantic.observation_evidence:
            event_id = self._observation_id_to_event_id.get(evidence.observation_id)
            if event_id in target_ids:
                return True
        return False


# Backward-compatible test import.
_recall_result_to_metadata = recall_result_to_metadata
