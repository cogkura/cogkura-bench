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
    """Canonical project event categories."""

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


class FeedbackOutcome(StrEnum):
    """Learning feedback outcome labels."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"
    INCORRECT = "incorrect"


def _require_tzaware(label: str, value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValidationError(f"{label} must be timezone-aware.")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class SemanticFact:
    """Atomic semantic proposition attached to a project event."""

    subject: str
    predicate: str
    object: str
    cardinality: str = "many"
    polarity: str = "affirm"
    qualifiers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValidationError("subject must not be empty.")
        if not self.predicate.strip():
            raise ValidationError("predicate must not be empty.")
        if not self.object.strip():
            raise ValidationError("object must not be empty.")
        object.__setattr__(self, "qualifiers", MappingProxyType(dict(self.qualifiers)))


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


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Neutral retrieval request."""

    query_id: str
    query: str
    as_of: datetime
    limit: int
    goal: str | None = None
    valid_at: datetime | None = None

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
