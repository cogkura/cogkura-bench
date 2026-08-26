"""Evidence-group diagnostics for working-memory stage classification."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cogkurabench.metrics.ranking import item_has_any, order_retrieved_items
from cogkurabench.models import (
    BenchmarkQuery,
    EvidenceGroup,
    EvidenceGroupStage,
    RetrievedItem,
)


@dataclass(frozen=True, slots=True)
class EvidenceGroupDiagnostic:
    """Per-group retrieval and context diagnostic."""

    group_id: str
    label: str
    retrieval_present: bool
    context_present: bool
    first_retrieval_rank: int | None
    first_context_rank: int | None
    stage: str
    context_slot_count: int = 0


@dataclass(frozen=True, slots=True)
class ForbiddenGroupDiagnostic:
    """Per-group forbidden presence at retrieval and context stages."""

    group_id: str
    label: str
    retrieval_present: bool
    context_present: bool


@dataclass(frozen=True, slots=True)
class ItemGroupClassification:
    """Per-item classification against labelled evidence groups."""

    rank: int
    source_event_ids: tuple[str, ...]
    matched_expected_groups: tuple[str, ...]
    matched_forbidden_groups: tuple[str, ...]
    classification: str
    redundant_labelled_coverage: bool = False


def group_present_in_items(
    group: EvidenceGroup,
    items: Sequence[RetrievedItem],
) -> bool:
    """Return whether any item cites an event from the group."""
    for item in items:
        if item_has_any(item, group.event_ids):
            return True
    return False


def first_group_rank(
    group: EvidenceGroup,
    items: Sequence[RetrievedItem],
) -> int | None:
    """Return the 1-based rank of the first item citing the group, or None."""
    ordered = order_retrieved_items(items)
    for item in ordered:
        if item_has_any(item, group.event_ids):
            return item.rank
    return None


def count_group_slots(
    group: EvidenceGroup,
    items: Sequence[RetrievedItem],
) -> int:
    """Count context items whose provenance intersects the group."""
    return sum(1 for item in items if item_has_any(item, group.event_ids))


def classify_stage(
    *,
    retrieval_present: bool,
    context_present: bool,
) -> str:
    """Classify an expected group's stage."""
    if retrieval_present and context_present:
        return EvidenceGroupStage.SELECTED.value
    if retrieval_present and not context_present:
        return EvidenceGroupStage.SELECTION_DROP.value
    if not retrieval_present and not context_present:
        return EvidenceGroupStage.RETRIEVAL_MISS.value
    return EvidenceGroupStage.CONTEXT_ONLY.value


def matched_groups_for_item(
    item: RetrievedItem,
    groups: Sequence[EvidenceGroup],
) -> tuple[str, ...]:
    """Return group IDs whose event IDs intersect the item's provenance."""
    matched: list[str] = []
    for group in groups:
        if item_has_any(item, group.event_ids):
            matched.append(group.id)
    return tuple(matched)


def classify_item(
    item: RetrievedItem,
    *,
    expected_groups: Sequence[EvidenceGroup],
    forbidden_groups: Sequence[EvidenceGroup],
) -> str:
    """Classify one item against expected and forbidden evidence groups."""
    expected = matched_groups_for_item(item, expected_groups)
    forbidden = matched_groups_for_item(item, forbidden_groups)
    if expected and forbidden:
        return "expected_and_forbidden"
    if expected:
        return "expected"
    if forbidden:
        return "forbidden"
    return "unclassified"


def evidence_group_coverage(
    groups: Sequence[EvidenceGroup],
    items: Sequence[RetrievedItem],
) -> float:
    """Fraction of groups represented in the item set."""
    if not groups:
        return 1.0
    present = sum(1 for group in groups if group_present_in_items(group, items))
    return present / len(groups)


def forbidden_group_intrusion(
    groups: Sequence[EvidenceGroup],
    items: Sequence[RetrievedItem],
) -> float:
    """Fraction of forbidden groups present in the item set."""
    if not groups:
        return 0.0
    present = sum(1 for group in groups if group_present_in_items(group, items))
    return present / len(groups)


def redundant_expected_group_items(
    items: Sequence[RetrievedItem],
    expected_groups: Sequence[EvidenceGroup],
) -> int:
    """Count context items that add no new expected-group coverage."""
    if not expected_groups:
        return 0
    covered: set[str] = set()
    redundant = 0
    for item in order_retrieved_items(items):
        matched = set(matched_groups_for_item(item, expected_groups))
        if not matched:
            continue
        if matched <= covered:
            redundant += 1
        else:
            covered |= matched
    return redundant


