"""CogKura memory backend adapter."""

from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from cogkurabench.models import (
    AssessmentRequest,
    AssessmentResponse,
    BackendCapabilities,
    BenchmarkFeedback,
    ContextRequest,
    ContextResponse,
    FeedbackOutcome,
    ProjectEvent,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedItem,
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

_OPTIONAL_RECALL_METADATA_FIELDS: tuple[str, ...] = (
    "rank_activation",
    "text_coverage",
    "text_cue_fit",
    "temporal_mode",
    "slot_fit",
    "structured_adjustment",
    "eligibility",
    "admission_reason",
    "support_slot",
    "support_semantic",
    "semantic_slot",
    "semantic_status",
)


def _indicates_missing_knowledge_from_flags(flags: Sequence[str]) -> bool:
    return any(flag in flags for flag in MISSING_KNOWLEDGE_FLAGS)


def _json_safe_metadata_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _recall_result_to_metadata(result: RecallResult) -> dict[str, object]:
    metadata: dict[str, object] = {
        "activation": result.activation,
        "score": result.score,
        "latency_seconds": result.latency_seconds,
        "reason": result.reason,
    }
    components = result.components
    metadata["activation_base_level"] = components.base_level
    metadata["activation_spreading"] = components.spreading
    metadata["activation_partial_match"] = components.partial_match
    metadata["activation_noise"] = components.noise
    metadata["activation_total"] = components.total
    metadata["activation_current_state"] = components.current_state

    for field_name in _OPTIONAL_RECALL_METADATA_FIELDS:
        if hasattr(result, field_name):
            metadata[field_name] = _json_safe_metadata_value(getattr(result, field_name))

    memory = result.memory
    if hasattr(memory, "status"):
        metadata["semantic_status"] = _json_safe_metadata_value(memory.status)
    if hasattr(memory, "predicate"):
        metadata["semantic_predicate"] = memory.predicate
    if hasattr(memory, "subject_entity_id"):
        metadata["semantic_subject_entity_id"] = memory.subject_entity_id
    if hasattr(memory, "object_value"):
        metadata["semantic_object_value"] = memory.object_value
    if hasattr(memory, "slot_key"):
        metadata["semantic_slot_key"] = memory.slot_key

    return metadata


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
        payload.append(
            {
                "predicate": fact.predicate,
                "object_value": fact.object,
                "subject_entity_id": fact.subject,
                "cardinality": fact.cardinality,
                "polarity": fact.polarity,
                "qualifiers": dict(fact.qualifiers),
            }
        )
    return payload


class CogKuraBackend:
    """Benchmark adapter for CogKura 0.14.x public memory API."""

    def __init__(self) -> None:
        self._memory: Memory | None = None
        self._observation_store: Any = None
        self._observation_id_to_event_id: dict[str, str] = {}
        self._version: str | None = None

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
        )

    async def reset(self) -> None:
        cogkura = _require_cogkura()
        from cogkura.algorithms.semantic import (
            ComplementaryLearningSemanticConsolidator,  # noqa: PLC0415
        )
        from cogkura.storage.in_memory_observation import InMemoryObservationStore  # noqa: PLC0415

        self._version = _installed_cogkura_version(cogkura)
        if self._memory is not None:
            await self._memory.clear(tenant_id=TENANT_ID)
        self._observation_store = InMemoryObservationStore()
        self._memory = cogkura.Memory(
            observation_store=self._observation_store,
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                minimum_supporting_episodes=1,
            ),
        )
        self._observation_id_to_event_id.clear()

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
        await self._refresh_observation_map()

    async def prepare(self, *, as_of: datetime) -> None:
        memory = self._require_memory()
        await memory.encode_episodes(tenant_id=TENANT_ID, as_of=as_of)
        await memory.consolidate_semantics(tenant_id=TENANT_ID, as_of=as_of)
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
        items = self._results_to_items(results)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return RetrievalResponse(items=tuple(items), latency_ms=latency_ms)

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
        items = self._results_to_items(snapshot.recall_results)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return ContextResponse(
            items=tuple(items),
            estimated_tokens=snapshot.estimated_prompt_tokens,
            latency_ms=latency_ms,
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
        return AssessmentResponse(
            indicates_missing_knowledge=indicates_missing,
            indicates_conflict=indicates_conflict,
            latency_ms=latency_ms,
            signals=signals,
            flags=flags,
            backend_metadata={"retrieved_count": assessment.retrieved_count},
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
        await memory.apply_forgetting(tenant_id=TENANT_ID, as_of=as_of)

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

    def _results_to_items(self, results: Sequence[RecallResult]) -> list[RetrievedItem]:
        items: list[RetrievedItem] = []
        for rank, result in enumerate(results, start=1):
            event_ids = self._event_ids_for_result(result)
            if not event_ids:
                continue
            text = self._statement_for_result(result)
            items.append(
                RetrievedItem(
                    source_event_ids=event_ids,
                    text=text,
                    score=result.score,
                    rank=rank,
                    memory_type=result.memory_kind.value,
                    metadata=_recall_result_to_metadata(result),
                )
            )
        return items

    def _event_ids_for_result(self, result: RecallResult) -> tuple[str, ...]:
        memory = result.memory
        observation_ids: set[str] = set()
        if hasattr(memory, "evidence"):
            for evidence in memory.evidence:
                observation_ids.add(evidence.observation_id)
        if hasattr(memory, "observation_evidence"):
            for evidence in memory.observation_evidence:
                observation_ids.add(evidence.observation_id)
        event_ids = tuple(
            sorted(
                {
                    self._observation_id_to_event_id[observation_id]
                    for observation_id in observation_ids
                    if observation_id in self._observation_id_to_event_id
                }
            )
        )
        return event_ids

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
