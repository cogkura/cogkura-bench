"""Neutral benchmark domain models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from cogkurabench.exceptions import ValidationError


class EventType(StrEnum):
    """Canonical benchmark event categories across domains."""

    CONVERSATION = "conversation"
    REQUIREMENT = "requirement"
    REQUIREMENT_CHANGE = "requirement_change"
    ARCHITECTURE_DECISION = "architecture_decision"
    IMPLEMENTATION = "implementation"
    BUG = "bug"
    INCIDENT = "incident"
    TEST_FAILURE = "test_failure"
    FIX = "fix"
    DEPENDENCY = "dependency"
    REJECTED_APPROACH = "rejected_approach"
    USER_FEEDBACK = "user_feedback"
    RELEASE = "release"
    DOCUMENTATION = "documentation"
    NOISE = "noise"
    BROWSE = "browse"
    PURCHASE = "purchase"
    PRODUCT_RETURN = "product_return"
    SUPPORT_INTERACTION = "support_interaction"
    PREFERENCE_STATEMENT = "preference_statement"
    POSITIVE_OUTCOME = "positive_outcome"
    NEGATIVE_OUTCOME = "negative_outcome"


class Capability(StrEnum):
    """Benchmark memory capabilities."""

    DIRECT_RECALL = "direct_recall"
    EPISODIC_RECALL = "episodic_recall"
    ASSOCIATIVE_RECALL = "associative_recall"
    TEMPORAL_RECALL = "temporal_recall"
    KNOWLEDGE_UPDATE = "knowledge_update"
    FORGETTING = "forgetting"
    WORKING_MEMORY = "working_memory"
    LEARNING = "learning"
    METAMEMORY = "metamemory"
    INTERFERENCE = "interference"


class CompetitionDirection(StrEnum):
    """Benchmark-neutral temporal competition direction."""

    PROACTIVE = "proactive"
    RETROACTIVE = "retroactive"
    CO_TEMPORAL = "co_temporal"


class FeedbackOutcome(StrEnum):
    """Learning feedback outcome labels."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"
    INCORRECT = "incorrect"


class EvidenceGroupStage(StrEnum):
    """Stage classification for evidence-group diagnostics."""

    SELECTED = "selected"
    SELECTION_DROP = "selection_drop"
    RETRIEVAL_MISS = "retrieval_miss"
    CONTEXT_ONLY = "context_only"