def unclassified_context_items(
    items: Sequence[RetrievedItem],
    *,
    expected_groups: Sequence[EvidenceGroup],
    forbidden_groups: Sequence[EvidenceGroup],
) -> int:
    """Count items matching neither expected nor forbidden evidence groups."""
    return sum(
        1
        for item in items
        if classify_item(
            item,
            expected_groups=expected_groups,
            forbidden_groups=forbidden_groups,
        )
        == "unclassified"
    )


def compute_evidence_group_diagnostics(
    query: BenchmarkQuery,
    retrieved_items: Sequence[RetrievedItem],
    context_items: Sequence[RetrievedItem],
    *,
    has_context: bool,
) -> tuple[
    tuple[EvidenceGroupDiagnostic, ...],
    tuple[ForbiddenGroupDiagnostic, ...],
    tuple[ItemGroupClassification, ...],
    dict[str, float],
]:
    """Compute evidence-group diagnostics and scalar metrics for one query."""
    expected_groups = query.expected_evidence_groups
    forbidden_groups = query.forbidden_evidence_groups
    if not expected_groups and not forbidden_groups:
        return (), (), (), {}

    ordered_retrieval = order_retrieved_items(retrieved_items)
    ordered_context = order_retrieved_items(context_items)

    expected_diagnostics: list[EvidenceGroupDiagnostic] = []
    for group in expected_groups:
        retrieval_present = group_present_in_items(group, ordered_retrieval)
        context_present = group_present_in_items(group, ordered_context) if has_context else False
        if has_context:
            stage = classify_stage(
                retrieval_present=retrieval_present,
                context_present=context_present,
            )
        elif retrieval_present:
            stage = ""
        else:
            stage = EvidenceGroupStage.RETRIEVAL_MISS.value
        expected_diagnostics.append(
            EvidenceGroupDiagnostic(
                group_id=group.id,
                label=group.label,
                retrieval_present=retrieval_present,
                context_present=context_present,
                first_retrieval_rank=first_group_rank(group, ordered_retrieval),
                first_context_rank=(
                    first_group_rank(group, ordered_context) if has_context else None
                ),
                stage=stage,
                context_slot_count=(
                    count_group_slots(group, ordered_context) if has_context else 0
                ),
            )
        )

    forbidden_diagnostics: list[ForbiddenGroupDiagnostic] = []
    for group in forbidden_groups:
        forbidden_diagnostics.append(
            ForbiddenGroupDiagnostic(
                group_id=group.id,
                label=group.label,
                retrieval_present=group_present_in_items(group, ordered_retrieval),
                context_present=(
                    group_present_in_items(group, ordered_context) if has_context else False
                ),
            )
        )

    covered_expected: set[str] = set()
    item_classifications: list[ItemGroupClassification] = []
    for item in ordered_context:
        matched_expected = matched_groups_for_item(item, expected_groups)
        matched_forbidden = matched_groups_for_item(item, forbidden_groups)
        classification = classify_item(
            item,
            expected_groups=expected_groups,
            forbidden_groups=forbidden_groups,
        )
        redundant = False
        if matched_expected:
            matched_set = set(matched_expected)
            redundant = matched_set <= covered_expected and bool(matched_set)
            covered_expected |= matched_set
        item_classifications.append(
            ItemGroupClassification(
                rank=item.rank,
                source_event_ids=item.source_event_ids,
                matched_expected_groups=matched_expected,
                matched_forbidden_groups=matched_forbidden,
                classification=classification,
                redundant_labelled_coverage=redundant,
            )
        )

    metrics: dict[str, float] = {}
    if expected_groups:
        metrics["evidence_group_coverage_at_retrieval"] = evidence_group_coverage(
            expected_groups,
            ordered_retrieval,
        )
        if has_context:
            metrics["evidence_group_coverage_at_budget"] = evidence_group_coverage(
                expected_groups,
                ordered_context,
            )
            metrics["redundant_expected_group_items"] = float(
                redundant_expected_group_items(ordered_context, expected_groups)
            )
    if forbidden_groups and has_context:
        metrics["forbidden_group_intrusion_at_budget"] = forbidden_group_intrusion(
            forbidden_groups,
            ordered_context,
        )
    if has_context and (expected_groups or forbidden_groups):
        metrics["unclassified_context_items"] = float(
            unclassified_context_items(
                ordered_context,
                expected_groups=expected_groups,
                forbidden_groups=forbidden_groups,
            )
        )

    return (
        tuple(expected_diagnostics),
        tuple(forbidden_diagnostics),
        tuple(item_classifications),
        metrics,
    )
