"""Backend-neutral source inspection requests, observations, and declared checks.

Gold checks never cross the adapter boundary. Names describe observable evidence,
not a second implementation of admission, reconciliation, or source trust.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import TypeAlias

from cogkurabench.exceptions import ValidationError

Scalar: TypeAlias = str | int | float | bool | None
CheckValue: TypeAlias = Scalar | tuple[str, ...]
STATES = frozenset(
    {"known", "unknown", "contested", "withdrawn", "historical_only", "indeterminate"}
)


@dataclass(frozen=True, slots=True)
class SourceInspectionSpec:
    """Exact slot and explicit bounds; no expected answer or reason codes."""

    subject: str
    predicate: str
    qualifiers: Mapping[str, Scalar] = field(default_factory=dict)
    max_revisions: int = 128
    max_relations: int = 256
    max_evidence: int = 256
    context: bool = False
    as_of: datetime | None = None

    def __post_init__(self) -> None:
        if not self.subject.strip() or not self.predicate.strip():
            raise ValidationError("source inspection requires subject and predicate.")
        if not isinstance(self.context, bool):
            raise ValidationError("source inspection context must be boolean.")
        for name in ("max_revisions", "max_relations", "max_evidence"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValidationError(f"{name} must be a positive integer.")
        if self.as_of is not None and self.as_of.utcoffset() is None:
            raise ValidationError("source inspection as_of must be timezone-aware.")
        if any(
            not isinstance(k, str)
            or not k.strip()
            or not isinstance(v, str | int | float | bool | type(None))
            or (isinstance(v, float) and not math.isfinite(v))
            for k, v in self.qualifiers.items()
        ):
            raise ValidationError("source qualifiers must be finite scalars.")
        object.__setattr__(self, "qualifiers", MappingProxyType(dict(self.qualifiers)))


@dataclass(frozen=True, slots=True)
class EvidenceCoverageObservation:
    has_evidence: bool
    revision_complete: bool
    locator_complete: bool
    relation_complete: bool | None
    truncated: bool
    distinct_sources: int
    referenced: int
    returned: int
    relation_applicable: int
    relation_not_applicable: int


@dataclass(frozen=True, slots=True)
class SourceRevisionObservation:
    event_ids: tuple[str, ...]
    status: str | None
    view: str
    history_complete: bool
    valid_from: datetime | None
    valid_until: datetime | None
    latest: tuple[bool | None, ...]


@dataclass(frozen=True, slots=True)
class SourceDecisionObservation:
    operation: str
    outcome: str
    reasons: tuple[str, ...]
    event_ids: tuple[str, ...]
    effective_at: datetime | None


@dataclass(frozen=True, slots=True)
class SourceAssessmentObservation:
    state: str
    conflict: str
    conflict_complete: bool
    cross_source_disagreement: bool | None
    independence: str
    inventory_complete: bool
    decision_history: str
    reasons: tuple[str, ...]
    quality: EvidenceCoverageObservation
    revisions: tuple[SourceRevisionObservation, ...]
    event_ids: tuple[str, ...]
    pending_count: int
    indeterminate_revision_count: int
    transition_event_ids: tuple[str, ...]
    transition_effective_times: tuple[str, ...]
    unmapped_evidence_count: int
    decisions: tuple[SourceDecisionObservation, ...]
    decisions_available: bool
    decisions_complete: bool | None
    decisions_truncated: bool | None
    context_quality: EvidenceCoverageObservation | None = None
    context_event_ids: tuple[str, ...] = ()
    context_older_count: int | None = None
    context_currentness_complete: bool | None = None


# Each supported assertion has a defined scoring category. Tuple checks are exact
# sets; ``*_contains`` checks are subsets and ``*_excludes`` checks disjointness.
FIELD_CATEGORIES = {
    "state": "state",
    "conflict": "conflict",
    "conflict_complete": "completeness",
    "cross_source_disagreement": "conflict",
    "independence": "uncertainty",
    "inventory_complete": "completeness",
    "decision_history": "uncertainty",
    "reasons_contains": "reason",
    "event_ids": "attribution",
    "event_ids_excludes": "temporal",
    "transition_event_ids": "attribution",
    "transition_effective_times": "temporal",
    "pending_count": "temporal",
    "indeterminate_revision_count": "uncertainty",
    "unmapped_evidence_count": "attribution",
    "decisions_available": "uncertainty",
    "decisions_complete": "completeness",
    "decisions_truncated": "completeness",
    "decision_reasons_contains": "reason",
    "decision_outcomes_contains": "reason",
    "decision_event_ids_contains": "attribution",
    "revision_views_contains": "temporal",
    "revision_statuses_contains": "state",
    "latest_values": "uncertainty",
    "context_event_ids_contains": "attribution",
    "context_older_count": "currentness",
    "context_currentness_complete": "currentness",
}
for _prefix in ("quality", "context_quality"):
    for _name in EvidenceCoverageObservation.__dataclass_fields__:
        FIELD_CATEGORIES[f"{_prefix}.{_name}"] = "completeness"


@dataclass(frozen=True, slots=True)
class SourceAssessmentExpectation:
    """Independently declared checks on neutral observation fields.

    An explicit None checks unknown/not-applicable; omission does not score that
    field. Report checks apply only to a profile advertising decision diagnostics.
    """

    checks: Mapping[str, CheckValue]
    diagnostic_checks: Mapping[str, CheckValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "state" not in self.checks or self.checks["state"] not in STATES:
            raise ValidationError("source expectations require a valid state.")
        for name in ("checks", "diagnostic_checks"):
            values = dict(getattr(self, name))
            for key, value in values.items():
                if key not in FIELD_CATEGORIES:
                    raise ValidationError(f"unknown source assessment check {key!r}.")
                if name == "diagnostic_checks" and not key.startswith("decision"):
                    raise ValidationError("diagnostic checks may only describe pass reports.")
                if not isinstance(value, str | int | float | bool | tuple | type(None)):
                    raise ValidationError(f"invalid source assessment check {key!r}.")
                if isinstance(value, tuple) and any(not isinstance(v, str) for v in value):
                    raise ValidationError("source tuple checks must contain strings.")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValidationError("source checks must be finite.")
                if (
                    key.endswith(("_contains", "_excludes"))
                    or key
                    in {
                        "event_ids",
                        "transition_event_ids",
                        "transition_effective_times",
                        "latest_values",
                    }
                ) and not isinstance(value, tuple):
                    raise ValidationError(f"source check {key!r} requires a tuple.")
                if key.endswith(
                    (
                        "_count",
                        ".distinct_sources",
                        ".referenced",
                        ".returned",
                        ".relation_applicable",
                        ".relation_not_applicable",
                    )
                ):
                    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                        raise ValidationError(
                            f"source check {key!r} requires a nonnegative integer."
                        )
            object.__setattr__(self, name, MappingProxyType(values))


@dataclass(frozen=True, slots=True)
class SourceAssessmentRequest:
    query: str
    as_of: datetime
    valid_at: datetime | None
    tenant_id: str
    subject_id: str | None
    spec: SourceInspectionSpec

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.query.strip():
            raise ValidationError("source request requires tenant and query.")
        if self.subject_id is not None and not self.subject_id.strip():
            raise ValidationError("source request subject_id must not be blank.")
        if self.as_of.utcoffset() is None or (
            self.valid_at is not None and self.valid_at.utcoffset() is None
        ):
            raise ValidationError("source request times must be timezone-aware.")
        if self.spec.as_of is not None and self.spec.as_of > self.as_of:
            raise ValidationError("source request cannot inspect future knowledge.")