def _require_tzaware(label: str, value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValidationError(f"{label} must be timezone-aware.")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class EntityRelationship:
    """Directed relationship between catalogue or product entities."""

    source_entity_id: str
    relation_type: str
    target_entity_id: str
    provenance: str | None = None

    def __post_init__(self) -> None:
        if not self.source_entity_id.strip():
            raise ValidationError("relationship source_entity_id must not be empty.")
        if not self.relation_type.strip():
            raise ValidationError("relationship relation_type must not be empty.")
        if not self.target_entity_id.strip():
            raise ValidationError("relationship target_entity_id must not be empty.")
        if self.source_entity_id == self.target_entity_id:
            raise ValidationError(
                "relationship source_entity_id must differ from target_entity_id."
            )


@dataclass(frozen=True, slots=True)
class SemanticFact:
    """Atomic semantic proposition attached to a benchmark event."""

    subject: str
    predicate: str
    object: str
    cardinality: str = "many"
    polarity: str = "affirm"
    qualifiers: Mapping[str, str] = field(default_factory=dict)
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValidationError("subject must not be empty.")
        if not self.predicate.strip():
            raise ValidationError("predicate must not be empty.")
        if not self.object.strip():
            raise ValidationError("object must not be empty.")
        object.__setattr__(self, "qualifiers", MappingProxyType(dict(self.qualifiers)))
        if self.valid_from is not None:
            object.__setattr__(self, "valid_from", _require_tzaware("valid_from", self.valid_from))
        if self.valid_until is not None:
            object.__setattr__(
                self, "valid_until", _require_tzaware("valid_until", self.valid_until)
            )


@dataclass(frozen=True, slots=True)
class EvidenceGroup:
    """Several source events that satisfy one benchmark concept."""

    id: str
    label: str
    event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("evidence group id must not be empty.")
        if not self.label.strip():
            raise ValidationError("evidence group label must not be empty.")
        if not self.event_ids:
            raise ValidationError(f"evidence group {self.id!r} must contain at least one event.")
        if len(set(self.event_ids)) != len(self.event_ids):
            raise ValidationError(f"evidence group {self.id!r} contains duplicate event IDs.")


@dataclass(frozen=True, slots=True)
class CompetitionExpectation:
    """Query-level ground truth for a directed competition relationship."""

    id: str
    candidate_event_ids: tuple[str, ...]
    competitor_event_ids: tuple[str, ...]
    direction: CompetitionDirection | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("competition expectation id must not be empty.")
        if not self.candidate_event_ids:
            raise ValidationError(
                f"competition expectation {self.id!r} must contain candidate event IDs."
            )
        if not self.competitor_event_ids:
            raise ValidationError(
                f"competition expectation {self.id!r} must contain competitor event IDs."
            )
        if set(self.candidate_event_ids) == set(self.competitor_event_ids):
            raise ValidationError(
                f"competition expectation {self.id!r} candidate and competitor groups "
                "must not be identical."
            )


@dataclass(frozen=True, slots=True)
class CompetitionObservation:
    """Backend-neutral observed competition relationship."""

    candidate_source_event_ids: tuple[str, ...]
    competitor_source_event_ids: tuple[str, ...]
    direction: CompetitionDirection
    strength: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.candidate_source_event_ids:
            raise ValidationError("candidate_source_event_ids must not be empty.")
        if not self.competitor_source_event_ids:
            raise ValidationError("competitor_source_event_ids must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class ExpectedFact:
    """Optional structured fact expectation for a query."""

    subject: str
    predicate: str
    object: str

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValidationError("expected fact subject must not be empty.")
        if not self.predicate.strip():
            raise ValidationError("expected fact predicate must not be empty.")
        if not self.object.strip():
            raise ValidationError("expected fact object must not be empty.")


@dataclass(frozen=True, slots=True)
class ProjectEvent:
    """Canonical structured event in a benchmark scenario."""

    id: str
    timestamp: datetime
    sequence: int
    subject_id: str
    event_type: EventType
    content: str
    entities: tuple[str, ...] = ()
    semantic_facts: tuple[SemanticFact, ...] = ()
    tags: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    related_events: tuple[str, ...] = ()
    session_id: str | None = None
    relationships: tuple[EntityRelationship, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("event id must not be empty.")
        if not self.subject_id.strip():
            raise ValidationError("subject_id must not be empty.")
        if not self.content.strip():
            raise ValidationError("content must not be empty.")
        object.__setattr__(self, "timestamp", _require_tzaware("timestamp", self.timestamp))


@dataclass(frozen=True, slots=True)
class BenchmarkQuery:
    """Ground-truth query against a benchmark scenario."""

    id: str
    timestamp: datetime
    capability: Capability
    query: str
    goal: str | None = None
    expected_evidence_ids: tuple[str, ...] = ()
    acceptable_evidence_ids: tuple[str, ...] = ()
    forbidden_evidence_ids: tuple[str, ...] = ()
    expected_fact: ExpectedFact | None = None
    valid_at: datetime | None = None
    should_abstain: bool = False
    retrieval_limit: int = 5
    prompt_budget_tokens: int | None = None
    related_query_id: str | None = None
    tags: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    predicate: str | None = None
    object_value: str | None = None
    expected_evidence_groups: tuple[EvidenceGroup, ...] = ()
    forbidden_evidence_groups: tuple[EvidenceGroup, ...] = ()
    expected_competitions: tuple[CompetitionExpectation, ...] = ()
    forbidden_competitions: tuple[CompetitionExpectation, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("query id must not be empty.")
        if not self.query.strip():
            raise ValidationError("query text must not be empty.")
        if self.retrieval_limit <= 0:
            raise ValidationError("retrieval_limit must be greater than zero.")
        object.__setattr__(self, "timestamp", _require_tzaware("timestamp", self.timestamp))
        if self.valid_at is not None:
            object.__setattr__(self, "valid_at", _require_tzaware("valid_at", self.valid_at))
        expected_group_ids = [group.id for group in self.expected_evidence_groups]
        forbidden_group_ids = [group.id for group in self.forbidden_evidence_groups]
        if len(set(expected_group_ids)) != len(expected_group_ids):
            raise ValidationError(f"query {self.id} has duplicate expected evidence group IDs.")
        if len(set(forbidden_group_ids)) != len(forbidden_group_ids):
            raise ValidationError(f"query {self.id} has duplicate forbidden evidence group IDs.")
        overlap = set(expected_group_ids) & set(forbidden_group_ids)
        if overlap:
            raise ValidationError(
                f"query {self.id} assigns group IDs to both expected and forbidden: "
                f"{sorted(overlap)}"
            )
        competition_ids = [
            expectation.id
            for expectation in (*self.expected_competitions, *self.forbidden_competitions)
        ]
        if len(set(competition_ids)) != len(competition_ids):
            raise ValidationError(f"query {self.id} has duplicate competition expectation IDs.")


@dataclass(frozen=True, slots=True)
class BenchmarkFeedback:
    """Explicit learning feedback tied to a prior query."""

    id: str
    timestamp: datetime
    query_id: str
    outcome: FeedbackOutcome
    target_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("feedback id must not be empty.")
        if not self.query_id.strip():
            raise ValidationError("query_id must not be empty.")
        object.__setattr__(self, "timestamp", _require_tzaware("timestamp", self.timestamp))


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    """Versioned dataset metadata."""

    name: str
    schema_version: int
    events: int
    queries: int
    feedback: int
    description: str
    required_capabilities: tuple[Capability, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("manifest name must not be empty.")
        if self.schema_version <= 0:
            raise ValidationError("schema_version must be greater than zero.")


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Supported optional backend features."""

    retrieve: bool = True
    select_context: bool = False
    assess: bool = False
    learn: bool = False
    forget: bool = False
    maintain: bool = False
    competition_diagnostics: bool = False


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Neutral retrieval request."""

    query_id: str
    query: str
    as_of: datetime
    limit: int
    goal: str | None = None
    valid_at: datetime | None = None
    entity_ids: tuple[str, ...] = ()
    predicate: str | None = None
    object_value: str | None = None

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValidationError("query_id must not be empty.")
        if self.limit <= 0:
            raise ValidationError("limit must be greater than zero.")
        object.__setattr__(self, "as_of", _require_tzaware("as_of", self.as_of))
        if self.valid_at is not None:
            object.__setattr__(self, "valid_at", _require_tzaware("valid_at", self.valid_at))


@dataclass(frozen=True, slots=True)
class RetrievedItem:
    """Neutral retrieved memory item."""

    source_event_ids: tuple[str, ...]
    text: str
    score: float | None
    rank: int
    memory_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValidationError("rank must be greater than zero.")
        if not self.source_event_ids:
            raise ValidationError("source_event_ids must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class RetrievalResponse:
    """Neutral retrieval response."""

    items: tuple[RetrievedItem, ...]
    latency_ms: float
    competition_observations: tuple[CompetitionObservation, ...] = ()
    backend_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValidationError("latency_ms must not be negative.")
        object.__setattr__(self, "backend_metadata", MappingProxyType(dict(self.backend_metadata)))


@dataclass(frozen=True, slots=True)
class ContextRequest:
    """Working-memory context selection request."""

    query_id: str
    query: str
    as_of: datetime
    goal: str | None = None
    valid_at: datetime | None = None
    prompt_budget_tokens: int | None = None
    entity_ids: tuple[str, ...] = ()
    predicate: str | None = None
    object_value: str | None = None

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValidationError("query_id must not be empty.")
        object.__setattr__(self, "as_of", _require_tzaware("as_of", self.as_of))
        if self.valid_at is not None:
            object.__setattr__(self, "valid_at", _require_tzaware("valid_at", self.valid_at))


@dataclass(frozen=True, slots=True)
class ContextResponse:
    """Working-memory context selection response."""

    items: tuple[RetrievedItem, ...]
    estimated_tokens: int
    latency_ms: float
    backend_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.estimated_tokens < 0:
            raise ValidationError("estimated_tokens must not be negative.")
        if self.latency_ms < 0:
            raise ValidationError("latency_ms must not be negative.")
        object.__setattr__(self, "backend_metadata", MappingProxyType(dict(self.backend_metadata)))


@dataclass(frozen=True, slots=True)
class AssessmentRequest:
    """Metamemory assessment request."""

    query_id: str
    query: str
    as_of: datetime
    goal: str | None = None
    valid_at: datetime | None = None
    should_abstain: bool = False
    entity_ids: tuple[str, ...] = ()
    predicate: str | None = None
    object_value: str | None = None

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValidationError("query_id must not be empty.")
        object.__setattr__(self, "as_of", _require_tzaware("as_of", self.as_of))
        if self.valid_at is not None:
            object.__setattr__(self, "valid_at", _require_tzaware("valid_at", self.valid_at))


@dataclass(frozen=True, slots=True)
class AssessmentResponse:
    """Metamemory assessment response."""

    indicates_missing_knowledge: bool
    indicates_conflict: bool
    latency_ms: float
    signals: Mapping[str, float | None] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    backend_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValidationError("latency_ms must not be negative.")
        object.__setattr__(self, "signals", MappingProxyType(dict(self.signals)))
        object.__setattr__(self, "backend_metadata", MappingProxyType(dict(self.backend_metadata)))


@dataclass(frozen=True, slots=True)
class IngestAction:
    """Ingest a single project event at its timestamp."""

    timestamp: datetime
    sequence: int
    event: ProjectEvent


@dataclass(frozen=True, slots=True)
class QueryAction:
    """Execute a benchmark query."""

    timestamp: datetime
    sequence: int
    query: BenchmarkQuery


@dataclass(frozen=True, slots=True)
class FeedbackAction:
    """Apply learning feedback."""

    timestamp: datetime
    sequence: int
    feedback: BenchmarkFeedback


@dataclass(frozen=True, slots=True)
class MaintenanceAction:
    """Scheduled memory maintenance."""

    timestamp: datetime
    sequence: int


BenchmarkAction = IngestAction | QueryAction | FeedbackAction | MaintenanceAction


@dataclass(frozen=True, slots=True)
class BenchmarkDataset:
    """Loaded benchmark dataset with compiled action stream."""

    manifest: DatasetManifest
    events: tuple[ProjectEvent, ...]
    queries: tuple[BenchmarkQuery, ...]
    feedback: tuple[BenchmarkFeedback, ...]
    actions: tuple[BenchmarkAction, ...]
    root: str

    @property
    def name(self) -> str:
        return self.manifest.name

    def event_by_id(self) -> dict[str, ProjectEvent]:
        return {event.id: event for event in self.events}

    def query_by_id(self) -> dict[str, BenchmarkQuery]:
        return {query.id: query for query in self.queries}
